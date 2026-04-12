"""
Source artifact scanner for linking code/tests to specifications.

This module provides utilities for scanning repositories, discovering
existing files, and mapping them to features/stories using AST analysis.
"""

from __future__ import annotations

import ast
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.progress import Progress

from specfact_cli.models.plan import Feature, Story
from specfact_cli.models.source_tracking import SourceTracking
from specfact_cli.utils.terminal import get_progress_config


console = Console()


def _impl_functions_for_file(
    scanner: SourceArtifactScanner,
    impl_file: str,
    repo_path: Path,
    file_functions_cache: dict[str, list[str]],
) -> list[str]:
    if impl_file in file_functions_cache:
        return file_functions_cache[impl_file]
    file_path = repo_path / impl_file
    return scanner.extract_function_mappings(file_path) if file_path.exists() else []


def _test_functions_for_file(
    scanner: SourceArtifactScanner,
    test_file: str,
    repo_path: Path,
    file_test_functions_cache: dict[str, list[str]],
) -> list[str]:
    if test_file in file_test_functions_cache:
        return file_test_functions_cache[test_file]
    file_path = repo_path / test_file
    return scanner.extract_test_mappings(file_path) if file_path.exists() else []


def _cancel_future_map(future_to_feature: dict[Any, Any]) -> None:
    for f in future_to_feature:
        if not f.done():
            f.cancel()


def _drain_feature_link_futures(
    future_to_feature: dict[Any, Any],
    progress: Progress,
    task: Any,
    total_features: int,
) -> bool:
    """Return True if interrupted (KeyboardInterrupt)."""
    completed_count = 0
    interrupted = False
    try:
        for future in as_completed(future_to_feature):
            try:
                future.result()
                completed_count += 1
                progress.update(
                    task,
                    completed=completed_count,
                    description=(
                        f"[cyan]Linking features to source files... ({completed_count}/{total_features} features)"
                    ),
                )
            except KeyboardInterrupt:
                interrupted = True
                _cancel_future_map(future_to_feature)
                break
            except Exception:
                completed_count += 1
                progress.update(
                    task,
                    completed=completed_count,
                    description=f"[cyan]Linking features to source files... ({completed_count}/{total_features})",
                )
    except KeyboardInterrupt:
        interrupted = True
        _cancel_future_map(future_to_feature)
    return interrupted


def _scanner_repo_ready(self: Any) -> bool:
    p: Path = self.repo_path
    return p.exists() and p.is_dir()


def _scan_repo_returns_map(self: Any, result: SourceArtifactMap) -> bool:
    return isinstance(result, SourceArtifactMap)


@dataclass
class SourceArtifactMap:
    """Mapping of source artifacts to features/stories."""

    implementation_files: dict[str, list[str]] = field(default_factory=dict)  # file_path -> [feature_keys]
    test_files: dict[str, list[str]] = field(default_factory=dict)  # file_path -> [feature_keys]
    function_mappings: dict[str, list[str]] = field(default_factory=dict)  # "file.py::func" -> [story_keys]
    test_mappings: dict[str, list[str]] = field(default_factory=dict)  # "test_file.py::test_func" -> [story_keys]


@dataclass(slots=True)
class _FeatureLinkingContext:
    repo_path: Path
    impl_files: list[Path]
    test_files: list[Path]
    file_functions_cache: dict[str, list[str]]
    file_test_functions_cache: dict[str, list[str]]
    file_hashes_cache: dict[str, str]
    impl_files_by_stem: dict[str, list[Path]]
    test_files_by_stem: dict[str, list[Path]]
    impl_stems_by_substring: dict[str, set[str]]
    test_stems_by_substring: dict[str, set[str]]


@dataclass(slots=True)
class _ImplTestPathLinkArgs:
    feature_key_lower: str
    feature_title_words: list[str]
    repo_path: Path
    file_hashes_cache: dict[str, str]
    impl_files_by_stem: dict[str, list[Path]]
    test_files_by_stem: dict[str, list[Path]]
    impl_stems_by_substring: dict[str, set[str]]
    test_stems_by_substring: dict[str, set[str]]


