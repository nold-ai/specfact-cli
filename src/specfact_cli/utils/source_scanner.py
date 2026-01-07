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

from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.progress import Progress

from specfact_cli.models.plan import Feature
from specfact_cli.models.source_tracking import SourceTracking
from specfact_cli.utils.terminal import get_progress_config


console = Console()


@dataclass
class SourceArtifactMap:
    """Mapping of source artifacts to features/stories."""

    implementation_files: dict[str, list[str]] = field(default_factory=dict)  # file_path -> [feature_keys]
    test_files: dict[str, list[str]] = field(default_factory=dict)  # file_path -> [feature_keys]
    function_mappings: dict[str, list[str]] = field(default_factory=dict)  # "file.py::func" -> [story_keys]
    test_mappings: dict[str, list[str]] = field(default_factory=dict)  # "test_file.py::test_func" -> [story_keys]


class SourceArtifactScanner:
    """Scanner for discovering and linking source artifacts to specifications."""

    def __init__(self, repo_path: Path) -> None:
        """
        Initialize scanner with repository path.

        Args:
            repo_path: Path to repository root
        """
        self.repo_path = repo_path.resolve()

    @beartype
    @require(lambda self: self.repo_path.exists(), "Repository path must exist")
    @require(lambda self: self.repo_path.is_dir(), "Repository path must be directory")
    @ensure(lambda self, result: isinstance(result, SourceArtifactMap), "Must return SourceArtifactMap")
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

    def _link_feature_to_specs(
        self,
        feature: Feature,
        repo_path: Path,
        impl_files: list[Path],
        test_files: list[Path],
        file_functions_cache: dict[str, list[str]] | None = None,
        file_test_functions_cache: dict[str, list[str]] | None = None,
        file_hashes_cache: dict[str, str] | None = None,
        impl_files_by_stem: dict[str, list[Path]] | None = None,
        test_files_by_stem: dict[str, list[Path]] | None = None,
        impl_stems_by_substring: dict[str, set[str]] | None = None,
        test_stems_by_substring: dict[str, set[str]] | None = None,
    ) -> None:
        """
        Link a single feature to matching files (thread-safe helper).

        Args:
            feature: Feature to link
            repo_path: Repository path
            impl_files: Pre-collected implementation files
            test_files: Pre-collected test files
            file_functions_cache: Pre-computed function mappings cache (file_path -> [functions])
            file_test_functions_cache: Pre-computed test function mappings cache (file_path -> [test_functions])
            file_hashes_cache: Pre-computed file hashes cache (file_path -> hash)
        """
        if feature.source_tracking is None:
            feature.source_tracking = SourceTracking()

        # Initialize caches if not provided (for backward compatibility)
        if file_functions_cache is None:
            file_functions_cache = {}
        if file_test_functions_cache is None:
            file_test_functions_cache = {}
        if file_hashes_cache is None:
            file_hashes_cache = {}
        if impl_files_by_stem is None:
            impl_files_by_stem = {}
        if test_files_by_stem is None:
            test_files_by_stem = {}
        if impl_stems_by_substring is None:
            impl_stems_by_substring = {}
        if test_stems_by_substring is None:
            test_stems_by_substring = {}

        # Try to match feature key/title to files
        feature_key_lower = feature.key.lower()
        feature_title_words = [w for w in feature.title.lower().split() if len(w) > 3]

        # Use indexed lookup for O(1) file matching instead of O(n) iteration
        # This is much faster for large codebases with many features
        matched_impl_files: set[str] = set()
        matched_test_files: set[str] = set()

        # Strategy: Use inverted index for O(1) candidate lookup instead of O(n) iteration
        # This eliminates the slowdown that occurs when iterating through all stems

        # 1. Check if feature key matches any file stem directly (fastest path - O(1))
        if feature_key_lower in impl_files_by_stem:
            for file_path in impl_files_by_stem[feature_key_lower]:
                rel_path = str(file_path.relative_to(repo_path))
                matched_impl_files.add(rel_path)

        # 2. Check if any title word matches file stems exactly (O(k) where k = number of title words)
        for word in feature_title_words:
            if word in impl_files_by_stem:
                for file_path in impl_files_by_stem[word]:
                    rel_path = str(file_path.relative_to(repo_path))
                    matched_impl_files.add(rel_path)

        # 3. Use inverted index for O(1) candidate stem lookup (much faster than O(n) iteration)
        # Build candidate stems using the inverted index
        # Optimization: Use set union instead of multiple updates to avoid repeated hash operations
        candidate_stems: set[str] = set()

        # Collect all sets to union in one operation (more efficient than multiple updates)
        sets_to_union: list[set[str]] = []

        # Check feature key in inverted index
        if feature_key_lower in impl_stems_by_substring:
            sets_to_union.append(impl_stems_by_substring[feature_key_lower])

        # Check each title word in inverted index
        for word in feature_title_words:
            if word in impl_stems_by_substring:
                sets_to_union.append(impl_stems_by_substring[word])

        # Union all sets at once (more efficient than multiple updates)
        if sets_to_union:
            candidate_stems = set().union(*sets_to_union)

        # Check only candidate stems (much smaller set, found via O(1) lookup)
        for stem in candidate_stems:
            if stem in impl_files_by_stem:
                for file_path in impl_files_by_stem[stem]:
                    rel_path = str(file_path.relative_to(repo_path))
                    matched_impl_files.add(rel_path)

        # Add matched implementation files to feature
        for rel_path in matched_impl_files:
            if rel_path not in feature.source_tracking.implementation_files:
                feature.source_tracking.implementation_files.append(rel_path)
                # Use cached hash if available (all hashes should be pre-computed)
                if rel_path in file_hashes_cache:
                    feature.source_tracking.file_hashes[rel_path] = file_hashes_cache[rel_path]
                else:
                    # Fallback: compute hash if not in cache (shouldn't happen, but safe fallback)
                    file_path = repo_path / rel_path
                    if file_path.exists():
                        feature.source_tracking.update_hash(file_path)

        # Check if feature key matches any test file stem directly (O(1))
        if feature_key_lower in test_files_by_stem:
            for file_path in test_files_by_stem[feature_key_lower]:
                rel_path = str(file_path.relative_to(repo_path))
                matched_test_files.add(rel_path)

        # Check if any title word matches test file stems exactly (O(k))
        for word in feature_title_words:
            if word in test_files_by_stem:
                for file_path in test_files_by_stem[word]:
                    rel_path = str(file_path.relative_to(repo_path))
                    matched_test_files.add(rel_path)

        # Use inverted index for O(1) candidate test stem lookup
        # Optimization: Use set union instead of multiple updates
        candidate_test_stems: set[str] = set()

        # Collect all sets to union in one operation (more efficient than multiple updates)
        test_sets_to_union: list[set[str]] = []

        # Check feature key in inverted index
        if feature_key_lower in test_stems_by_substring:
            test_sets_to_union.append(test_stems_by_substring[feature_key_lower])

        # Check each title word in inverted index
        for word in feature_title_words:
            if word in test_stems_by_substring:
                test_sets_to_union.append(test_stems_by_substring[word])

        # Union all sets at once (more efficient than multiple updates)
        if test_sets_to_union:
            candidate_test_stems = set().union(*test_sets_to_union)

        # Check only candidate test stems (found via O(1) lookup)
        for stem in candidate_test_stems:
            if stem in test_files_by_stem:
                for file_path in test_files_by_stem[stem]:
                    rel_path = str(file_path.relative_to(repo_path))
                    matched_test_files.add(rel_path)

        # Add matched test files to feature
        for rel_path in matched_test_files:
            if rel_path not in feature.source_tracking.test_files:
                feature.source_tracking.test_files.append(rel_path)
                # Use cached hash if available (all hashes should be pre-computed)
                if rel_path in file_hashes_cache:
                    feature.source_tracking.file_hashes[rel_path] = file_hashes_cache[rel_path]
                else:
                    # Fallback: compute hash if not in cache (shouldn't happen, but safe fallback)
                    file_path = repo_path / rel_path
                    if file_path.exists():
                        feature.source_tracking.update_hash(file_path)

        # Extract function mappings for stories using cached results
        # Optimization: Use sets for O(1) lookups instead of O(n) list membership checks
        # This prevents slowdown as stories accumulate more function mappings
        for story in feature.stories:
            # Convert to sets for fast lookups (only if we need to add many items)
            # For small lists, the overhead isn't worth it, but for large lists it's critical
            source_functions_set = set(story.source_functions) if story.source_functions else set()
            test_functions_set = set(story.test_functions) if story.test_functions else set()

            for impl_file in feature.source_tracking.implementation_files:
                # Use cached functions if available (all functions should be pre-computed)
                if impl_file in file_functions_cache:
                    functions = file_functions_cache[impl_file]
                else:
                    # Fallback: compute if not in cache (shouldn't happen, but safe fallback)
                    file_path = repo_path / impl_file
                    functions = self.extract_function_mappings(file_path) if file_path.exists() else []

                for func_name in functions:
                    func_mapping = f"{impl_file}::{func_name}"
                    if func_mapping not in source_functions_set:
                        source_functions_set.add(func_mapping)

            for test_file in feature.source_tracking.test_files:
                # Use cached test functions if available (all test functions should be pre-computed)
                if test_file in file_test_functions_cache:
                    test_functions = file_test_functions_cache[test_file]
                else:
                    # Fallback: compute if not in cache (shouldn't happen, but safe fallback)
                    file_path = repo_path / test_file
                    test_functions = self.extract_test_mappings(file_path) if file_path.exists() else []

                for test_func_name in test_functions:
                    test_mapping = f"{test_file}::{test_func_name}"
                    if test_mapping not in test_functions_set:
                        test_functions_set.add(test_mapping)

            # Convert back to lists (Pydantic models expect lists)
            story.source_functions = list(source_functions_set)
            story.test_functions = list(test_functions_set)

        # Update sync timestamp
        feature.source_tracking.update_sync_timestamp()

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

        # Pre-parse all implementation files once and index by stem
        for file_path in impl_files:
            if self._is_implementation_file(file_path):
                rel_path = str(file_path.relative_to(repo_path))
                stem = file_path.stem.lower()

                # Index by stem for fast lookup
                if stem not in impl_files_by_stem:
                    impl_files_by_stem[stem] = []
                impl_files_by_stem[stem].append(file_path)

                # Build inverted index: extract all meaningful substrings from stem
                # (words separated by underscores, and the full stem)
                stem_parts = stem.split("_")
                for part in stem_parts:
                    if len(part) > 2:  # Only index meaningful substrings
                        if part not in impl_stems_by_substring:
                            impl_stems_by_substring[part] = set()
                        impl_stems_by_substring[part].add(stem)
                # Also index the full stem
                if stem not in impl_stems_by_substring:
                    impl_stems_by_substring[stem] = set()
                impl_stems_by_substring[stem].add(stem)

                # Cache functions
                if rel_path not in file_functions_cache:
                    functions = self.extract_function_mappings(file_path)
                    file_functions_cache[rel_path] = functions

                # Cache hash
                if rel_path not in file_hashes_cache and file_path.exists():
                    try:
                        source_tracking = SourceTracking()
                        source_tracking.update_hash(file_path)
                        file_hashes_cache[rel_path] = source_tracking.file_hashes.get(rel_path, "")
                    except Exception:
                        pass  # Skip files that can't be hashed

        # Pre-parse all test files once and index by stem
        for file_path in test_files:
            if self._is_test_file(file_path):
                rel_path = str(file_path.relative_to(repo_path))
                stem = file_path.stem.lower()

                # Index by stem for fast lookup
                if stem not in test_files_by_stem:
                    test_files_by_stem[stem] = []
                test_files_by_stem[stem].append(file_path)

                # Build inverted index for test files
                stem_parts = stem.split("_")
                for part in stem_parts:
                    if len(part) > 2:  # Only index meaningful substrings
                        if part not in test_stems_by_substring:
                            test_stems_by_substring[part] = set()
                        test_stems_by_substring[part].add(stem)
                # Also index the full stem
                if stem not in test_stems_by_substring:
                    test_stems_by_substring[stem] = set()
                test_stems_by_substring[stem].add(stem)

                # Cache test functions
                if rel_path not in file_test_functions_cache:
                    test_functions = self.extract_test_mappings(file_path)
                    file_test_functions_cache[rel_path] = test_functions

                # Cache hash
                if rel_path not in file_hashes_cache and file_path.exists():
                    try:
                        source_tracking = SourceTracking()
                        source_tracking.update_hash(file_path)
                        file_hashes_cache[rel_path] = source_tracking.file_hashes.get(rel_path, "")
                    except Exception:
                        pass  # Skip files that can't be hashed

        console.print(
            f"[dim]✓ Cached {len(file_functions_cache)} implementation files, {len(file_test_functions_cache)} test files[/dim]"
        )

        # Process features in parallel with progress reporting
        # In test mode, use fewer workers to avoid resource contention
        if os.environ.get("TEST_MODE") == "true":
            max_workers = max(1, min(2, len(features)))  # Max 2 workers in test mode
        else:
            max_workers = min(os.cpu_count() or 4, 8, len(features))  # Cap at 8 workers

        executor = ThreadPoolExecutor(max_workers=max_workers)
        interrupted = False
        # In test mode, use wait=False to avoid hanging on shutdown
        wait_on_shutdown = os.environ.get("TEST_MODE") != "true"

        # Add progress reporting
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
                    executor.submit(
                        self._link_feature_to_specs,
                        feature,
                        repo_path,
                        impl_files,
                        test_files,
                        file_functions_cache,
                        file_test_functions_cache,
                        file_hashes_cache,
                        impl_files_by_stem,
                        test_files_by_stem,
                        impl_stems_by_substring,
                        test_stems_by_substring,
                    ): feature
                    for feature in features
                }
                completed_count = 0
                try:
                    for future in as_completed(future_to_feature):
                        try:
                            future.result()  # Wait for completion
                            completed_count += 1
                            # Update progress with meaningful description
                            progress.update(
                                task,
                                completed=completed_count,
                                description=f"[cyan]Linking features to source files... ({completed_count}/{len(features)} features)",
                            )
                        except KeyboardInterrupt:
                            interrupted = True
                            for f in future_to_feature:
                                if not f.done():
                                    f.cancel()
                            break
                        except Exception:
                            # Suppress other exceptions but still count as completed
                            completed_count += 1
                            progress.update(
                                task,
                                completed=completed_count,
                                description=f"[cyan]Linking features to source files... ({completed_count}/{len(features)})",
                            )
                except KeyboardInterrupt:
                    interrupted = True
                    for f in future_to_feature:
                        if not f.done():
                            f.cancel()
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
