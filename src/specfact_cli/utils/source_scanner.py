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

from specfact_cli.models.plan import Feature
from specfact_cli.models.source_tracking import SourceTracking


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
        self, feature: Feature, repo_path: Path, impl_files: list[Path], test_files: list[Path]
    ) -> None:
        """
        Link a single feature to matching files (thread-safe helper).

        Args:
            feature: Feature to link
            repo_path: Repository path
            impl_files: Pre-collected implementation files
            test_files: Pre-collected test files
        """
        if feature.source_tracking is None:
            feature.source_tracking = SourceTracking()

        # Try to match feature key/title to files
        feature_key_lower = feature.key.lower()
        feature_title_lower = feature.title.lower()

        # Search for matching implementation files
        for file_path in impl_files:
            if self._is_implementation_file(file_path):
                file_name_lower = file_path.stem.lower()
                # Simple matching: check if feature key or title appears in filename
                if feature_key_lower in file_name_lower or any(
                    word in file_name_lower for word in feature_title_lower.split() if len(word) > 3
                ):
                    rel_path = str(file_path.relative_to(repo_path))
                    if rel_path not in feature.source_tracking.implementation_files:
                        feature.source_tracking.implementation_files.append(rel_path)
                    # Compute and store hash
                    feature.source_tracking.update_hash(file_path)

        # Search for matching test files
        for file_path in test_files:
            if self._is_test_file(file_path):
                file_name_lower = file_path.stem.lower()
                # Match test files to features
                if feature_key_lower in file_name_lower or any(
                    word in file_name_lower for word in feature_title_lower.split() if len(word) > 3
                ):
                    rel_path = str(file_path.relative_to(repo_path))
                    if rel_path not in feature.source_tracking.test_files:
                        feature.source_tracking.test_files.append(rel_path)
                    # Compute and store hash
                    feature.source_tracking.update_hash(file_path)

        # Extract function mappings for stories
        for story in feature.stories:
            for impl_file in feature.source_tracking.implementation_files:
                file_path = repo_path / impl_file
                if file_path.exists():
                    functions = self.extract_function_mappings(file_path)
                    for func_name in functions:
                        func_mapping = f"{impl_file}::{func_name}"
                        if func_mapping not in story.source_functions:
                            story.source_functions.append(func_mapping)

            for test_file in feature.source_tracking.test_files:
                file_path = repo_path / test_file
                if file_path.exists():
                    test_functions = self.extract_test_mappings(file_path)
                    for test_func_name in test_functions:
                        test_mapping = f"{test_file}::{test_func_name}"
                        if test_mapping not in story.test_functions:
                            story.test_functions.append(test_mapping)

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

        # Process features in parallel
        # In test mode, use fewer workers to avoid resource contention
        if os.environ.get("TEST_MODE") == "true":
            max_workers = max(1, min(2, len(features)))  # Max 2 workers in test mode
        else:
            max_workers = min(os.cpu_count() or 4, 8, len(features))  # Cap at 8 workers

        executor = ThreadPoolExecutor(max_workers=max_workers)
        interrupted = False
        # In test mode, use wait=False to avoid hanging on shutdown
        wait_on_shutdown = os.environ.get("TEST_MODE") != "true"
        try:
            future_to_feature = {
                executor.submit(self._link_feature_to_specs, feature, repo_path, impl_files, test_files): feature
                for feature in features
            }
            try:
                for future in as_completed(future_to_feature):
                    try:
                        future.result()  # Wait for completion
                    except KeyboardInterrupt:
                        interrupted = True
                        for f in future_to_feature:
                            if not f.done():
                                f.cancel()
                        break
                    except Exception:
                        # Suppress other exceptions (same as before)
                        pass
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
