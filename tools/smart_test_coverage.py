#!/usr/bin/env python3
"""
Smart Test Coverage Management System

This script provides intelligent test coverage management that:
1. Detects changes in source files since last coverage run
2. Caches coverage results with file hashes
3. Only runs full tests when necessary
4. Provides fast incremental testing for development
5. Supports multiple testing levels: unit, folder, integration, e2e, and full

Usage:
    python tools/smart_test_coverage.py check      # Check if full test needed
    python tools/smart_test_coverage.py run        # Run tests with smart detection
    python tools/smart_test_coverage.py run --level unit        # Run only unit tests for modified files
    python tools/smart_test_coverage.py run --level folder      # Run tests for modified file folders
    python tools/smart_test_coverage.py run --level integration # Run all integration tests
    python tools/smart_test_coverage.py run --level e2e         # Run end-to-end tests only
    python tools/smart_test_coverage.py run --level full        # Run full test suite
    python tools/smart_test_coverage.py force      # Force full test run
    python tools/smart_test_coverage.py status     # Show current status
    python tools/smart_test_coverage.py threshold  # Check coverage threshold
    python tools/smart_test_coverage.py index      # Refresh baseline hashes without running tests
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# TOML parsing - prefer tomlkit (style-preserving, widely used), fallback to tomllib (Python 3.11+)
try:
    import tomlkit  # type: ignore[import]

    TOML_LIBRARY = "tomlkit"
except ImportError:
    try:
        import tomllib  # type: ignore[import]

        TOML_LIBRARY = "tomllib"
    except ImportError:
        raise ImportError("No TOML parser available. Please install tomlkit (recommended) or use Python 3.11+")


class CoverageThresholdError(Exception):
    """Raised when coverage falls below the required threshold."""


class SmartCoverageManager:
    def __init__(self, project_root: str = ".", coverage_threshold: float | None = None):
        self.project_root = Path(project_root).resolve()
        self.cache_dir = self.project_root / ".coverage_cache"
        self.cache_file = self.cache_dir / "coverage_cache.json"
        # Remember last computed git-changed set per run to avoid re-spawning git repeatedly
        self._git_changed_cache: set[str] | None = None

        # Source directories that affect test coverage (from pyproject.toml)
        self.source_dirs = ["src", "tools"]
        self.test_dirs = ["tests"]

        # Test level directories for different test types
        self.test_level_dirs = {
            "unit": "tests/unit",
            "integration": "tests/integration",
            "e2e": "tests/integration",  # E2E tests are a subset of integration tests
        }

        # Configuration files that affect test behavior
        self.config_files = [
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
            "requirements-dev.txt",
            ".pre-commit-config.yaml",
            "pytest.ini",
            "tox.ini",
            "conftest.py",
        ]

        # File patterns to exclude from change detection
        self.exclude_patterns = [
            "*.md",  # Documentation
            "*.rst",  # Documentation
            "*.txt",  # Text files (except requirements)
            "*.json",  # JSON files (except package.json)
            "*.yaml",  # YAML files (except config)
            "*.yml",  # YAML files (except config)
            "*.log",  # Log files
            "*.tmp",  # Temporary files
            "*.cache",  # Cache files
            "*.pyc",  # Python bytecode
            "__pycache__",  # Python cache directories
            ".git",  # Git directory
            ".coverage_cache",  # Our own cache
            "logs",  # Log directories
            "docs",  # Documentation directories
            "papers",  # Research papers
            "presentations",  # Presentation files
            "images",  # Image files
            "*.png",  # Image files
            "*.jpg",  # Image files
            "*.jpeg",  # Image files
            "*.gif",  # Image files
            "*.svg",  # Image files
            "*.ico",  # Icon files
            "*.pdf",  # PDF files
            "*.doc",  # Document files
            "*.docx",  # Document files
            "*.ppt",  # Presentation files
            "*.pptx",  # Presentation files
            "*.xls",  # Spreadsheet files
            "*.xlsx",  # Spreadsheet files
        ]

        # Coverage threshold - read from pyproject.toml or environment
        self.coverage_threshold = coverage_threshold or self._get_coverage_threshold()

        # Ensure cache directory exists
        self.cache_dir.mkdir(exist_ok=True)

        # Load existing cache
        self.cache = self._load_cache()

        # Optional: allow selecting a specific hatch test environment via env var
        # Examples:
        #   HATCH_TEST_ENV=hatch-test.py3.13
        #   HATCH_TEST_ENV=py3.13 (will be prefixed with 'hatch-test.')
        # Backward-compat alias: HATCH_TEST_PY
        self.hatch_test_env = os.environ.get("HATCH_TEST_ENV") or os.environ.get("HATCH_TEST_PY")
        # Optional: allow specifying hatch binary explicitly
        self.hatch_bin = os.environ.get("HATCH_BIN") or shutil.which("hatch") or "hatch"
        # Allow disabling hatch usage in constrained environments
        self.use_hatch = os.environ.get("SMART_TEST_USE_HATCH", "true").lower() not in ("0", "false", "no")

    def _build_hatch_test_cmd(
        self, with_coverage: bool, extra_args: list[str] | None = None, parallel: bool = False
    ) -> list[str]:
        """Construct the hatch test command, honoring optional env selection."""
        base_cmd: list[str] = [self.hatch_bin, "test"]
        if self.hatch_test_env:
            env_name = (
                self.hatch_test_env
                if self.hatch_test_env.startswith("hatch-test.")
                else f"hatch-test.{self.hatch_test_env}"
            )
            base_cmd += ["-e", env_name]
        if with_coverage:
            base_cmd += ["--cover", "-v"]
        else:
            base_cmd += ["-v"]
        # Parallel execution is handled by hatch configuration (parallel = true)
        # No need to add -n parameter manually
        if extra_args:
            base_cmd += extra_args
        return base_cmd

    def _build_pytest_cmd(
        self, with_coverage: bool, extra_args: list[str] | None = None, parallel: bool = False
    ) -> list[str]:
        """Construct a direct pytest command as a fallback when hatch cannot be used."""
        base_cmd: list[str] = [sys.executable, "-m", "pytest"]
        if with_coverage:
            # Use coverage for src and tools, align with pyproject config
            base_cmd += ["--cov=src", "--cov=tools", "--cov-report=term-missing", "-v"]
        else:
            base_cmd += ["-v"]
        # Parallel execution is handled by hatch configuration (parallel = true)
        # No need to add -n parameter manually
        if extra_args:
            base_cmd += extra_args
        return base_cmd

    def _get_coverage_threshold(self) -> float:
        """Get coverage threshold from pyproject.toml or environment variable."""
        # First check environment variable
        env_threshold = os.environ.get("COVERAGE_THRESHOLD")
        if env_threshold:
            try:
                return float(env_threshold)
            except ValueError:
                print(f"⚠️  Invalid COVERAGE_THRESHOLD environment variable: {env_threshold}")

        # Try to read from pyproject.toml
        pyproject_path = self.project_root / "pyproject.toml"
        if pyproject_path.exists():
            try:
                if TOML_LIBRARY == "tomlkit":
                    # Use tomlkit (recommended - style-preserving, works with text mode)
                    with open(pyproject_path, encoding="utf-8") as f:
                        parsed = tomlkit.parse(f.read())  # type: ignore[possibly-unbound]
                    # tomlkit.Table is dict-like, convert to dict for type safety
                    config: dict[str, Any] = dict(parsed.unwrap() if hasattr(parsed, "unwrap") else parsed)  # type: ignore[assignment,arg-type]
                elif TOML_LIBRARY == "tomllib":
                    # Use tomllib (stdlib, Python 3.11+ - requires binary mode)
                    with open(pyproject_path, "rb") as f:
                        config = tomllib.load(f)  # type: ignore[possibly-unbound]
                else:
                    # This should never happen due to ImportError in import block, but type checker needs it
                    raise RuntimeError(f"Unknown TOML library: {TOML_LIBRARY}")

                # Look for fail_under in [tool.coverage.report]
                coverage_config = config.get("tool", {}).get("coverage", {}).get("report", {})
                fail_under = coverage_config.get("fail_under")

                if fail_under is not None:
                    return float(fail_under)
            except (KeyError, ValueError, AttributeError) as e:
                print(f"⚠️  Could not read coverage threshold from pyproject.toml: {e}")

        # Default fallback (used only when env and pyproject are unavailable/invalid)
        # Note: When pyproject.toml provides fail_under, that value (e.g., 70) takes precedence.
        return 80.0

    def _load_cache(self) -> dict:
        """Load coverage cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file) as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {
            "last_full_run": None,
            "coverage_percentage": 0,
            "file_hashes": {},
            "test_count": 0,
            "coverage_data": {},
        }

    def _save_cache(self):
        """Save coverage cache to file."""
        with open(self.cache_file, "w") as f:
            json.dump(self.cache, f, indent=2)

    def _get_file_hash(self, file_path: Path) -> str:
        """Get SHA256 hash of file content."""
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except (FileNotFoundError, PermissionError):
            return ""

    def _should_exclude_file(self, file_path: Path) -> bool:
        """Check if a file should be excluded from change detection."""
        file_str = str(file_path)

        # Check against exclude patterns
        for pattern in self.exclude_patterns:
            if pattern.startswith("*."):
                # File extension pattern
                if file_str.endswith(pattern[1:]):
                    return True
            elif pattern.endswith("*"):
                # Directory pattern
                if pattern[:-1] in file_str:
                    return True
            else:
                # Exact match
                if file_str.endswith(pattern):
                    return True

        return False

    def _is_config_file(self, file_path: Path) -> bool:
        """Check if a file is a configuration file that affects test behavior."""
        file_name = file_path.name
        return file_name in self.config_files

    def _get_source_files(self) -> list[Path]:
        """Get all source files that affect coverage."""
        source_files = []
        for source_dir in self.source_dirs:
            source_path = self.project_root / source_dir
            if source_path.exists():
                for py_file in source_path.rglob("*.py"):
                    if not self._should_exclude_file(py_file):
                        source_files.append(py_file)
        return source_files

    def _get_test_files(self) -> list[Path]:
        """Get all test files including fixtures and helpers."""
        test_files = []
        for test_dir in self.test_dirs:
            test_path = self.project_root / test_dir
            if test_path.exists():
                # Include all Python files in tests directory to catch:
                # - test_*.py files
                # - conftest.py fixtures
                # - helper utilities and support modules
                for py_file in test_path.rglob("*.py"):
                    if not self._should_exclude_file(py_file):
                        test_files.append(py_file)
        return test_files

    def _get_modified_test_files(self) -> list[Path]:
        """Get modified test files using git candidates; fallback to full scan if git unavailable."""
        if not self.cache.get("last_full_run"):
            return []
        modified: list[Path] = []
        cached = self.cache.get("test_file_hashes", {})
        git_changed = self._git_changed_paths()
        if git_changed:
            for rel in git_changed:
                p = self.project_root / rel
                if not p.exists() or self._should_exclude_file(p):
                    continue
                # Only consider test tree
                if not any(str(p).startswith(str(self.project_root / d)) for d in self.test_dirs):
                    continue
                h = self._get_file_hash(p)
                if h and cached.get(rel) != h:
                    modified.append(p)
            return modified
        # Fallback: scan all known test files and compare hashes
        for p in self._get_test_files():
            rel = str(p.relative_to(self.project_root))
            if self._should_exclude_file(p):
                continue
            h = self._get_file_hash(p)
            if h and cached.get(rel) != h:
                modified.append(p)
        return modified

    def _split_tests_by_level(self, test_paths: list[Path]) -> tuple[list[Path], list[Path], list[Path]]:
        """Split provided test paths into (unit, integration, e2e) buckets.
        E2E is detected by filename containing 'e2e'."""
        unit: list[Path] = []
        integ: list[Path] = []
        e2e: list[Path] = []
        for p in test_paths:
            p_str = str(p)
            name = p.name.lower()
            if "tests/unit" in p_str:
                unit.append(p)
            elif "tests/integration" in p_str:
                if "e2e" in name:
                    e2e.append(p)
                else:
                    integ.append(p)
            else:
                # default to unit if under tests/ but unknown layout
                unit.append(p)
        return unit, integ, e2e

    def _get_test_files_by_level(self, test_level: str) -> list[Path]:
        """Get test files for a specific test level (unit, integration, e2e)."""
        test_files = []
        test_dir = self.test_level_dirs.get(test_level)
        if not test_dir:
            return test_files

        test_path = self.project_root / test_dir
        if test_path.exists():
            for py_file in test_path.rglob("*.py"):
                if not self._should_exclude_file(py_file):
                    # For e2e tests, only include files with 'e2e' in the name
                    if test_level == "e2e" and "e2e" not in py_file.name.lower():
                        continue
                    test_files.append(py_file)
        return test_files

    def _get_config_files(self) -> list[Path]:
        """Get all configuration files that affect test behavior."""
        config_files = []
        for config_file in self.config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                config_files.append(config_path)
        return config_files

    def _get_modified_files(self) -> list[Path]:
        """Get list of modified source files.
        Prefer git candidates; fallback to full scan when git is unavailable or reports no changes."""
        if not self.cache.get("last_full_run"):
            return []

        modified_files: list[Path] = []
        cached_hashes = self.cache.get("file_hashes", {})
        git_changed = self._git_changed_paths()
        if git_changed:
            for rel in git_changed:
                p = self.project_root / rel
                if not p.exists() or self._should_exclude_file(p):
                    continue
                # Only consider source roots (src, tools)
                if not any(str(p).startswith(str(self.project_root / d)) for d in self.source_dirs):
                    continue
                current_hash = self._get_file_hash(p)
                if current_hash:
                    cached_hash = cached_hashes.get(rel)
                    # Skip version-only changes
                    if cached_hash != current_hash and not self._is_version_only_change(
                        rel, cached_hash or "", current_hash
                    ):
                        modified_files.append(p)
            return modified_files
        # Fallback: scan all known source files and compare hashes
        for p in self._get_source_files():
            if self._should_exclude_file(p):
                continue
            rel = str(p.relative_to(self.project_root))
            current_hash = self._get_file_hash(p)
            cached_hash = cached_hashes.get(rel, "")
            if (
                current_hash
                and cached_hash != current_hash
                and not self._is_version_only_change(rel, cached_hash or "", current_hash)
            ):
                modified_files.append(p)
        return modified_files

    def _get_modified_folders(self) -> set[Path]:
        """Get set of parent folders containing modified files."""
        modified_files = self._get_modified_files()
        modified_folders = set()

        for file_path in modified_files:
            # Get parent folder
            parent_folder = file_path.parent
            modified_folders.add(parent_folder)

            # Also include grandparent if it's a meaningful module boundary
            grandparent = parent_folder.parent
            if grandparent.name in ["common", "agents", "tools"]:
                modified_folders.add(grandparent)

        return modified_folders

    def _get_unit_tests_for_files(self, modified_files: list[Path]) -> list[Path]:
        """Get unit test files for specific modified source files."""
        unit_tests = []

        for source_file in modified_files:
            # Convert source file path to test file path
            # e.g., src/common/logger_setup.py -> tests/unit/common/test_logger_setup.py
            try:
                relative_path = source_file.relative_to(self.project_root)
            except ValueError:
                # If not relative to project root, skip
                continue

            # Remove 'src/' or 'tools/' prefix
            if str(relative_path).startswith("src/"):
                test_path = str(relative_path)[4:]  # Remove 'src/'
            elif str(relative_path).startswith("tools/"):
                test_path = str(relative_path)[6:]  # Remove 'tools/'
            else:
                continue

            # Get the base name without extension
            base_name = Path(test_path).stem  # e.g., "logger_setup" from "logger_setup.py"

            # Look for test files that start with "test_" and contain the base name
            # This handles patterns like:
            # - test_logger_setup.py
            # - test_smart_test_coverage.py
            # - test_smart_test_coverage_enhanced.py

            # Handle the case where the file is directly in src/ or tools/ (no subdirectory)
            test_subdir = Path(test_path).parent
            if str(test_subdir) == ".":
                # File is directly in src/ or tools/, so look in tests/unit/tools/ or tests/unit/src/
                if str(relative_path).startswith("src/"):
                    test_dir = self.project_root / "tests" / "unit" / "src"
                elif str(relative_path).startswith("tools/"):
                    test_dir = self.project_root / "tests" / "unit" / "tools"
                else:
                    test_dir = self.project_root / "tests" / "unit"
            else:
                # File is in a subdirectory, preserve the structure
                test_dir = self.project_root / "tests" / "unit" / test_subdir

            if test_dir.exists():
                for test_file in test_dir.glob("test_*.py"):
                    test_name = test_file.stem  # e.g., "test_logger_setup" or "test_smart_test_coverage_enhanced"

                    # Check if the test file name contains the base name
                    # This handles both exact matches and enhanced versions
                    # e.g., "smart_test_coverage" matches "test_smart_test_coverage" and "test_smart_test_coverage_enhanced"
                    if base_name in test_name:
                        unit_tests.append(test_file)

        return unit_tests

    def _get_files_in_folders(self, modified_folders: set[Path]) -> list[Path]:
        """Get all source files in the modified folders."""
        folder_files = []

        for folder in modified_folders:
            # Find all Python files in the folder and subfolders
            try:
                relative_folder = folder.relative_to(self.project_root)
            except ValueError:
                # If not relative to project root, skip
                continue

            # Only process src/ and tools/ folders
            if (
                str(relative_folder).startswith("src/")
                or str(relative_folder).startswith("tools/")
                or str(relative_folder) == "src"
                or str(relative_folder) == "tools"
            ):
                # Find all Python files in the directory and subdirectories
                for file_path in folder.rglob("*.py"):
                    # Skip __pycache__ and test files
                    if "__pycache__" not in str(file_path) and not file_path.name.startswith("test_"):
                        folder_files.append(file_path)

        return folder_files

    def _get_folder_tests(self, modified_folders: set[Path]) -> list[Path]:
        """Get test files for modified folders (legacy method - now handled by _run_folder_tests)."""
        # This method is now deprecated in favor of running unit tests for all files in folders
        return []

    def _has_source_changes(self) -> bool:
        """Check if any source files have changed since last coverage run.
        Uses git candidates when available; otherwise falls back to full scan of source dirs."""
        if not self.cache.get("last_full_run"):
            return True
        cached_hashes = self.cache.get("file_hashes", {})
        git_changed = self._git_changed_paths()
        if git_changed:
            for rel in git_changed:
                # Limit to source roots
                p = self.project_root / rel
                if not p.exists() or self._should_exclude_file(p):
                    continue
                if not any(str(p).startswith(str(self.project_root / d)) for d in self.source_dirs):
                    continue
                h = self._get_file_hash(p)
                if (
                    h
                    and cached_hashes.get(rel) != h
                    and not self._is_version_only_change(rel, cached_hashes.get(rel, ""), h)
                ):
                    return True
            return False
        # Fallback: compare all source files against cache
        for p in self._get_source_files():
            if self._should_exclude_file(p):
                continue
            rel = str(p.relative_to(self.project_root))
            h = self._get_file_hash(p)
            if (
                h
                and cached_hashes.get(rel) != h
                and not self._is_version_only_change(rel, cached_hashes.get(rel, ""), h)
            ):
                return True
        return False

    def _has_test_changes(self) -> bool:
        """Check if any test files have changed since last coverage run.
        Uses git candidates when available; otherwise falls back to full scan of test dirs."""
        if not self.cache.get("last_full_run"):
            return True
        cached_test_hashes = self.cache.get("test_file_hashes", {})
        git_changed = self._git_changed_paths()
        if git_changed:
            for rel in git_changed:
                p = self.project_root / rel
                if not p.exists() or self._should_exclude_file(p):
                    continue
                if not any(str(p).startswith(str(self.project_root / d)) for d in self.test_dirs):
                    continue
                h = self._get_file_hash(p)
                if h and cached_test_hashes.get(rel) != h:
                    return True
            return False
        # Fallback: compare all test files against cache
        for p in self._get_test_files():
            if self._should_exclude_file(p):
                continue
            rel = str(p.relative_to(self.project_root))
            h = self._get_file_hash(p)
            if h and cached_test_hashes.get(rel) != h:
                return True
        return False

    def _is_version_only_change(self, file_path: str, cached_hash: str, current_hash: str) -> bool:
        """Check if the change is only a version number update."""
        # Only check version files
        version_files = ["pyproject.toml", "setup.py", "src/__init__.py"]
        if not any(file_path.endswith(f) for f in version_files):
            return False

        try:
            current_file = self.project_root / file_path
            if not current_file.exists():
                return False

            with open(current_file, encoding="utf-8") as f:
                current_content = f.read()

            # For pyproject.toml, check if only version line changed
            if file_path.endswith("pyproject.toml"):
                # Look for version = "x.y.z" pattern
                import re

                version_pattern = r'version\s*=\s*["\'](\d+\.\d+\.\d+)["\']'
                version_matches = re.findall(version_pattern, current_content)

                # If we found exactly one version match and it looks like a version number
                if len(version_matches) == 1:
                    version = version_matches[0]
                    # Check if it's a valid semantic version pattern
                    if re.match(r"^\d+\.\d+\.\d+$", version):
                        # Count non-version lines that might have changed
                        lines = current_content.split("\n")
                        non_version_lines = [
                            line
                            for line in lines
                            if "version" not in line.lower() or not re.search(version_pattern, line)
                        ]
                        # If most lines are not version-related, it's likely just a version change
                        if len(non_version_lines) > 10:  # pyproject.toml should have many other lines
                            return True

            # For setup.py, check for version parameter
            elif file_path.endswith("setup.py"):
                import re

                version_pattern = r'version\s*=\s*["\'](\d+\.\d+\.\d+)["\']'
                version_matches = re.findall(version_pattern, current_content)

                if len(version_matches) == 1:
                    version = version_matches[0]
                    if re.match(r"^\d+\.\d+\.\d+$", version):
                        # Count non-version lines
                        lines = current_content.split("\n")
                        non_version_lines = [
                            line
                            for line in lines
                            if "version" not in line.lower() or not re.search(version_pattern, line)
                        ]
                        if len(non_version_lines) > 5:  # setup.py should have other content
                            return True

            # For __init__.py, check for __version__ assignment
            elif file_path.endswith("src/__init__.py"):
                import re

                version_pattern = r'__version__\s*=\s*["\'](\d+\.\d+\.\d+)["\']'
                version_matches = re.findall(version_pattern, current_content)

                if len(version_matches) == 1:
                    version = version_matches[0]
                    if re.match(r"^\d+\.\d+\.\d+$", version):
                        # For __init__.py, if it's mostly just version and docstring, it's likely version-only
                        lines = current_content.split("\n")
                        non_version_lines = [
                            line
                            for line in lines
                            if "version" not in line.lower()
                            and not line.strip().startswith("#")
                            and not line.strip().startswith('"""')
                            and not line.strip().startswith("'''")
                            and line.strip()
                        ]
                        if len(non_version_lines) <= 2:  # Should be minimal content beyond version
                            return True

        except Exception:
            # If we can't read or parse the file, assume it's not version-only
            pass

        return False

    def _has_config_changes(self) -> bool:
        """Check if any configuration files have changed since last coverage run.
        Uses git candidates when available; otherwise falls back to full scan of config files."""
        if not self.cache.get("last_full_run"):
            return True
        cached_config_hashes = self.cache.get("config_file_hashes", {})
        git_changed = self._git_changed_paths()
        if git_changed:
            for rel in git_changed:
                p = self.project_root / rel
                if not p.exists() or self._should_exclude_file(p):
                    continue
                if p.name not in self.config_files:
                    continue
                h = self._get_file_hash(p)
                if h:
                    cached_hash = cached_config_hashes.get(rel)
                    if cached_hash != h and not self._is_version_only_change(rel, cached_hash or "", h):
                        return True
            return False
        # Fallback: compare all config files against cache
        for p in self._get_config_files():
            if self._should_exclude_file(p):
                continue
            rel = str(p.relative_to(self.project_root))
            h = self._get_file_hash(p)
            cached_hash = cached_config_hashes.get(rel, "")
            if h and cached_hash != h and not self._is_version_only_change(rel, cached_hash or "", h):
                return True
        return False

    def _run_coverage_tests(self) -> tuple[bool, int, float]:
        """Run full coverage tests and return (success, test_count, coverage_percentage)."""
        print("🔄 Running full test suite with coverage...")

        # Create logs directory if it doesn't exist
        logs_dir = self.project_root / "logs" / "tests"
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Generate timestamp for log files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_log_file = logs_dir / f"test_run_{timestamp}.log"
        coverage_log_file = logs_dir / f"coverage_{timestamp}.log"

        try:
            # Run tests with coverage - capture both stdout and stderr
            print(f"📝 Test output will be logged to: {test_log_file}")
            print(f"📊 Coverage details will be logged to: {coverage_log_file}")

            with open(test_log_file, "w") as log_file, open(coverage_log_file, "w") as cov_file:
                # Write header to log files
                log_file.write(f"Test Run Started: {datetime.now().isoformat()}\n")
                log_file.write("=" * 80 + "\n")
                cov_file.write(f"Coverage Analysis Started: {datetime.now().isoformat()}\n")
                cov_file.write("=" * 80 + "\n")

                # Run tests with real-time output to both console and log
                # Implement robust fallback: try Hatch first (if enabled), then fall back to pytest

                def run_and_stream(cmd_to_run: list[str]) -> tuple[int | None, list[str], Exception | None]:
                    output_local: list[str] = []
                    try:
                        proc = subprocess.Popen(
                            cmd_to_run,
                            cwd=self.project_root,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            bufsize=1,
                            universal_newlines=True,
                        )
                    except Exception as e:  # FileNotFoundError, OSError, etc.
                        return None, output_local, e

                    assert proc.stdout is not None
                    for line in iter(proc.stdout.readline, ""):
                        if line:
                            print(line.rstrip())
                            log_file.write(line)
                            log_file.flush()
                            output_local.append(line)
                    try:
                        rc = proc.wait(timeout=600)  # 10 minute timeout
                    except subprocess.TimeoutExpired:
                        try:
                            proc.kill()
                        except Exception:
                            pass
                        raise
                    return rc, output_local, None

                output_lines = []
                return_code: int | None = None
                if self.use_hatch:
                    hatch_cmd = self._build_hatch_test_cmd(with_coverage=True, parallel=True)
                    rc, out, err = run_and_stream(hatch_cmd)
                    output_lines.extend(out)
                    # Only fall back to pytest if hatch failed to start or had a critical error
                    # Don't fall back for non-zero exit codes that might be due to coverage threshold failures
                    if err is not None or rc is None:
                        print("⚠️  Hatch test failed to start; falling back to pytest.")
                        log_file.write("Hatch test failed to start; falling back to pytest.\n")
                        pytest_cmd = self._build_pytest_cmd(with_coverage=True, parallel=True)
                        rc2, out2, _ = run_and_stream(pytest_cmd)
                        output_lines.extend(out2)
                        return_code = rc2 if rc2 is not None else 1
                    else:
                        return_code = rc
                else:
                    pytest_cmd = self._build_pytest_cmd(with_coverage=True, parallel=True)
                    rc, out, _ = run_and_stream(pytest_cmd)
                    output_lines.extend(out)
                    return_code = rc if rc is not None else 1

                # Write footer to log files
                log_file.write("\n" + "=" * 80 + "\n")
                log_file.write(f"Test Run Completed: {datetime.now().isoformat()}\n")
                log_file.write(f"Exit Code: {return_code}\n")

                cov_file.write(f"Coverage Analysis Completed: {datetime.now().isoformat()}\n")
                cov_file.write(f"Exit Code: {return_code}\n")

            # Parse coverage percentage from output
            coverage_percentage = 0
            test_count = 0
            success = return_code == 0

            # Extract coverage from output
            for line in output_lines:
                if "TOTAL" in line and "%" in line:
                    # Extract percentage
                    parts = line.split()
                    for part in parts:
                        if part.endswith("%"):
                            try:
                                coverage_percentage = float(part[:-1])
                                break
                            except ValueError:
                                pass

                # Count tests (look for "passed" or "failed")
                if " passed" in line or " failed" in line:
                    try:
                        # Look for the summary line format: "======== 2779 passed, 2 skipped, 8 subtests passed in 120.46s ========"
                        if line.startswith("========") and (" passed" in line or " failed" in line):
                            # Extract the first number before "passed" or "failed" (not "subtests passed")
                            words = line.split()
                            for i, word in enumerate(words):
                                if (
                                    (word == "passed" or word == "passed," or word == "failed" or word == "failed,")
                                    and i > 0
                                    and words[i - 1] != "subtests"
                                ):
                                    test_count = int(words[i - 1])
                                    break
                        # Fallback for other formats
                        elif (" passed" in line or " failed" in line) and "subtests passed" not in line:
                            words = line.split()
                            for i, word in enumerate(words):
                                if (word == "passed" or word == "failed") and i > 0:
                                    test_count = int(words[i - 1])
                                    break
                    except (ValueError, IndexError):
                        pass

            # Full tests - coverage threshold is enforced
            if success:
                print(f"✅ Tests completed: {test_count} tests, {coverage_percentage:.1f}% coverage")
                print(f"📝 Full test log: {test_log_file}")
                print(f"📊 Coverage log: {coverage_log_file}")
            else:
                print(f"❌ Tests failed with exit code {return_code}")
                print(f"📝 Check test log for details: {test_log_file}")
                print(f"📊 Check coverage log for details: {coverage_log_file}")

            return success, test_count, coverage_percentage

        except subprocess.TimeoutExpired:
            print("❌ Test run timed out after 10 minutes")
            return False, 0, 0
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return False, 0, 0

    def _run_tests(self, test_files: list[Path], test_level: str) -> tuple[bool, int, float]:
        """Run tests for specific files and return (success, test_count, coverage_percentage)."""
        if not test_files:
            print(f"ℹ️  No {test_level} tests found to run")
            return True, 0, 100.0

        print(f"🔄 Running {test_level} tests for {len(test_files)} files...")

        # Create logs directory if it doesn't exist
        logs_dir = self.project_root / "logs" / "tests"
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Generate timestamp for log files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_log_file = logs_dir / f"{test_level}_test_run_{timestamp}.log"
        coverage_log_file = logs_dir / f"{test_level}_coverage_{timestamp}.log"

        try:
            # Convert Path objects to strings for pytest
            test_file_strings = [str(f) for f in test_files]

            print(f"📝 {test_level.title()} test output will be logged to: {test_log_file}")
            print(f"📊 {test_level.title()} coverage details will be logged to: {coverage_log_file}")

            with open(test_log_file, "w") as log_file, open(coverage_log_file, "w") as cov_file:
                # Write header to log files
                log_file.write(f"{test_level.title()} Test Run Started: {datetime.now().isoformat()}\n")
                log_file.write("=" * 80 + "\n")
                cov_file.write(f"{test_level.title()} Coverage Analysis Started: {datetime.now().isoformat()}\n")
                cov_file.write("=" * 80 + "\n")

                # Run tests with real-time output to both console and log
                # Implement robust fallback: try Hatch first (if enabled), then fall back to pytest

                def run_and_stream(cmd_to_run: list[str]) -> tuple[int | None, list[str], Exception | None]:
                    output_local: list[str] = []
                    try:
                        proc = subprocess.Popen(
                            cmd_to_run,
                            cwd=self.project_root,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            bufsize=1,
                            universal_newlines=True,
                        )
                    except Exception as e:  # FileNotFoundError, OSError, etc.
                        return None, output_local, e

                    assert proc.stdout is not None
                    for line in iter(proc.stdout.readline, ""):
                        if line:
                            print(line.rstrip())
                            log_file.write(line)
                            log_file.flush()
                            output_local.append(line)
                    try:
                        rc = proc.wait(timeout=600)  # 10 minute timeout
                    except subprocess.TimeoutExpired:
                        try:
                            proc.kill()
                        except Exception:
                            pass
                        raise
                    return rc, output_local, None

                output_lines = []
                return_code: int | None = None
                # Option A: Only collect coverage for classic unit/folder tests.
                # Contract layers (integration/e2e/scenarios) should NOT collect line coverage.
                want_coverage = test_level in ["unit", "folder"]
                if self.use_hatch:
                    hatch_cmd = self._build_hatch_test_cmd(with_coverage=want_coverage, extra_args=test_file_strings)
                    rc, out, err = run_and_stream(hatch_cmd)
                    output_lines.extend(out)
                    # Only fall back to pytest if hatch failed to start or had a critical error
                    # Don't fall back for non-zero exit codes that might be due to coverage threshold failures
                    if err is not None or rc is None:
                        print("⚠️  Hatch test failed to start; falling back to pytest.")
                        log_file.write("Hatch test failed to start; falling back to pytest.\n")
                        pytest_cmd = self._build_pytest_cmd(with_coverage=want_coverage, extra_args=test_file_strings)
                        rc2, out2, _ = run_and_stream(pytest_cmd)
                        output_lines.extend(out2)
                        return_code = rc2 if rc2 is not None else 1
                    else:
                        return_code = rc
                else:
                    pytest_cmd = self._build_pytest_cmd(with_coverage=want_coverage, extra_args=test_file_strings)
                    rc, out, _ = run_and_stream(pytest_cmd)
                    output_lines.extend(out)
                    return_code = rc if rc is not None else 1

                # Write footer to log files
                log_file.write("\n" + "=" * 80 + "\n")
                log_file.write(f"{test_level.title()} Test Run Completed: {datetime.now().isoformat()}\n")
                log_file.write(f"Exit Code: {return_code}\n")

                cov_file.write(f"{test_level.title()} Coverage Analysis Completed: {datetime.now().isoformat()}\n")
                cov_file.write(f"Exit Code: {return_code}\n")

            # Parse coverage percentage from output
            coverage_percentage = 0
            tested_coverage_percentage = 0
            test_count = 0
            success = return_code == 0

            # For integration/E2E tests, set coverage to 100% since we don't measure it
            if test_level in ["integration", "e2e"]:
                coverage_percentage = 100.0
                tested_coverage_percentage = 100.0
            else:
                # Extract coverage from output for unit/folder/full tests
                for line in output_lines:
                    if "TOTAL" in line and "%" in line:
                        # Extract percentage
                        parts = line.split()
                        for part in parts:
                            if part.endswith("%"):
                                try:
                                    coverage_percentage = float(part[:-1])
                                    break
                                except ValueError:
                                    pass

            # Count tests (look for "passed" or "failed") - works for all test levels
            for line in output_lines:
                if " passed" in line or " failed" in line:
                    try:
                        # Look for the summary line format: "======== 2779 passed, 2 skipped, 8 subtests passed in 120.46s ========"
                        if line.startswith("========") and (" passed" in line or " failed" in line):
                            # Extract the first number before "passed" or "failed" (not "subtests passed")
                            words = line.split()
                            for i, word in enumerate(words):
                                if (
                                    (word == "passed" or word == "passed," or word == "failed" or word == "failed,")
                                    and i > 0
                                    and words[i - 1] != "subtests"
                                ):
                                    test_count = int(words[i - 1])
                                    break
                        # Fallback for other formats
                        elif (" passed" in line or " failed" in line) and "subtests passed" not in line:
                            words = line.split()
                            for i, word in enumerate(words):
                                if (word == "passed" or word == "failed") and i > 0:
                                    test_count = int(words[i - 1])
                                    break
                    except (ValueError, IndexError):
                        pass

            # Calculate tested code coverage for unit/folder tests
            if test_level in ["unit", "folder"] and test_files:
                tested_coverage_percentage = self._calculate_tested_coverage(test_files, output_lines)
            else:
                tested_coverage_percentage = coverage_percentage

            # For unit/folder tests, check if failure is due to coverage threshold
            if not success and test_level in ["unit", "folder"]:
                # Check if tests actually passed but failed due to coverage threshold
                if test_count > 0 and coverage_percentage > 0:
                    # Check if the failure is due to coverage threshold
                    coverage_threshold_failure = False
                    for line in output_lines:
                        if (
                            "coverage failure" in line.lower()
                            or "fail_under" in line.lower()
                            or "less than fail-under" in line.lower()
                            or ("total of" in line and "is less than fail-under" in line)
                        ):
                            coverage_threshold_failure = True
                            break

                    if coverage_threshold_failure:
                        # This is a coverage threshold failure, not a test failure
                        success = True  # Treat as success for unit/folder tests
                        print(
                            f"⚠️  Warning: Overall coverage {coverage_percentage:.1f}% is below threshold of {self.coverage_threshold:.1f}%"
                        )
                        print("💡 This is expected for unit/folder tests. Full test run will enforce the threshold.")

            # For unit/folder tests, also check tested code coverage against threshold
            if test_level in ["unit", "folder"] and tested_coverage_percentage > 0:
                if tested_coverage_percentage < self.coverage_threshold:
                    print(
                        f"⚠️  Warning: Tested code coverage {tested_coverage_percentage:.1f}% is below threshold of {self.coverage_threshold:.1f}%"
                    )
                    print("💡 Consider adding more tests for the modified files.")
                else:
                    print(
                        f"✅ Tested code coverage {tested_coverage_percentage:.1f}% meets threshold of {self.coverage_threshold:.1f}%"
                    )

            if success:
                if test_level in ["unit", "folder"] and tested_coverage_percentage > 0:
                    print(
                        f"✅ {test_level.title()} tests completed: {test_count} tests, {coverage_percentage:.1f}% overall, {tested_coverage_percentage:.1f}% tested code coverage"
                    )
                else:
                    print(
                        f"✅ {test_level.title()} tests completed: {test_count} tests, {coverage_percentage:.1f}% coverage"
                    )
                print(f"📝 Full {test_level} test log: {test_log_file}")
                print(f"📊 {test_level.title()} coverage log: {coverage_log_file}")
            else:
                print(f"❌ {test_level.title()} tests failed with exit code {return_code}")
                print(f"📝 Check {test_level} test log for details: {test_log_file}")
                print(f"📊 Check {test_level} coverage log for details: {coverage_log_file}")

            # Cleanup generated test files after test run
            self._cleanup_generated_test_files()

            return success, test_count, coverage_percentage

        except subprocess.TimeoutExpired:
            print(f"❌ {test_level.title()} test run timed out after 10 minutes")
            # Cleanup even on timeout
            self._cleanup_generated_test_files()
            return False, 0, 0
        except Exception as e:
            print(f"❌ Error running {test_level} tests: {e}")
            # Cleanup even on error
            self._cleanup_generated_test_files()
            return False, 0, 0

    def _cleanup_generated_test_files(self) -> None:
        """Clean up generated test_*_contract.py files from project root."""
        try:
            # Find all test_*_contract.py files in project root
            test_files = list(self.project_root.glob("test_*_contract.py"))

            if test_files:
                print(f"🧹 Cleaning up {len(test_files)} generated test files...")
                for test_file in test_files:
                    try:
                        test_file.unlink()
                        print(f"   Removed: {test_file.name}")
                    except OSError as e:
                        print(f"   Warning: Could not remove {test_file.name}: {e}")
                print("✅ Cleanup completed")
            else:
                print("ℹ️  No generated test files to clean up")

        except Exception as e:
            print(f"⚠️  Warning: Error during cleanup: {e}")

    def _calculate_tested_coverage(self, test_files: list[Path], output_lines: list[str]) -> float:
        """Calculate coverage percentage for only the tested files."""
        if not test_files:
            return 0.0

        # Get the source files that were actually tested
        tested_source_files = set()
        for test_file in test_files:
            # Convert test file path to source file path
            # e.g., tests/unit/tools/test_smart_test_coverage.py -> tools/smart_test_coverage.py
            if test_file.name.startswith("test_"):
                source_name = test_file.name[5:]  # Remove 'test_' prefix
                # For tools directory tests
                if "tools" in str(test_file):
                    source_file = self.project_root / "tools" / source_name
                # For src directory tests (tests/unit/module/test_file.py -> src/module/file.py)
                elif "tests" in str(test_file) and "unit" in str(test_file):
                    # Extract the module path from test file
                    # e.g., tests/unit/common/test_logger_setup.py -> src/common/logger_setup.py
                    test_parts = test_file.parts
                    # Find the index of 'unit' and get the next part as module_path
                    try:
                        unit_index = test_parts.index("unit")
                        if unit_index + 1 < len(test_parts):
                            module_path = test_parts[unit_index + 1]  # 'common'
                            source_file = self.project_root / "src" / module_path / source_name
                        else:
                            continue
                    except ValueError:
                        continue
                else:
                    continue

                if source_file.exists():
                    tested_source_files.add(str(source_file.relative_to(self.project_root)))

        if not tested_source_files:
            return 0.0

        # Parse coverage data from output lines
        total_statements = 0
        total_missed = 0
        total_branches = 0
        total_branch_parts = 0

        in_coverage_table = False
        for line in output_lines:
            # Look for the coverage table header
            if "Name" in line and "Stmts" in line and "Miss" in line and "Cover" in line:
                in_coverage_table = True
                continue

            # Skip the separator line
            if in_coverage_table and line.startswith("---"):
                continue

            # Look for the TOTAL line to stop parsing
            if in_coverage_table and "TOTAL" in line:
                break

            # Parse coverage data for each file
            if in_coverage_table and line.strip():
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        file_name = parts[0]
                        # Check if this file is one of our tested files
                        if any(tested_file in file_name for tested_file in tested_source_files):
                            statements = int(parts[1])
                            missed = int(parts[2])
                            branches = int(parts[3]) if len(parts) > 3 else 0
                            branch_parts = int(parts[4]) if len(parts) > 4 else 0

                            total_statements += statements
                            total_missed += missed
                            total_branches += branches
                            total_branch_parts += branch_parts
                    except (ValueError, IndexError):
                        continue

        # Calculate coverage percentage
        if total_statements > 0:
            covered_statements = total_statements - total_missed
            coverage_percentage = (covered_statements / total_statements) * 100
            return round(coverage_percentage, 1)

        return 0.0

    def _check_coverage_threshold(self, coverage_percentage: float):
        """Check if coverage meets the required threshold."""
        if coverage_percentage < self.coverage_threshold:
            raise CoverageThresholdError(
                f"Coverage {coverage_percentage:.1f}% is below required threshold of {self.coverage_threshold:.1f}%\n"
                f"Please add more tests or improve existing test coverage to reach at least {self.coverage_threshold:.1f}%"
            )

    def _update_cache(
        self,
        success: bool,
        test_count: int,
        coverage_percentage: float,
        enforce_threshold: bool = True,
        update_only: bool = False,
        updated_sources: list[Path] | None = None,
        updated_tests: list[Path] | None = None,
        updated_configs: list[Path] | None = None,
    ) -> None:
        """Update cache and hashes.
        If update_only is True, only update hashes for provided file lists (when their tests passed).
        Otherwise, refresh all known hashes.
        """
        # Only enforce coverage threshold for full test runs and when tests succeeded
        if success and enforce_threshold:
            self._check_coverage_threshold(coverage_percentage)
        elif success and not enforce_threshold and coverage_percentage < self.coverage_threshold:
            print(
                f"⚠️  Warning: Coverage {coverage_percentage:.1f}% is below threshold of {self.coverage_threshold:.1f}%"
            )
            print("💡 This is expected for unit/folder tests. Full test run will enforce the threshold.")

        # Prepare existing maps
        file_hashes: dict[str, str] = dict(self.cache.get("file_hashes", {}))
        test_file_hashes: dict[str, str] = dict(self.cache.get("test_file_hashes", {}))
        config_file_hashes: dict[str, str] = dict(self.cache.get("config_file_hashes", {}))

        def update_map(paths: list[Path] | None, target: dict[str, str]):
            if not paths:
                return
            for p in paths:
                h = self._get_file_hash(p)
                if h:
                    rel = str(p.relative_to(self.project_root))
                    target[rel] = h

        if update_only:
            update_map(updated_sources, file_hashes)
            update_map(updated_tests, test_file_hashes)
            update_map(updated_configs, config_file_hashes)
        else:
            # Refresh entire tree
            for file_path in self._get_source_files():
                h = self._get_file_hash(file_path)
                if h:
                    file_hashes[str(file_path.relative_to(self.project_root))] = h
            for file_path in self._get_test_files():
                h = self._get_file_hash(file_path)
                if h:
                    test_file_hashes[str(file_path.relative_to(self.project_root))] = h
            for file_path in self._get_config_files():
                h = self._get_file_hash(file_path)
                if h:
                    config_file_hashes[str(file_path.relative_to(self.project_root))] = h

        # Update cache; keep last_full_run as the last index time (not necessarily a full suite)
        self.cache.update(
            {
                "last_full_run": datetime.now().isoformat(),
                "coverage_percentage": coverage_percentage if success else self.cache.get("coverage_percentage", 0),
                "file_hashes": file_hashes,
                "test_file_hashes": test_file_hashes,
                "config_file_hashes": config_file_hashes,
                "test_count": test_count if success else self.cache.get("test_count", 0),
                "success": success,
            }
        )

        self._save_cache()

    def check_if_full_test_needed(self) -> bool:
        """Check if a full test run is needed.
        For local smart-test runs we NEVER require a full run; CI will run the full suite."""
        source_changed = self._has_source_changes()
        test_changed = self._has_test_changes()
        config_changed = self._has_config_changes()

        if config_changed:
            print("🔄 Configuration or infra changes detected - will run changed-only tests (no full run)")
            return False

        if source_changed or test_changed:
            reasons = []
            if source_changed:
                reasons.append("source files")
            if test_changed:
                reasons.append("test files")
            print(f"🔄 {'/'.join(reasons)} have changed - running changed-only tests")
            return False

        print("✅ No relevant changes detected - using cached coverage data")
        return False

    def get_status(self) -> dict:
        """Get current coverage status."""
        return {
            "last_run": self.cache.get("last_full_run"),
            "coverage_percentage": self.cache.get("coverage_percentage", 0),
            "test_count": self.cache.get("test_count", 0),
            "source_changed": self._has_source_changes(),
            "test_changed": self._has_test_changes(),
            "config_changed": self._has_config_changes(),
            "needs_full_run": self.check_if_full_test_needed(),
        }

    def get_recent_logs(self, count: int = 5) -> list[Path]:
        """Get recent test log files."""
        logs_dir = self.project_root / "logs" / "tests"
        if not logs_dir.exists():
            return []

        # Get all test log files and sort by modification time
        log_files = list(logs_dir.glob("test_run_*.log"))
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return log_files[:count]

    def show_recent_logs(self, count: int = 3):
        """Show recent test log files and their status."""
        recent_logs = self.get_recent_logs(count)

        if not recent_logs:
            print("📝 No test logs found")
            return

        print(f"📝 Recent test logs (last {len(recent_logs)}):")
        for i, log_file in enumerate(recent_logs, 1):
            # Get file modification time
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)

            # Try to determine success/failure from log content
            status = "❓ Unknown"
            try:
                with open(log_file) as f:
                    content = f.read()
                    if "Exit Code: 0" in content:
                        status = "✅ Passed"
                    elif "Exit Code:" in content:
                        status = "❌ Failed"
            except Exception:
                pass

            print(f"   {i}. {log_file.name} - {mtime.strftime('%Y-%m-%d %H:%M:%S')} - {status}")

    def show_latest_log(self):
        """Show the latest test log content."""
        recent_logs = self.get_recent_logs(1)

        if not recent_logs:
            print("📝 No test logs found")
            return

        latest_log = recent_logs[0]
        print(f"📝 Latest test log: {latest_log.name}")
        print("=" * 80)

        try:
            file_mode = latest_log.stat().st_mode
            if file_mode & 0o444 == 0:
                raise PermissionError("Log file is not readable due to permissions")
            with open(latest_log) as f:
                content = f.read()
                # Show last 50 lines to avoid overwhelming output
                lines = content.split("\n")
                if len(lines) > 50:
                    print("... (showing last 50 lines)")
                    lines = lines[-50:]
                print("\n".join(lines))
        except Exception as e:
            print(f"❌ Error reading log file: {e}")

    def run_smart_tests(self, test_level: str = "auto", force: bool = False) -> bool:
        """Run tests with smart change detection and specified level."""
        if test_level == "auto":
            # Compute changed sources and tests
            source_changed = self._has_source_changes()
            test_changed = self._has_test_changes()
            config_changed = self._has_config_changes()

            if source_changed or test_changed or config_changed or force:
                return self._run_changed_only()
            # No changes - use cached data
            status = self.get_status()
            print(
                f"📊 Using cached results: {status['test_count']} tests, {status['coverage_percentage']:.1f}% coverage"
            )
            return status.get("success", False)
        if force:
            # Force mode - run the specified level regardless of changes
            return self.run_tests_by_level(test_level)
        return self.run_tests_by_level(test_level)

    def run_tests_by_level(self, test_level: str) -> bool:
        """Run tests by specified level: unit, folder, integration, e2e, or full."""
        if test_level == "unit":
            return self._run_unit_tests()
        if test_level == "folder":
            return self._run_folder_tests()
        if test_level == "integration":
            return self._run_integration_tests()
        if test_level == "e2e":
            return self._run_e2e_tests()
        if test_level == "full":
            return self._run_full_tests()
        print(f"❌ Unknown test level: {test_level}")
        return False

    def _run_unit_tests(self) -> bool:
        """Run unit tests for modified files only."""
        modified_files = self._get_modified_files()
        if not modified_files:
            print("ℹ️  No modified files detected - no unit tests to run")
            return True

        print(f"🔍 Found {len(modified_files)} modified files:")
        for file_path in modified_files:
            try:
                relative_path = file_path.relative_to(self.project_root)
                print(f"   - {relative_path}")
            except ValueError:
                print(f"   - {file_path}")

        unit_tests = self._get_unit_tests_for_files(modified_files)
        if not unit_tests:
            print("⚠️  No unit tests found for modified files")
            print("💡 Consider adding unit tests for:")
            for file_path in modified_files:
                try:
                    relative_path = file_path.relative_to(self.project_root)
                    print(f"   - {relative_path}")
                except ValueError:
                    print(f"   - {file_path}")
            return True

        print(f"🧪 Running unit tests for {len(unit_tests)} test files...")
        success, test_count, coverage_percentage = self._run_tests(unit_tests, "unit")

        # Update cache hashes only for files covered by successful unit batch
        if success:
            self._update_cache(
                True,
                test_count,
                coverage_percentage,
                enforce_threshold=False,
                update_only=True,
                updated_sources=modified_files,
                updated_tests=unit_tests,
            )
            print(f"✅ Unit tests completed: {test_count} tests, {coverage_percentage:.1f}% coverage")
        else:
            print("❌ Unit tests failed")

        return success

    def _run_folder_tests(self) -> bool:
        """Run unit tests for all files in modified folders."""
        modified_folders = self._get_modified_folders()
        if not modified_folders:
            print("ℹ️  No modified folders detected - no folder tests to run")
            return True

        print(f"📁 Found {len(modified_folders)} modified folders:")
        for folder in modified_folders:
            try:
                relative_path = folder.relative_to(self.project_root)
                print(f"   - {relative_path}")
            except ValueError:
                print(f"   - {folder}")

        # Get all source files in the modified folders
        folder_files = self._get_files_in_folders(modified_folders)
        if not folder_files:
            print("ℹ️  No source files found in modified folders")
            return True

        print(f"🔍 Found {len(folder_files)} source files in modified folders:")
        for file_path in folder_files:
            try:
                relative_path = file_path.relative_to(self.project_root)
                print(f"   - {relative_path}")
            except ValueError:
                print(f"   - {file_path}")

        # Get unit tests for all files in the modified folders
        folder_tests = self._get_unit_tests_for_files(folder_files)
        if not folder_tests:
            print("⚠️  No unit tests found for files in modified folders")
            print("💡 Consider adding unit tests for:")
            for file_path in folder_files:
                try:
                    relative_path = file_path.relative_to(self.project_root)
                    print(f"   - {relative_path}")
                except ValueError:
                    print(f"   - {file_path}")
            return True

        print(f"🧪 Running unit tests for {len(folder_tests)} test files in modified folders...")
        success, test_count, coverage_percentage = self._run_tests(folder_tests, "folder")

        # Update cache only for files in modified folders when tests passed
        if success:
            self._update_cache(
                True,
                test_count,
                coverage_percentage,
                enforce_threshold=False,
                update_only=True,
                updated_sources=folder_files,
                updated_tests=folder_tests,
            )
            print(f"✅ Folder tests completed: {test_count} tests, {coverage_percentage:.1f}% coverage")
        else:
            print("❌ Folder tests failed")

        return success

    def _run_integration_tests(self) -> bool:
        """Run all integration tests."""
        integration_tests = self._get_test_files_by_level("integration")
        if not integration_tests:
            print("ℹ️  No integration tests found")
            return True

        print(f"🔗 Found {len(integration_tests)} integration test files:")
        for test_file in integration_tests:
            try:
                relative_path = test_file.relative_to(self.project_root)
                print(f"   - {relative_path}")
            except ValueError:
                print(f"   - {test_file}")

        print("🧪 Running integration tests...")
        success, test_count, coverage_percentage = self._run_tests(integration_tests, "integration")

        # Update cache for integration tests (test file hashes only)
        if success:
            self._update_cache(
                True,
                test_count,
                coverage_percentage,
                enforce_threshold=False,
                update_only=True,
                updated_tests=integration_tests,
            )
            print(f"✅ Integration tests completed: {test_count} tests, {coverage_percentage:.1f}% coverage")
            print("ℹ️  Note: Integration test coverage is not enforced - focus is on component interaction validation")
        else:
            print("❌ Integration tests failed")

        return success

    def _run_e2e_tests(self) -> bool:
        """Run end-to-end tests only."""
        e2e_tests = self._get_test_files_by_level("e2e")
        if not e2e_tests:
            print("ℹ️  No e2e tests found")
            return True

        print(f"🌐 Found {len(e2e_tests)} e2e test files:")
        for test_file in e2e_tests:
            try:
                relative_path = test_file.relative_to(self.project_root)
                print(f"   - {relative_path}")
            except ValueError:
                print(f"   - {test_file}")

        print("🧪 Running e2e tests...")
        success, test_count, coverage_percentage = self._run_tests(e2e_tests, "e2e")

        # Update cache for e2e tests (test file hashes only)
        if success:
            self._update_cache(
                True,
                test_count,
                coverage_percentage,
                enforce_threshold=False,
                update_only=True,
                updated_tests=e2e_tests,
            )
            print(f"✅ E2E tests completed: {test_count} tests, {coverage_percentage:.1f}% coverage")
            print("ℹ️  Note: E2E test coverage is not enforced - focus is on full workflow validation")
        else:
            print("❌ E2E tests failed")

        return success

    def _run_full_tests(self) -> bool:
        """Run full test suite."""
        success, test_count, coverage_percentage = self._run_coverage_tests()
        # Only refresh hashes if the full suite succeeded; otherwise keep prior baseline.
        if success:
            # Do not fail on low line coverage locally; contract-first layers are primary gates.
            self._update_cache(True, test_count, coverage_percentage, enforce_threshold=False)
        return success

    def _run_changed_only(self) -> bool:
        """Run only tests impacted by changes since last cached hashes.
        - Unit: tests mapped from modified source files + directly modified unit tests
        - Integration/E2E: only directly modified tests
        No full-suite fallback here; CI should catch broader regressions."""
        # Collect modified items
        modified_sources = self._get_modified_files()
        modified_tests = self._get_modified_test_files()

        # Map modified sources to unit tests
        unit_from_sources = self._get_unit_tests_for_files(modified_sources)
        # Split modified tests by level
        unit_direct, integ_direct, e2e_direct = self._split_tests_by_level(modified_tests)

        # Merge and deduplicate
        def dedupe(paths: list[Path]) -> list[Path]:
            seen: set[str] = set()
            out: list[Path] = []
            for p in paths:
                key = str(p.resolve())
                if key not in seen:
                    seen.add(key)
                    out.append(p)
            return out

        unit_tests = dedupe(unit_from_sources + unit_direct)
        integ_tests = dedupe(integ_direct)
        e2e_tests = dedupe(e2e_direct)

        ran_any = False
        overall_success = True

        if unit_tests:
            ran_any = True
            ok, unit_count, unit_cov = self._run_tests(unit_tests, "unit")
            if ok:
                # Update hashes only for modified sources we mapped and the unit test files themselves
                self._update_cache(
                    True,
                    unit_count,
                    unit_cov,
                    enforce_threshold=False,
                    update_only=True,
                    updated_sources=modified_sources,
                    updated_tests=unit_tests,
                )
            overall_success = overall_success and ok
        if integ_tests:
            ran_any = True
            ok, integ_count, integ_cov = self._run_tests(integ_tests, "integration")
            if ok:
                self._update_cache(
                    True, integ_count, integ_cov, enforce_threshold=False, update_only=True, updated_tests=integ_tests
                )
            overall_success = overall_success and ok
        if e2e_tests:
            ran_any = True
            ok, e2e_count, e2e_cov = self._run_tests(e2e_tests, "e2e")
            if ok:
                self._update_cache(
                    True, e2e_count, e2e_cov, enforce_threshold=False, update_only=True, updated_tests=e2e_tests
                )
            overall_success = overall_success and ok

        if not ran_any:
            print("ℹ️  No changed files detected that map to tests - skipping test execution")
            # Still keep cache timestamp to allow future git comparisons
            self._update_cache(True, 0, self.cache.get("coverage_percentage", 0.0), enforce_threshold=False)
            return True

        return overall_success

    def force_full_run(self, test_level: str = "full") -> bool:
        """Force a test run regardless of file changes."""
        print(f"🔄 Forcing {test_level} test run...")
        if test_level == "full":
            success, test_count, coverage_percentage = self._run_coverage_tests()
            self._update_cache(success, test_count, coverage_percentage, enforce_threshold=True)
        else:
            success = self.run_tests_by_level(test_level)
        return success

    def _git_changed_paths(self) -> set[str]:
        """Return a set of repository-relative paths changed (staged or unstaged).
        Falls back to empty set if git is unavailable.
        Results are cached per SmartCoverageManager instance per run.
        """
        if self._git_changed_cache is not None:
            return set(self._git_changed_cache)
        changed: set[str] = set()
        try:
            # Use porcelain to get staged/unstaged changes (renames show as R100 old -> new; take new path)
            cmd = ["git", "--no-pager", "status", "--porcelain"]
            out = subprocess.check_output(cmd, cwd=self.project_root, text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                if not line.strip():
                    continue
                # Format: XY <path> or R? <old> -> <new>
                payload = line[3:].strip()
                if " -> " in payload:
                    path = payload.split(" -> ", 1)[1]
                else:
                    path = payload
                # Normalize and keep repo-relative
                rel = str(Path(path))
                changed.add(rel)
        except Exception:
            # If git not available, return empty set to avoid over-triggering
            pass
        self._git_changed_cache = set(changed)
        return set(changed)


def main():
    parser = argparse.ArgumentParser(description="Smart Test Coverage Management System")
    parser.add_argument(
        "command",
        choices=["check", "run", "force", "status", "threshold", "logs", "latest", "index"],
        help="Command to execute",
    )
    parser.add_argument(
        "--level",
        choices=["unit", "folder", "integration", "e2e", "full", "auto"],
        default="auto",
        help="Test level for 'run' command (default: auto)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force test run regardless of file changes",
    )

    args = parser.parse_args()

    manager = SmartCoverageManager()

    try:
        if args.command == "check":
            needs_full_run = manager.check_if_full_test_needed()
            sys.exit(0 if not needs_full_run else 1)

        elif args.command == "run":
            success = manager.run_smart_tests(args.level, args.force)
            sys.exit(0 if success else 1)

        elif args.command == "force":
            success = manager.run_smart_tests(args.level, force=True)
            sys.exit(0 if success else 1)

        elif args.command == "status":
            status = manager.get_status()
            print("📊 Coverage Status:")
            print(f"   Last Run: {status['last_run'] or 'Never'}")
            print(f"   Coverage: {status['coverage_percentage']:.1f}%")
            print(f"   Test Count: {status['test_count']}")
            print(f"   Source Changed: {status['source_changed']}")
            print(f"   Test Changed: {status['test_changed']}")
            print(f"   Config Changed: {status['config_changed']}")
            print(f"   Needs Full Run: {status['needs_full_run']}")
            print(f"   Threshold: {manager.coverage_threshold:.1f}%")

            # Check if current coverage meets threshold
            current_coverage = status["coverage_percentage"]
            if current_coverage < manager.coverage_threshold:
                print("   ⚠️  Coverage below threshold!")
            else:
                print("   ✅ Coverage meets threshold")

            print()
            manager.show_recent_logs(3)
            sys.exit(0)

        elif args.command == "threshold":
            """Check if current coverage meets threshold without running tests."""
            status = manager.get_status()
            current_coverage = status["coverage_percentage"]

            print("📊 Coverage Threshold Check:")
            print(f"   Current Coverage: {current_coverage:.1f}%")
            print(f"   Required Threshold: {manager.coverage_threshold:.1f}%")

            if current_coverage < manager.coverage_threshold:
                print("   ❌ Coverage below threshold!")
                print(f"   Difference: {manager.coverage_threshold - current_coverage:.1f}% needed")
                sys.exit(1)
            else:
                print("   ✅ Coverage meets threshold!")
                print(f"   Margin: {current_coverage - manager.coverage_threshold:.1f}% above threshold")
                sys.exit(0)

        elif args.command == "logs":
            # For logs command, we need to handle additional arguments manually
            # since argparse doesn't handle positional arguments after subcommands well
            count = 5
            if len(sys.argv) > 2:
                try:
                    count = int(sys.argv[2])
                except ValueError:
                    print("Error: logs count must be a number")
                    sys.exit(1)
            manager.show_recent_logs(count)
            sys.exit(0)

        elif args.command == "latest":
            manager.show_latest_log()
            sys.exit(0)

        elif args.command == "index":
            # Refresh baseline hashes without executing tests
            print("📦 Indexing current project hashes as baseline (no tests run)...")
            cur_cov = manager.cache.get("coverage_percentage", 0.0)
            cur_cnt = manager.cache.get("test_count", 0)
            manager._update_cache(True, cur_cnt, cur_cov, enforce_threshold=False, update_only=False)
            print("✅ Baseline updated. Future smart runs will consider only new changes.")
            sys.exit(0)

        else:
            print(f"Unknown command: {args.command}")
            print("Use 'python tools/smart_test_coverage.py' without arguments to see usage")
            sys.exit(1)

    except CoverageThresholdError as e:
        print("❌ Coverage threshold not met!")
        print(f"{e}")
        print("\n💡 To fix this issue:")
        print("   1. Add more unit tests to increase coverage")
        print("   2. Improve existing test coverage")
        print("   3. Check for untested code paths")
        print("   4. Run 'hatch run smart-test-status' to see detailed coverage")
        sys.exit(1)


if __name__ == "__main__":
    main()