class SourceArtifactScanner:
    """Scanner for discovering and linking source artifacts to specifications."""

    repo_path: Path

    def __init__(self, repo_path: Path) -> None:
        """
        Initialize scanner with repository path.

        Args:
            repo_path: Path to repository root
        """
        self.repo_path = repo_path.resolve()

    @beartype
    @require(_scanner_repo_ready, "Repository path must exist and be a directory")
    @ensure(_scan_repo_returns_map, "Must return SourceArtifactMap")
    def scan_repository(self) -> SourceArtifactMap:
        """
        Discover existing files and their current state.

        Returns:
            SourceArtifactMap with discovered files and mappings
        """
        artifact_map = SourceArtifactMap()

        # Discover implementation files (src/, lib/, app/, etc.)
        for pattern in ["src/**/*.py", "lib/**/*.py", "app/**/*.py", "*.py"]:
            for file_path in self.repo_path.glob(pattern):
                if self._is_implementation_file(file_path):
                    rel_path = str(file_path.relative_to(self.repo_path))
                    artifact_map.implementation_files[rel_path] = []

        # Discover test files (tests/, test/, spec/, etc.)
        for pattern in ["tests/**/*.py", "test/**/*.py", "spec/**/*.py", "**/test_*.py", "**/*_test.py"]:
            for file_path in self.repo_path.glob(pattern):
                if self._is_test_file(file_path):
                    rel_path = str(file_path.relative_to(self.repo_path))
                    artifact_map.test_files[rel_path] = []

        return artifact_map

    def _resolve_matched_paths(
        self,
        feature_key_lower: str,
        feature_title_words: list[str],
        files_by_stem: dict[str, list[Path]],
        stems_by_substring: dict[str, set[str]],
        repo_path: Path,
    ) -> set[str]:
        """
        Use inverted-index lookups to find all repo-relative file paths matching a feature.

        Searches by exact key match, exact title-word match, and then by substring index.

        Args:
            feature_key_lower: Lowercased feature key
            feature_title_words: Lowercased title words (len > 3)
            files_by_stem: Stem -> file paths index
            stems_by_substring: Substring -> stem set inverted index
            repo_path: Repository root for computing relative paths

        Returns:
            Set of repo-relative path strings
        """
        matched: set[str] = set()
        # Exact key match
        for fp in files_by_stem.get(feature_key_lower, []):
            matched.add(str(fp.relative_to(repo_path)))
        # Exact title-word matches
        for word in feature_title_words:
            for fp in files_by_stem.get(word, []):
                matched.add(str(fp.relative_to(repo_path)))
        # Inverted-index expansion for substring matches
        sets_to_union: list[set[str]] = []
        if feature_key_lower in stems_by_substring:
            sets_to_union.append(stems_by_substring[feature_key_lower])
        for word in feature_title_words:
            if word in stems_by_substring:
                sets_to_union.append(stems_by_substring[word])
        candidate_stems = set().union(*sets_to_union) if sets_to_union else set()
        for stem in candidate_stems:
            for fp in files_by_stem.get(stem, []):
                matched.add(str(fp.relative_to(repo_path)))
        return matched

    def _register_matched_files(
        self,
        matched_rel_paths: set[str],
        tracked_list: list[str],
        source_tracking: SourceTracking,
        file_hashes_cache: dict[str, str],
        repo_path: Path,
    ) -> None:
        """
        Add newly matched file paths to a source tracking list and update hashes.

        Args:
            matched_rel_paths: Repo-relative paths to register
            tracked_list: The list to append new paths to (mutated in-place)
            source_tracking: SourceTracking object (for hash updates)
            file_hashes_cache: Pre-computed hash cache
            repo_path: Repository root for resolving absolute paths
        """
        for rel_path in matched_rel_paths:
            if rel_path in tracked_list:
                continue
            tracked_list.append(rel_path)
            if rel_path in file_hashes_cache:
                source_tracking.file_hashes[rel_path] = file_hashes_cache[rel_path]
            else:
                file_path = repo_path / rel_path
                if file_path.exists():
                    source_tracking.update_hash(file_path)

    def _link_feature_impl_and_test_paths(
        self,
        source_tracking: SourceTracking,
        args: _ImplTestPathLinkArgs,
    ) -> None:
        matched_impl = self._resolve_matched_paths(
            args.feature_key_lower,
            args.feature_title_words,
            args.impl_files_by_stem,
            args.impl_stems_by_substring,
            args.repo_path,
        )
        self._register_matched_files(
            matched_impl,
            source_tracking.implementation_files,
            source_tracking,
            args.file_hashes_cache,
            args.repo_path,
        )

        matched_test = self._resolve_matched_paths(
            args.feature_key_lower,
            args.feature_title_words,
            args.test_files_by_stem,
            args.test_stems_by_substring,
            args.repo_path,
        )
        self._register_matched_files(
            matched_test,
            source_tracking.test_files,
            source_tracking,
            args.file_hashes_cache,
            args.repo_path,
        )

    def _link_feature_to_specs(self, feature: Feature, ctx: _FeatureLinkingContext) -> None:
        """
        Link a single feature to matching files (thread-safe helper).

        Args:
            feature: Feature to link
            ctx: Pre-computed repository file caches and indexes for linking.
        """
        if feature.source_tracking is None:
            feature.source_tracking = SourceTracking()
        source_tracking = feature.source_tracking
        if source_tracking is None:
            return

        feature_key_lower = feature.key.lower()
        feature_title_words = [w for w in feature.title.lower().split() if len(w) > 3]

        self._link_feature_impl_and_test_paths(
            source_tracking,
            _ImplTestPathLinkArgs(
                feature_key_lower=feature_key_lower,
                feature_title_words=feature_title_words,
                repo_path=ctx.repo_path,
                file_hashes_cache=ctx.file_hashes_cache,
                impl_files_by_stem=ctx.impl_files_by_stem,
                test_files_by_stem=ctx.test_files_by_stem,
                impl_stems_by_substring=ctx.impl_stems_by_substring,
                test_stems_by_substring=ctx.test_stems_by_substring,
            ),
        )

        for story in feature.stories:
            self._collect_story_function_mappings(
                story,
                ctx.repo_path,
                source_tracking,
                ctx.file_functions_cache,
                ctx.file_test_functions_cache,
            )

        # Update sync timestamp
        source_tracking.update_sync_timestamp()

    def _collect_story_function_mappings(
        self,
        story: Story,
        repo_path: Path,
        source_tracking: SourceTracking,
        file_functions_cache: dict[str, list[str]],
        file_test_functions_cache: dict[str, list[str]],
    ) -> None:
        """Populate story source/test function mappings from tracked files."""
        source_functions_set: set[str] = set(story.source_functions) if story.source_functions else set()
        test_functions_set: set[str] = set(story.test_functions) if story.test_functions else set()

        for impl_file in source_tracking.implementation_files:
            functions = _impl_functions_for_file(self, impl_file, repo_path, file_functions_cache)
            for func_name in functions:
                func_mapping = f"{impl_file}::{func_name}"
                if func_mapping not in source_functions_set:
                    source_functions_set.add(func_mapping)

        for test_file in source_tracking.test_files:
            test_functions = _test_functions_for_file(self, test_file, repo_path, file_test_functions_cache)
            for test_func_name in test_functions:
                test_mapping = f"{test_file}::{test_func_name}"
                if test_mapping not in test_functions_set:
                    test_functions_set.add(test_mapping)

        story.source_functions = list(source_functions_set)
        story.test_functions = list(test_functions_set)

    @beartype
    @require(lambda self, features: isinstance(features, list), "Features must be list")
    @require(lambda self, features: all(isinstance(f, Feature) for f in features), "All items must be Feature")
    @ensure(lambda result: result is None, "Must return None")
    def link_to_specs(self, features: list[Feature], repo_path: Path | None = None) -> None:
        """
        Map code files → feature specs using AST analysis (parallelized).

        Args:
            features: List of features to link
            repo_path: Repository path (defaults to self.repo_path)
        """
        if repo_path is None:
            repo_path = self.repo_path

        if not features:
            return

        # Pre-collect all files once (avoid repeated glob operations)
        impl_files: list[Path] = []
        for pattern in ["src/**/*.py", "lib/**/*.py", "app/**/*.py"]:
            impl_files.extend(repo_path.glob(pattern))

        test_files: list[Path] = []
        for pattern in ["tests/**/*.py", "test/**/*.py", "**/test_*.py", "**/*_test.py"]:
            test_files.extend(repo_path.glob(pattern))

        # Remove duplicates
        impl_files = list(set(impl_files))
        test_files = list(set(test_files))

        # Pre-compute caches to avoid repeated AST parsing and hash computation
        # This is a major performance optimization for large codebases
        console.print("[dim]Pre-computing file caches (AST parsing, hashes)...[/dim]")
        file_functions_cache: dict[str, list[str]] = {}
        file_test_functions_cache: dict[str, list[str]] = {}
        file_hashes_cache: dict[str, str] = {}

        # Pre-index files by stem (filename without extension) for O(1) lookup
        # This avoids iterating through all files for each feature
        impl_files_by_stem: dict[str, list[Path]] = {}  # stem -> [file_paths]
        test_files_by_stem: dict[str, list[Path]] = {}  # stem -> [file_paths]

        # Build inverted index: for each word/substring, track which stems contain it
        # This allows O(1) lookup of candidate stems instead of O(n) iteration
        impl_stems_by_substring: dict[str, set[str]] = {}  # substring -> {stems}
        test_stems_by_substring: dict[str, set[str]] = {}  # substring -> {stems}

        for file_path in impl_files:
            self._index_impl_file_for_link_cache(
                file_path,
                repo_path,
                file_functions_cache,
                file_hashes_cache,
                impl_files_by_stem,
                impl_stems_by_substring,
            )

        for file_path in test_files:
            self._index_test_file_for_link_cache(
                file_path,
                repo_path,
                file_test_functions_cache,
                file_hashes_cache,
                test_files_by_stem,
                test_stems_by_substring,
            )

        console.print(
            f"[dim]✓ Cached {len(file_functions_cache)} implementation files, {len(file_test_functions_cache)} test files[/dim]"
        )

        linking_ctx = _FeatureLinkingContext(
            repo_path=repo_path,
            impl_files=impl_files,
            test_files=test_files,
            file_functions_cache=file_functions_cache,
            file_test_functions_cache=file_test_functions_cache,
            file_hashes_cache=file_hashes_cache,
            impl_files_by_stem=impl_files_by_stem,
            test_files_by_stem=test_files_by_stem,
            impl_stems_by_substring=impl_stems_by_substring,
            test_stems_by_substring=test_stems_by_substring,
        )
        self._run_parallel_feature_linking(features, linking_ctx)

    def _index_impl_file_for_link_cache(
        self,
        file_path: Path,
        repo_path: Path,
        file_functions_cache: dict[str, list[str]],
        file_hashes_cache: dict[str, str],
        impl_files_by_stem: dict[str, list[Path]],
        impl_stems_by_substring: dict[str, set[str]],
    ) -> None:
        if not self._is_implementation_file(file_path):
            return
        rel_path = str(file_path.relative_to(repo_path))
        stem = file_path.stem.lower()

        if stem not in impl_files_by_stem:
            impl_files_by_stem[stem] = []
        impl_files_by_stem[stem].append(file_path)

        stem_parts = stem.split("_")
        for part in stem_parts:
            if len(part) > 2:
                if part not in impl_stems_by_substring:
                    impl_stems_by_substring[part] = set()
                impl_stems_by_substring[part].add(stem)
        if stem not in impl_stems_by_substring:
            impl_stems_by_substring[stem] = set()
        impl_stems_by_substring[stem].add(stem)

        if rel_path not in file_functions_cache:
            functions = self.extract_function_mappings(file_path)
            file_functions_cache[rel_path] = functions

        if rel_path not in file_hashes_cache and file_path.exists():
            try:
                source_tracking = SourceTracking()
                source_tracking.update_hash(file_path)
                file_hashes_cache[rel_path] = source_tracking.file_hashes.get(rel_path, "")
            except (OSError, ValueError):
                pass

    def _index_test_file_for_link_cache(
        self,
        file_path: Path,
        repo_path: Path,
        file_test_functions_cache: dict[str, list[str]],
        file_hashes_cache: dict[str, str],
        test_files_by_stem: dict[str, list[Path]],
        test_stems_by_substring: dict[str, set[str]],
    ) -> None:
        if not self._is_test_file(file_path):
            return
        rel_path = str(file_path.relative_to(repo_path))
        stem = file_path.stem.lower()

        if stem not in test_files_by_stem:
            test_files_by_stem[stem] = []
        test_files_by_stem[stem].append(file_path)

        stem_parts = stem.split("_")
        for part in stem_parts:
            if len(part) > 2:
                if part not in test_stems_by_substring:
                    test_stems_by_substring[part] = set()
                test_stems_by_substring[part].add(stem)
        if stem not in test_stems_by_substring:
            test_stems_by_substring[stem] = set()
        test_stems_by_substring[stem].add(stem)

        if rel_path not in file_test_functions_cache:
            test_functions = self.extract_test_mappings(file_path)
            file_test_functions_cache[rel_path] = test_functions

        if rel_path not in file_hashes_cache and file_path.exists():
            try:
                source_tracking = SourceTracking()
                source_tracking.update_hash(file_path)
                file_hashes_cache[rel_path] = source_tracking.file_hashes.get(rel_path, "")
            except (OSError, ValueError):
                pass

    def _run_parallel_feature_linking(
        self,
        features: list[Feature],
        ctx: _FeatureLinkingContext,
    ) -> None:
        if os.environ.get("TEST_MODE") == "true":
            max_workers = max(1, min(2, len(features)))
        else:
            max_workers = min(os.cpu_count() or 4, 8, len(features))

        executor = ThreadPoolExecutor(max_workers=max_workers)
        interrupted = False
        wait_on_shutdown = os.environ.get("TEST_MODE") != "true"

        progress_columns, progress_kwargs = get_progress_config()
        with Progress(
            *progress_columns,
            console=console,
            **progress_kwargs,
        ) as progress:
            task = progress.add_task(
                f"[cyan]Linking {len(features)} features to source files...",
                total=len(features),
            )

            try:
                future_to_feature = {
                    executor.submit(self._link_feature_to_specs, feature, ctx): feature for feature in features
                }
                interrupted = _drain_feature_link_futures(future_to_feature, progress, task, len(features))
                if interrupted:
                    raise KeyboardInterrupt
            except KeyboardInterrupt:
                interrupted = True
                executor.shutdown(wait=False, cancel_futures=True)
                raise
            finally:
                if not interrupted:
                    executor.shutdown(wait=wait_on_shutdown)
                else:
                    executor.shutdown(wait=False)

    @beartype
    @require(lambda self, file_path: isinstance(file_path, Path), "File path must be Path")
    @ensure(lambda self, file_path, result: isinstance(result, list), "Must return list")
    def extract_function_mappings(self, file_path: Path) -> list[str]:
        """
        Extract function names from code.

        Args:
            file_path: Path to Python file

        Returns:
            List of function names
        """
        if not file_path.exists() or file_path.suffix != ".py":
            return []

        try:
            with file_path.open(encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            functions: list[str] = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append(node.name)

            return functions
        except (SyntaxError, UnicodeDecodeError):
            # Skip files with syntax errors or encoding issues
            return []

    @beartype
    @require(lambda self, test_file: isinstance(test_file, Path), "Test file path must be Path")
    @ensure(lambda self, test_file, result: isinstance(result, list), "Must return list")
    def extract_test_mappings(self, test_file: Path) -> list[str]:
        """
        Extract test function names from test file.

        Args:
            test_file: Path to test file

        Returns:
            List of test function names
        """
        if not test_file.exists() or test_file.suffix != ".py":
            return []

        try:
            with test_file.open(encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(test_file))

            test_functions: list[str] = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                    # Check if it's a test function (starts with test_)
                    test_functions.append(node.name)

            return test_functions
        except (SyntaxError, UnicodeDecodeError):
            # Skip files with syntax errors or encoding issues
            return []

    def _is_implementation_file(self, file_path: Path) -> bool:
        """
        Check if file is an implementation file (not a test).

        Args:
            file_path: Path to check

        Returns:
            True if implementation file, False otherwise
        """
        # Exclude test files
        if self._is_test_file(file_path):
            return False
        # Exclude common non-implementation directories
        excluded_dirs = {"__pycache__", ".git", ".venv", "venv", "node_modules", ".specfact"}
        return not any(part in excluded_dirs for part in file_path.parts)

    def _is_test_file(self, file_path: Path) -> bool:
        """
        Check if file is a test file.

        Args:
            file_path: Path to check

        Returns:
            True if test file, False otherwise
        """
        name = file_path.name
        # Check filename patterns
        if name.startswith("test_") or name.endswith("_test.py"):
            return True
        # Check directory patterns
        test_dirs = {"tests", "test", "spec"}
        return any(part in test_dirs for part in file_path.parts)
