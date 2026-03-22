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
import contextlib
import hashlib
import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO, cast

from icontract import ensure, require


logger = logging.getLogger(__name__)


# TOML parsing - prefer tomlkit (style-preserving, widely used), fallback to tomllib (Python 3.11+)
try:
    import tomlkit  # type: ignore[import]

    TOML_LIBRARY = "tomlkit"
except ImportError:
    try:
        import tomllib  # type: ignore[import]

        TOML_LIBRARY = "tomllib"
    except ImportError as err:
        raise ImportError("No TOML parser available. Please install tomlkit (recommended) or use Python 3.11+") from err


class CoverageThresholdError(Exception):
    """Raised when coverage falls below the required threshold."""


class SmartCoverageManager:
    _HATCH_ENV_BROKEN_MARKERS = (
        "Failed to inspect Python interpreter",
        "Broken symlink",
        "underlying Python interpreter removed",
    )

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
            "e2e": "tests/e2e",  # E2E tests live under tests/e2e
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
        self.cache: dict[str, Any] = self._load_cache()

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
        """Construct the hatch run command for the test script, honoring optional env selection.

        Uses `hatch run -e ENV run-cov` (or `run`) so that pytest receives only script
        args after `--`. Using `hatch test -e ENV --cover` can forward `-e` to pytest in
        some environments and cause "unrecognized arguments: -e".
        """
        if self.hatch_test_env and self.hatch_test_env.startswith("hatch-test."):
            env_name = self.hatch_test_env
        elif self.hatch_test_env:
            env_name = f"hatch-test.{self.hatch_test_env}"
        else:
            env_name = "hatch-test.py3.12"
        script = "run-cov" if with_coverage else "run"
        # -e/--env must be the first option before the run command
        base_cmd: list[str] = [self.hatch_bin, "-e", env_name, "run", script]
        # Pass pytest args explicitly after `--` to avoid collisions with hatch flags.
        base_cmd += ["--", "-v", "-r", "fEw"]
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
        # Pytest short summary report: failures/errors/warnings only (no passed tests).
        base_cmd += ["-r", "fEw"]
        # Parallel execution is handled by hatch configuration (parallel = true)
        # No need to add -n parameter manually
        if extra_args:
            base_cmd += extra_args
        return base_cmd

    def _get_test_timeout_seconds(self, test_level: str) -> int:
        """Resolve subprocess timeout for test execution."""
        default_timeout = 600
        slow_levels = {"integration", "scenarios", "e2e", "full"}
        if test_level in slow_levels:
            default_timeout = 1800
        timeout_raw = os.environ.get("SMART_TEST_TIMEOUT_SECONDS", str(default_timeout))
        try:
            timeout_seconds = int(timeout_raw)
        except ValueError:
            timeout_seconds = default_timeout
        return max(timeout_seconds, 60)

    def _should_fallback_from_hatch(
        self, return_code: int | None, output_lines: list[str], startup_error: Exception | None
    ) -> bool:
        """Detect Hatch startup/env failures that should fall back to direct pytest."""
        if startup_error is not None or return_code is None:
            return True
        if return_code == 0:
            return False
        combined_output = "\n".join(output_lines)
        return any(marker in combined_output for marker in self._HATCH_ENV_BROKEN_MARKERS)

    def _get_coverage_threshold(self) -> float:
        """Get coverage threshold from pyproject.toml or environment variable."""
        # First check environment variable
        env_threshold = os.environ.get("COVERAGE_THRESHOLD")
        if env_threshold:
            try:
                return float(env_threshold)
            except ValueError:
                logger.warning("Invalid COVERAGE_THRESHOLD environment variable: %s", env_threshold)

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
                logger.warning("Could not read coverage threshold from pyproject.toml: %s", e)

        # Default fallback (used only when env and pyproject are unavailable/invalid)
        # Note: When pyproject.toml provides fail_under, that value (e.g., 70) takes precedence.
        return 80.0

    def _load_cache(self) -> dict[str, Any]:
        """Load coverage cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file) as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        return cast(dict[str, Any], loaded)
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
        except (FileNotFoundError, PermissionError, IsADirectoryError):
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
        source_files: list[Path] = []
        for source_dir in self.source_dirs:
            source_path = self.project_root / source_dir
            if source_path.exists():
                for py_file in source_path.rglob("*.py"):
                    if not self._should_exclude_file(py_file):
                        source_files.append(py_file)
        return source_files

    def _get_test_files(self) -> list[Path]:
        """Get all test files including fixtures and helpers."""
        test_files: list[Path] = []
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

    def _git_modified_test_files(self, cached: dict[str, str]) -> list[Path]:
        modified: list[Path] = []
        for rel in self._git_changed_paths():
            p = self.project_root / rel
            if not p.exists() or self._should_exclude_file(p):
                continue
            if not any(str(p).startswith(str(self.project_root / d)) for d in self.test_dirs):
                continue
            h = self._get_file_hash(p)
            if h and cached.get(rel) != h:
                modified.append(p)
        return modified

    def _scan_modified_test_files(self, cached: dict[str, str]) -> list[Path]:
        modified: list[Path] = []
        for p in self._get_test_files():
            rel = str(p.relative_to(self.project_root))
            if self._should_exclude_file(p):
                continue
            h = self._get_file_hash(p)
            if h and cached.get(rel) != h:
                modified.append(p)
        return modified

    def _get_modified_test_files(self) -> list[Path]:
        """Get modified test files using git candidates; fallback to full scan if git unavailable."""
        if not self.cache.get("last_full_run"):
            return []
        cached: dict[str, str] = cast(dict[str, str], self.cache.get("test_file_hashes", {}))
        git_changed = self._git_changed_paths()
        if git_changed:
            return self._git_modified_test_files(cached)
        return self._scan_modified_test_files(cached)

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
        test_files: list[Path] = []
        test_dir = self.test_level_dirs.get(test_level)
        if not test_dir:
            return test_files

        test_path = self.project_root / test_dir
        if test_path.exists():
            for py_file in test_path.rglob("*.py"):
                if not self._should_exclude_file(py_file):
                    # For e2e tests, include files with 'e2e' or 'workflow' in the name
                    if test_level == "e2e":
                        name_lower = py_file.name.lower()
                        if "e2e" not in name_lower and "workflow" not in name_lower:
                            continue
                    test_files.append(py_file)
        return test_files

    def _get_config_files(self) -> list[Path]:
        """Get all configuration files that affect test behavior."""
        config_files: list[Path] = []
        for config_file in self.config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                config_files.append(config_path)
        return config_files

    def _path_is_under_roots(self, path: Path, roots: list[str]) -> bool:
        """Return whether a path is located under any configured repository root."""
        return any(str(path).startswith(str(self.project_root / root)) for root in roots)

    def _has_changed_file(
        self,
        file_path: Path,
        cached_hashes: dict[str, str],
        *,
        allow_version_only: bool = False,
    ) -> bool:
        """Return whether a tracked file differs from the cached hash."""
        rel = str(file_path.relative_to(self.project_root))
        current_hash = self._get_file_hash(file_path)
        if not current_hash:
            return False
        cached_hash = cached_hashes.get(rel, "")
        if cached_hash == current_hash:
            return False
        return not allow_version_only or not self._is_version_only_change(rel, cached_hash, current_hash)

    def _collect_changed_files(
        self,
        *,
        cached_hashes: dict[str, str],
        candidate_paths: list[Path],
        allow_version_only: bool = False,
    ) -> list[Path]:
        """Collect candidate files whose contents differ from the cached hash."""
        changed: list[Path] = []
        for path in candidate_paths:
            if self._should_exclude_file(path):
                continue
            if self._has_changed_file(path, cached_hashes, allow_version_only=allow_version_only):
                changed.append(path)
        return changed

    def _git_candidate_files(self, roots: list[str] | None = None) -> list[Path]:
        """Return changed files from git filtered to repository roots when provided."""
        candidates: list[Path] = []
        for rel in self._git_changed_paths():
            path = self.project_root / rel
            if not path.exists() or not path.is_file() or self._should_exclude_file(path):
                continue
            if roots is not None and not self._path_is_under_roots(path, roots):
                continue
            candidates.append(path)
        return candidates

    def _count_non_version_lines(self, content: str, version_pattern: str) -> int:
        """Count content lines that do not contain a version assignment."""
        return sum(
            1 for line in content.splitlines() if "version" not in line.lower() or not re.search(version_pattern, line)
        )

    def _version_pattern_matches(self, content: str, version_pattern: str) -> list[str]:
        """Return semantic-version matches for a given regex pattern."""
        return [match for match in re.findall(version_pattern, content) if re.match(r"^\d+\.\d+\.\d+$", match)]

    def _is_version_only_pyproject(self, content: str) -> bool:
        version_pattern = r'version\s*=\s*["\'](\d+\.\d+\.\d+)["\']'
        return (
            len(self._version_pattern_matches(content, version_pattern)) == 1
            and self._count_non_version_lines(content, version_pattern) > 10
        )

    def _is_version_only_setup(self, content: str) -> bool:
        version_pattern = r'version\s*=\s*["\'](\d+\.\d+\.\d+)["\']'
        return (
            len(self._version_pattern_matches(content, version_pattern)) == 1
            and self._count_non_version_lines(content, version_pattern) > 5
        )

    def _is_version_only_init(self, content: str) -> bool:
        version_pattern = r'__version__\s*=\s*["\'](\d+\.\d+\.\d+)["\']'
        if len(self._version_pattern_matches(content, version_pattern)) != 1:
            return False
        non_version_lines = [
            line
            for line in content.splitlines()
            if "version" not in line.lower()
            and not line.strip().startswith("#")
            and not line.strip().startswith('"""')
            and not line.strip().startswith("'''")
            and line.strip()
        ]
        return len(non_version_lines) <= 2

    def _source_file_for_test(self, test_file: Path) -> Path | None:
        """Resolve the source file a unit test targets."""
        if not test_file.name.startswith("test_"):
            return None
        source_name = test_file.name[5:]
        test_str = str(test_file)
        if "tools" in test_str:
            return self.project_root / "tools" / source_name
        if "tests" not in test_str or "unit" not in test_str:
            return None
        try:
            unit_index = test_file.parts.index("unit")
        except ValueError:
            return None
        if unit_index + 1 >= len(test_file.parts):
            return None
        return self.project_root / "src" / test_file.parts[unit_index + 1] / source_name

    def _tested_source_files(self, test_files: list[Path]) -> set[str]:
        """Resolve source file paths covered by a set of unit tests."""
        tested_source_files: set[str] = set()
        for test_file in test_files:
            source_file = self._source_file_for_test(test_file)
            if source_file is not None and source_file.exists():
                tested_source_files.add(str(source_file.relative_to(self.project_root)))
        return tested_source_files

    def _parse_coverage_row(self, line: str) -> tuple[str, int, int] | None:
        """Parse a coverage table row into file name and statement counts."""
        parts = line.split()
        if len(parts) < 3:
            return None
        try:
            return parts[0], int(parts[1]), int(parts[2])
        except ValueError:
            return None

    def _parse_logs_count(self, argv: list[str]) -> int:
        """Parse the optional count argument for the logs command."""
        if len(argv) <= 2:
            return 5
        return int(argv[2])

    def _log_status_summary(self, status: dict[str, Any]) -> None:
        """Render the current smart-test status summary."""
        logger.info("Coverage Status:")
        logger.info("   Last Run: %s", status["last_run"] or "Never")
        logger.info("   Coverage: %.1f%%", status["coverage_percentage"])
        logger.info("   Test Count: %s", status["test_count"])
        logger.info("   Source Changed: %s", status["source_changed"])
        logger.info("   Test Changed: %s", status["test_changed"])
        logger.info("   Config Changed: %s", status["config_changed"])
        logger.info("   Needs Full Run: %s", status["needs_full_run"])
        logger.info("   Threshold: %.1f%%", self.coverage_threshold)
        if status["coverage_percentage"] < self.coverage_threshold:
            logger.warning("   Coverage below threshold!")
        else:
            logger.info("   Coverage meets threshold")

    def _handle_threshold_command(self) -> int:
        """Evaluate the current cached coverage against the configured threshold."""
        status = self.get_status()
        current_coverage = status["coverage_percentage"]
        logger.info("Coverage Threshold Check:")
        logger.info("   Current Coverage: %.1f%%", current_coverage)
        logger.info("   Required Threshold: %.1f%%", self.coverage_threshold)
        if current_coverage < self.coverage_threshold:
            logger.error("   Coverage below threshold!")
            logger.info("   Difference: %.1f%% needed", self.coverage_threshold - current_coverage)
            return 1
        logger.info("   Coverage meets threshold!")
        logger.info("   Margin: %.1f%% above threshold", current_coverage - self.coverage_threshold)
        return 0

    def _coverage_row_adds_to_tested(self, line: str, tested_source_files: set[str]) -> tuple[int, int] | None:
        parsed = self._parse_coverage_row(line)
        if parsed is None:
            return None
        file_name, statements, missed = parsed
        if any(tested_file in file_name for tested_file in tested_source_files):
            return statements, missed
        return None

    def _iter_coverage_table_data_lines(self, output_lines: list[str]) -> list[str]:
        """Lines between the coverage header row and the TOTAL row (exclusive)."""
        data_lines: list[str] = []
        in_coverage_table = False
        for line in output_lines:
            if "Name" in line and "Stmts" in line and "Miss" in line and "Cover" in line:
                in_coverage_table = True
                continue
            if in_coverage_table and line.startswith("---"):
                continue
            if in_coverage_table and "TOTAL" in line:
                break
            if in_coverage_table and line.strip():
                data_lines.append(line)
        return data_lines

    def _accumulate_tested_coverage(self, output_lines: list[str], tested_source_files: set[str]) -> tuple[int, int]:
        """Aggregate covered statement counts for the tested source file set."""
        total_statements = 0
        total_missed = 0
        for line in self._iter_coverage_table_data_lines(output_lines):
            add = self._coverage_row_adds_to_tested(line, tested_source_files)
            if add is not None:
                st, ms = add
                total_statements += st
                total_missed += ms
        return total_statements, total_missed

    def _popen_stream_to_log(
        self,
        cmd: list[str],
        log_file: TextIO,
        *,
        timeout: int,
    ) -> tuple[int | None, list[str], Exception | None]:
        """Run ``cmd``, stream stdout to *log_file* and return (rc, lines, spawn_error)."""
        output_local: list[str] = []
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )
        except Exception as exc:
            return None, output_local, exc

        assert proc.stdout is not None
        for line in iter(proc.stdout.readline, ""):
            if line:
                logger.debug("%s", line.rstrip())
                log_file.write(line)
                log_file.flush()
                output_local.append(line)
        try:
            rc = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(Exception):
                proc.kill()
            raise
        return rc, output_local, None

    @staticmethod
    def _parse_total_coverage_percent(output_lines: list[str]) -> float:
        """Best-effort parse of overall coverage %% from pytest/coverage output lines."""
        coverage_percentage = 0.0
        for line in output_lines:
            if "TOTAL" not in line or "%" not in line:
                continue
            for part in line.split():
                if part.endswith("%"):
                    try:
                        return float(part[:-1])
                    except ValueError:
                        pass
        return coverage_percentage

    @staticmethod
    def _pytest_count_from_banner_line(line: str) -> int | None:
        """Parse count from ``======== N passed`` style summary lines."""
        if not line.startswith("========") or (" passed" not in line and " failed" not in line):
            return None
        words = line.split()
        for i, word in enumerate(words):
            if word in ("passed", "passed,", "failed", "failed,") and i > 0 and words[i - 1] != "subtests":
                try:
                    return int(words[i - 1])
                except ValueError:
                    return None
        return None

    @staticmethod
    def _pytest_count_from_plain_summary_line(line: str) -> int | None:
        """Parse count from looser pytest output lines (non-banner)."""
        if (" passed" not in line and " failed" not in line) or "subtests passed" in line:
            return None
        words = line.split()
        for i, word in enumerate(words):
            if word in ("passed", "failed") and i > 0:
                try:
                    return int(words[i - 1])
                except ValueError:
                    return None
        return None

    @classmethod
    def _try_parse_pytest_summary_test_count(cls, line: str) -> int | None:
        """Parse test count from a pytest summary line, if present."""
        if " passed" not in line and " failed" not in line:
            return None
        n = cls._pytest_count_from_banner_line(line)
        if n is not None:
            return n
        return cls._pytest_count_from_plain_summary_line(line)

    def _parse_pytest_test_count(self, output_lines: list[str]) -> int:
        test_count = 0
        for line in output_lines:
            n = self._try_parse_pytest_summary_test_count(line)
            if n is not None:
                test_count = n
        return test_count

    @staticmethod
    def _line_indicates_coverage_threshold_failure(line: str) -> bool:
        low = line.lower()
        return (
            "coverage failure" in low
            or "fail_under" in low
            or "less than fail-under" in low
            or ("total of" in line and "is less than fail-under" in line)
        )

    def _run_coverage_hatch_or_pytest(self, log_file: TextIO) -> tuple[int | None, list[str]]:
        """Execute full-suite hatch (optional fallback to pytest) with streaming logs."""
        output_lines: list[str] = []
        timeout_full = 600
        if self.use_hatch:
            hatch_cmd = self._build_hatch_test_cmd(with_coverage=True, parallel=True)
            rc, out, err = self._popen_stream_to_log(hatch_cmd, log_file, timeout=timeout_full)
            output_lines.extend(out)
            if self._should_fallback_from_hatch(rc, out, err):
                logger.warning("Hatch test failed to start cleanly; falling back to pytest.")
                log_file.write("Hatch test failed to start cleanly; falling back to pytest.\n")
                pytest_cmd = self._build_pytest_cmd(with_coverage=True, parallel=True)
                rc2, out2, _ = self._popen_stream_to_log(pytest_cmd, log_file, timeout=timeout_full)
                output_lines.extend(out2)
                return rc2 if rc2 is not None else 1, output_lines
            return rc, output_lines
        pytest_cmd = self._build_pytest_cmd(with_coverage=True, parallel=True)
        rc, out, _ = self._popen_stream_to_log(pytest_cmd, log_file, timeout=timeout_full)
        output_lines.extend(out)
        return rc if rc is not None else 1, output_lines

    def _run_leveled_hatch_or_pytest(
        self,
        log_file: TextIO,
        test_level: str,
        test_file_strings: list[str],
        want_coverage: bool,
        timeout_seconds: int,
    ) -> tuple[int | None, list[str]]:
        """Run hatch or pytest for a specific test level and file list."""
        output_lines: list[str] = []
        if self.use_hatch:
            hatch_cmd = self._build_hatch_test_cmd(with_coverage=want_coverage, extra_args=test_file_strings)
            selected_env = self.hatch_test_env if self.hatch_test_env else "default hatch-test matrix/env"
            logger.info("Using hatch for %s tests (env selector: %s)", test_level, selected_env)
            logger.debug("Executing: %s", shlex.join(hatch_cmd))
            rc, out, err = self._popen_stream_to_log(hatch_cmd, log_file, timeout=timeout_seconds)
            output_lines.extend(out)
            if err is not None or rc is None:
                logger.warning("Hatch test failed to start; falling back to pytest.")
                log_file.write("Hatch test failed to start; falling back to pytest.\n")
                pytest_cmd = self._build_pytest_cmd(with_coverage=want_coverage, extra_args=test_file_strings)
                logger.debug("Executing fallback: %s", shlex.join(pytest_cmd))
                rc2, out2, _ = self._popen_stream_to_log(pytest_cmd, log_file, timeout=timeout_seconds)
                output_lines.extend(out2)
                return rc2 if rc2 is not None else 1, output_lines
            return rc, output_lines
        pytest_cmd = self._build_pytest_cmd(with_coverage=want_coverage, extra_args=test_file_strings)
        logger.info("Hatch disabled; executing pytest directly: %s", shlex.join(pytest_cmd))
        rc, out, _ = self._popen_stream_to_log(pytest_cmd, log_file, timeout=timeout_seconds)
        output_lines.extend(out)
        return rc if rc is not None else 1, output_lines

    def _adjust_success_for_coverage_threshold(
        self,
        success: bool,
        test_level: str,
        test_count: int,
        coverage_percentage: float,
        output_lines: list[str],
    ) -> bool:
        """Treat threshold-only failures as success for unit/folder runs when appropriate."""
        if success or test_level not in ("unit", "folder") or test_count <= 0 or coverage_percentage <= 0:
            return success
        if not any(self._line_indicates_coverage_threshold_failure(line) for line in output_lines):
            return success
        logger.warning(
            "Overall coverage %.1f%% is below threshold of %.1f%%",
            coverage_percentage,
            self.coverage_threshold,
        )
        logger.info("This is expected for unit/folder tests. Full test run will enforce the threshold.")
        return True

    def _log_completed_test_run(
        self,
        success: bool,
        test_level: str,
        test_count: int,
        coverage_percentage: float,
        tested_coverage_percentage: float,
        test_log_file: Path,
        coverage_log_file: Path,
        return_code: int | None,
    ) -> None:
        """Emit summary log lines after a leveled test run."""
        if success:
            if test_level in ("unit", "folder") and tested_coverage_percentage > 0:
                logger.info(
                    "%s tests completed: %d tests, %.1f%% overall, %.1f%% tested code coverage",
                    test_level.title(),
                    test_count,
                    coverage_percentage,
                    tested_coverage_percentage,
                )
            else:
                logger.info(
                    "%s tests completed: %d tests, %.1f%% coverage",
                    test_level.title(),
                    test_count,
                    coverage_percentage,
                )
            logger.info("Full %s test log: %s", test_level, test_log_file)
            logger.info("%s coverage log: %s", test_level.title(), coverage_log_file)
        else:
            logger.error("%s tests failed with exit code %s", test_level.title(), return_code)
            logger.info("Check %s test log for details: %s", test_level, test_log_file)
            logger.info("Check %s coverage log for details: %s", test_level, coverage_log_file)

    def _log_tested_coverage_vs_threshold(self, test_level: str, tested_coverage_percentage: float) -> None:
        if test_level not in ("unit", "folder") or tested_coverage_percentage <= 0:
            return
        if tested_coverage_percentage < self.coverage_threshold:
            logger.warning(
                "Tested code coverage %.1f%% is below threshold of %.1f%%",
                tested_coverage_percentage,
                self.coverage_threshold,
            )
            logger.info("Consider adding more tests for the modified files.")
        else:
            logger.info(
                "Tested code coverage %.1f%% meets threshold of %.1f%%",
                tested_coverage_percentage,
                self.coverage_threshold,
            )

    def _get_modified_files(self) -> list[Path]:
        """Get list of modified source files.
        Prefer git candidates; fallback to full scan when git is unavailable or reports no changes."""
        if not self.cache.get("last_full_run"):
            return []

        cached_hashes: dict[str, str] = cast(dict[str, str], self.cache.get("file_hashes", {}))
        git_candidates = self._git_candidate_files(self.source_dirs)
        if git_candidates:
            return self._collect_changed_files(
                cached_hashes=cached_hashes,
                candidate_paths=git_candidates,
                allow_version_only=True,
            )
        # Fallback: scan all known source files and compare hashes
        return self._collect_changed_files(
            cached_hashes=cached_hashes,
            candidate_paths=self._get_source_files(),
            allow_version_only=True,
        )

    def _get_modified_folders(self) -> set[Path]:
        """Get set of parent folders containing modified files."""
        modified_files = self._get_modified_files()
        modified_folders: set[Path] = set()

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
        unit_tests: list[Path] = []

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
        folder_files: list[Path] = []

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
        cached_hashes: dict[str, str] = cast(dict[str, str], self.cache.get("file_hashes", {}))
        git_candidates = self._git_candidate_files(self.source_dirs)
        if git_candidates:
            return any(self._has_changed_file(path, cached_hashes, allow_version_only=True) for path in git_candidates)
        # Fallback: compare all source files against cache
        return any(
            self._has_changed_file(path, cached_hashes, allow_version_only=True) for path in self._get_source_files()
        )

    def _git_test_changes_detected(self, cached_test_hashes: dict[str, str]) -> bool:
        for rel in self._git_changed_paths():
            p = self.project_root / rel
            if not p.exists() or self._should_exclude_file(p):
                continue
            if not any(str(p).startswith(str(self.project_root / d)) for d in self.test_dirs):
                continue
            h = self._get_file_hash(p)
            if h and cached_test_hashes.get(rel) != h:
                return True
        return False

    def _scan_test_changes_detected(self, cached_test_hashes: dict[str, str]) -> bool:
        for p in self._get_test_files():
            if self._should_exclude_file(p):
                continue
            rel = str(p.relative_to(self.project_root))
            h = self._get_file_hash(p)
            if h and cached_test_hashes.get(rel) != h:
                return True
        return False

    def _has_test_changes(self) -> bool:
        """Check if any test files have changed since last coverage run.
        Uses git candidates when available; otherwise falls back to full scan of test dirs."""
        if not self.cache.get("last_full_run"):
            return True
        cached_test_hashes: dict[str, str] = cast(dict[str, str], self.cache.get("test_file_hashes", {}))
        git_changed = self._git_changed_paths()
        if git_changed:
            return self._git_test_changes_detected(cached_test_hashes)
        return self._scan_test_changes_detected(cached_test_hashes)

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

            if file_path.endswith("pyproject.toml"):
                return self._is_version_only_pyproject(current_content)
            if file_path.endswith("setup.py"):
                return self._is_version_only_setup(current_content)
            if file_path.endswith("src/__init__.py"):
                return self._is_version_only_init(current_content)

        except Exception:
            # If we can't read or parse the file, assume it's not version-only
            pass

        return False

    def _has_config_changes(self) -> bool:
        """Check if any configuration files have changed since last coverage run.
        Uses git candidates when available; otherwise falls back to full scan of config files."""
        if not self.cache.get("last_full_run"):
            return True
        cached_config_hashes: dict[str, str] = cast(dict[str, str], self.cache.get("config_file_hashes", {}))
        git_candidates = [path for path in self._git_candidate_files() if path.name in self.config_files]
        if git_candidates:
            return any(
                self._has_changed_file(path, cached_config_hashes, allow_version_only=True) for path in git_candidates
            )
        # Fallback: compare all config files against cache
        return any(
            self._has_changed_file(path, cached_config_hashes, allow_version_only=True)
            for path in self._get_config_files()
        )

    def _run_coverage_tests(self) -> tuple[bool, int, float]:
        """Run full coverage tests and return (success, test_count, coverage_percentage)."""
        logger.info("Running full test suite with coverage...")

        # Create logs directory if it doesn't exist
        logs_dir = self.project_root / "logs" / "tests"
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Generate timestamp for log files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_log_file = logs_dir / f"test_run_{timestamp}.log"
        coverage_log_file = logs_dir / f"coverage_{timestamp}.log"

        try:
            # Run tests with coverage - capture both stdout and stderr
            logger.info("Test output will be logged to: %s", test_log_file)
            logger.info("Coverage details will be logged to: %s", coverage_log_file)

            with open(test_log_file, "w") as log_file, open(coverage_log_file, "w") as cov_file:
                # Write header to log files
                log_file.write(f"Test Run Started: {datetime.now().isoformat()}\n")
                log_file.write("=" * 80 + "\n")
                cov_file.write(f"Coverage Analysis Started: {datetime.now().isoformat()}\n")
                cov_file.write("=" * 80 + "\n")

                return_code, output_lines = self._run_coverage_hatch_or_pytest(log_file)

                # Write footer to log files
                log_file.write("\n" + "=" * 80 + "\n")
                log_file.write(f"Test Run Completed: {datetime.now().isoformat()}\n")
                log_file.write(f"Exit Code: {return_code}\n")

                cov_file.write(f"Coverage Analysis Completed: {datetime.now().isoformat()}\n")
                cov_file.write(f"Exit Code: {return_code}\n")

            coverage_percentage = self._parse_total_coverage_percent(output_lines)
            test_count = self._parse_pytest_test_count(output_lines)
            success = return_code == 0

            # Full tests - coverage threshold is enforced
            if success:
                logger.info("Tests completed: %d tests, %.1f%% coverage", test_count, coverage_percentage)
                logger.info("Full test log: %s", test_log_file)
                logger.info("Coverage log: %s", coverage_log_file)
            else:
                logger.error("Tests failed with exit code %s", return_code)
                logger.info("Check test log for details: %s", test_log_file)
                logger.info("Check coverage log for details: %s", coverage_log_file)

            return success, test_count, coverage_percentage

        except subprocess.TimeoutExpired:
            logger.error("Test run timed out after 10 minutes")
            return False, 0, 0
        except Exception as e:
            logger.error("Error running tests: %s", e)
            return False, 0, 0

    def _run_tests(self, test_files: list[Path], test_level: str) -> tuple[bool, int, float]:
        """Run tests for specific files and return (success, test_count, coverage_percentage)."""
        if not test_files:
            logger.info("No %s tests found to run", test_level)
            return True, 0, 100.0

        logger.info("Running %s tests for %d files...", test_level, len(test_files))
        timeout_seconds = self._get_test_timeout_seconds(test_level)
        logger.debug("Test subprocess timeout: %ds", timeout_seconds)

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

            logger.info("%s test output will be logged to: %s", test_level.title(), test_log_file)
            logger.info("%s coverage details will be logged to: %s", test_level.title(), coverage_log_file)

            with open(test_log_file, "w") as log_file, open(coverage_log_file, "w") as cov_file:
                # Write header to log files
                log_file.write(f"{test_level.title()} Test Run Started: {datetime.now().isoformat()}\n")
                log_file.write("=" * 80 + "\n")
                cov_file.write(f"{test_level.title()} Coverage Analysis Started: {datetime.now().isoformat()}\n")
                cov_file.write("=" * 80 + "\n")

                want_coverage = test_level in ("unit", "folder")
                return_code, output_lines = self._run_leveled_hatch_or_pytest(
                    log_file,
                    test_level,
                    test_file_strings,
                    want_coverage,
                    timeout_seconds,
                )

                # Write footer to log files
                log_file.write("\n" + "=" * 80 + "\n")
                log_file.write(f"{test_level.title()} Test Run Completed: {datetime.now().isoformat()}\n")
                log_file.write(f"Exit Code: {return_code}\n")

                cov_file.write(f"{test_level.title()} Coverage Analysis Completed: {datetime.now().isoformat()}\n")
                cov_file.write(f"Exit Code: {return_code}\n")

            test_count = self._parse_pytest_test_count(output_lines)
            success = return_code == 0

            if test_level in ("integration", "e2e"):
                coverage_percentage = 100.0
                tested_coverage_percentage = 100.0
            else:
                coverage_percentage = self._parse_total_coverage_percent(output_lines)

            if test_level in ("unit", "folder") and test_files:
                tested_coverage_percentage = self._calculate_tested_coverage(test_files, output_lines)
            else:
                tested_coverage_percentage = coverage_percentage

            success = self._adjust_success_for_coverage_threshold(
                success, test_level, test_count, coverage_percentage, output_lines
            )
            self._log_tested_coverage_vs_threshold(test_level, tested_coverage_percentage)
            self._log_completed_test_run(
                success,
                test_level,
                test_count,
                coverage_percentage,
                tested_coverage_percentage,
                test_log_file,
                coverage_log_file,
                return_code,
            )

            # Cleanup generated test files after test run
            self._cleanup_generated_test_files()

            return success, test_count, coverage_percentage

        except subprocess.TimeoutExpired:
            logger.error("%s test run timed out after 10 minutes", test_level.title())
            # Cleanup even on timeout
            self._cleanup_generated_test_files()
            return False, 0, 0
        except Exception as e:
            logger.error("Error running %s tests: %s", test_level, e)
            # Cleanup even on error
            self._cleanup_generated_test_files()
            return False, 0, 0

    def _cleanup_generated_test_files(self) -> None:
        """Clean up generated test_*_contract.py files from project root."""
        try:
            # Find all test_*_contract.py files in project root
            test_files = list(self.project_root.glob("test_*_contract.py"))

            if test_files:
                logger.debug("Cleaning up %d generated test files...", len(test_files))
                for test_file in test_files:
                    try:
                        test_file.unlink()
                        logger.debug("Removed: %s", test_file.name)
                    except OSError as e:
                        logger.warning("Could not remove %s: %s", test_file.name, e)
                logger.debug("Cleanup completed")
            else:
                logger.debug("No generated test files to clean up")

        except Exception as e:
            logger.warning("Error during cleanup: %s", e)

    def _calculate_tested_coverage(self, test_files: list[Path], output_lines: list[str]) -> float:
        """Calculate coverage percentage for only the tested files."""
        if not test_files:
            return 0.0

        tested_source_files = self._tested_source_files(test_files)

        if not tested_source_files:
            return 0.0

        total_statements, total_missed = self._accumulate_tested_coverage(output_lines, tested_source_files)

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

    def _maybe_warn_subthreshold_non_full(
        self, success: bool, enforce_threshold: bool, coverage_percentage: float
    ) -> None:
        if success and enforce_threshold:
            self._check_coverage_threshold(coverage_percentage)
        elif success and not enforce_threshold and coverage_percentage < self.coverage_threshold:
            logger.warning(
                "Coverage %.1f%% is below threshold of %.1f%%",
                coverage_percentage,
                self.coverage_threshold,
            )
            logger.info("This is expected for unit/folder tests. Full test run will enforce the threshold.")

    def _refresh_all_tracked_hashes(
        self,
        file_hashes: dict[str, str],
        test_file_hashes: dict[str, str],
        config_file_hashes: dict[str, str],
    ) -> None:
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
        self._maybe_warn_subthreshold_non_full(success, enforce_threshold, coverage_percentage)

        # Prepare existing maps
        file_hashes: dict[str, str] = dict(cast(dict[str, str], self.cache.get("file_hashes", {})))
        test_file_hashes: dict[str, str] = dict(cast(dict[str, str], self.cache.get("test_file_hashes", {})))
        config_file_hashes: dict[str, str] = dict(cast(dict[str, str], self.cache.get("config_file_hashes", {})))

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
            self._refresh_all_tracked_hashes(file_hashes, test_file_hashes, config_file_hashes)

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

    @ensure(lambda result: isinstance(result, bool), "check_if_full_test_needed must return bool")
    def check_if_full_test_needed(self) -> bool:
        """Check if a full test run is needed.
        For local smart-test runs we NEVER require a full run; CI will run the full suite."""
        source_changed = self._has_source_changes()
        test_changed = self._has_test_changes()
        config_changed = self._has_config_changes()

        if config_changed:
            logger.info("Configuration or infra changes detected - will run changed-only tests (no full run)")
            return False

        if source_changed or test_changed:
            reasons: list[str] = []
            if source_changed:
                reasons.append("source files")
            if test_changed:
                reasons.append("test files")
            logger.info("%s have changed - running changed-only tests", "/".join(reasons))
            return False

        logger.info("No relevant changes detected - using cached coverage data")
        return False

    @ensure(lambda result: isinstance(result, dict), "get_status must return dict")
    def get_status(self) -> dict[str, Any]:
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

    @require(lambda count: count >= 0, "count must be non-negative")
    @ensure(lambda result: isinstance(result, list), "get_recent_logs must return list")
    def get_recent_logs(self, count: int = 5) -> list[Path]:
        """Get recent test log files."""
        logs_dir = self.project_root / "logs" / "tests"
        if not logs_dir.exists():
            return []

        # Get all test log files and sort by modification time
        log_files = list(logs_dir.glob("test_run_*.log"))
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return log_files[:count]

    @require(lambda count: count >= 0, "count must be non-negative")
    @ensure(lambda result: result is None, "show_recent_logs must return None")
    def show_recent_logs(self, count: int = 3) -> None:
        """Show recent test log files and their status."""
        recent_logs = self.get_recent_logs(count)

        if not recent_logs:
            logger.info("No test logs found")
            return

        logger.info("Recent test logs (last %d):", len(recent_logs))
        for i, log_file in enumerate(recent_logs, 1):
            # Get file modification time
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)

            # Try to determine success/failure from log content
            status = "Unknown"
            try:
                with open(log_file) as f:
                    content = f.read()
                    if "Exit Code: 0" in content:
                        status = "Passed"
                    elif "Exit Code:" in content:
                        status = "Failed"
            except Exception:
                pass

            logger.info("   %d. %s - %s - %s", i, log_file.name, mtime.strftime("%Y-%m-%d %H:%M:%S"), status)

    @ensure(lambda result: result is None, "show_latest_log must return None")
    def show_latest_log(self) -> None:
        """Show the latest test log content."""
        recent_logs = self.get_recent_logs(1)

        if not recent_logs:
            logger.info("No test logs found")
            return

        latest_log = recent_logs[0]
        logger.info("Latest test log: %s", latest_log.name)

        try:
            file_mode = latest_log.stat().st_mode
            if file_mode & 0o444 == 0:
                raise PermissionError("Log file is not readable due to permissions")
            with open(latest_log) as f:
                content = f.read()
                # Show last 50 lines to avoid overwhelming output
                lines = content.split("\n")
                if len(lines) > 50:
                    logger.debug("... (showing last 50 lines)")
                    lines = lines[-50:]
                logger.info("%s", "\n".join(lines))
        except Exception as e:
            logger.error("Error reading log file: %s", e)

    @require(lambda test_level: test_level in {"unit", "folder", "integration", "e2e", "full", "auto"})
    @ensure(lambda result: isinstance(result, bool), "run_smart_tests must return bool")
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
            logger.info(
                "Using cached results: %d tests, %.1f%% coverage",
                status["test_count"],
                status["coverage_percentage"],
            )
            return status.get("success", False)
        if force:
            # Force mode - run the specified level regardless of changes
            return self.run_tests_by_level(test_level)
        return self.run_tests_by_level(test_level)

    @require(lambda test_level: test_level in {"unit", "folder", "integration", "e2e", "full", "auto"})
    @ensure(lambda result: isinstance(result, bool), "run_tests_by_level must return bool")
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
        logger.error("Unknown test level: %s", test_level)
        return False

    def _run_unit_tests(self) -> bool:
        """Run unit tests for modified files only."""
        modified_files = self._get_modified_files()
        if not modified_files:
            logger.info("No modified files detected - no unit tests to run")
            return True

        logger.info("Found %d modified files:", len(modified_files))
        for file_path in modified_files:
            try:
                relative_path = file_path.relative_to(self.project_root)
                logger.info("   - %s", relative_path)
            except ValueError:
                logger.info("   - %s", file_path)

        unit_tests = self._get_unit_tests_for_files(modified_files)
        if not unit_tests:
            logger.warning("No unit tests found for modified files")
            logger.info("Consider adding unit tests for:")
            for file_path in modified_files:
                try:
                    relative_path = file_path.relative_to(self.project_root)
                    logger.info("   - %s", relative_path)
                except ValueError:
                    logger.info("   - %s", file_path)
            return True

        logger.info("Running unit tests for %d test files...", len(unit_tests))
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
            logger.info("Unit tests completed: %d tests, %.1f%% coverage", test_count, coverage_percentage)
        else:
            logger.error("Unit tests failed")

        return success

    def _run_folder_tests(self) -> bool:
        """Run unit tests for all files in modified folders."""
        modified_folders = self._get_modified_folders()
        if not modified_folders:
            logger.info("No modified folders detected - no folder tests to run")
            return True

        logger.info("Found %d modified folders:", len(modified_folders))
        for folder in modified_folders:
            try:
                relative_path = folder.relative_to(self.project_root)
                logger.info("   - %s", relative_path)
            except ValueError:
                logger.info("   - %s", folder)

        # Get all source files in the modified folders
        folder_files = self._get_files_in_folders(modified_folders)
        if not folder_files:
            logger.info("No source files found in modified folders")
            return True

        logger.info("Found %d source files in modified folders:", len(folder_files))
        for file_path in folder_files:
            try:
                relative_path = file_path.relative_to(self.project_root)
                logger.info("   - %s", relative_path)
            except ValueError:
                logger.info("   - %s", file_path)

        # Get unit tests for all files in the modified folders
        folder_tests = self._get_unit_tests_for_files(folder_files)
        if not folder_tests:
            logger.warning("No unit tests found for files in modified folders")
            logger.info("Consider adding unit tests for:")
            for file_path in folder_files:
                try:
                    relative_path = file_path.relative_to(self.project_root)
                    logger.info("   - %s", relative_path)
                except ValueError:
                    logger.info("   - %s", file_path)
            return True

        logger.info("Running unit tests for %d test files in modified folders...", len(folder_tests))
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
            logger.info("Folder tests completed: %d tests, %.1f%% coverage", test_count, coverage_percentage)
        else:
            logger.error("Folder tests failed")

        return success

    def _run_integration_tests(self) -> bool:
        """Run all integration tests."""
        integration_tests = self._get_test_files_by_level("integration")
        if not integration_tests:
            logger.info("No integration tests found")
            return True

        logger.info("Found %d integration test files:", len(integration_tests))
        for test_file in integration_tests:
            try:
                relative_path = test_file.relative_to(self.project_root)
                logger.info("   - %s", relative_path)
            except ValueError:
                logger.info("   - %s", test_file)

        logger.info("Running integration tests...")
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
            logger.info("Integration tests completed: %d tests, %.1f%% coverage", test_count, coverage_percentage)
            logger.info(
                "Note: Integration test coverage is not enforced - focus is on component interaction validation"
            )
        else:
            logger.error("Integration tests failed")

        return success

    def _run_e2e_tests(self) -> bool:
        """Run end-to-end tests only."""
        e2e_tests = self._get_test_files_by_level("e2e")
        if not e2e_tests:
            logger.info("No e2e tests found")
            return True

        logger.info("Found %d e2e test files:", len(e2e_tests))
        for test_file in e2e_tests:
            try:
                relative_path = test_file.relative_to(self.project_root)
                logger.info("   - %s", relative_path)
            except ValueError:
                logger.info("   - %s", test_file)

        logger.info("Running e2e tests...")
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
            logger.info("E2E tests completed: %d tests, %.1f%% coverage", test_count, coverage_percentage)
            logger.info("Note: E2E test coverage is not enforced - focus is on full workflow validation")
        else:
            logger.error("E2E tests failed")

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
            logger.info("No changed files detected that map to tests - skipping test execution")
            # Still keep cache timestamp to allow future git comparisons
            self._update_cache(True, 0, self.cache.get("coverage_percentage", 0.0), enforce_threshold=False)
            return True

        return overall_success

    @require(lambda test_level: test_level in {"unit", "folder", "integration", "e2e", "full", "auto"})
    @ensure(lambda result: isinstance(result, bool), "force_full_run must return bool")
    def force_full_run(self, test_level: str = "full") -> bool:
        """Force a test run regardless of file changes."""
        logger.info("Forcing %s test run...", test_level)
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
                path = payload.split(" -> ", 1)[1] if " -> " in payload else payload
                # Normalize and keep repo-relative
                rel = str(Path(path))
                changed.add(rel)
        except Exception:
            # If git not available, return empty set to avoid over-triggering
            pass
        self._git_changed_cache = set(changed)
        return set(changed)

    def _cli_smart_check_exit(self) -> int:
        return 0 if not self.check_if_full_test_needed() else 1

    def _cli_smart_run_exit(self, args: argparse.Namespace) -> int:
        return 0 if self.run_smart_tests(args.level, args.force) else 1

    def _cli_smart_force_exit(self, args: argparse.Namespace) -> int:
        return 0 if self.run_smart_tests(args.level, force=True) else 1

    def _cli_status_with_logs(self) -> int:
        self._log_status_summary(self.get_status())
        self.show_recent_logs(3)
        return 0

    def _cli_logs_paginated(self) -> int:
        try:
            count = self._parse_logs_count(sys.argv)
        except ValueError:
            logger.error("logs count must be a number")
            return 1
        self.show_recent_logs(count)
        return 0

    def _cli_show_latest_log(self) -> int:
        self.show_latest_log()
        return 0

    def _cli_index_baseline(self) -> int:
        logger.info("Indexing current project hashes as baseline (no tests run)...")
        cur_cov = self.cache.get("coverage_percentage", 0.0)
        cur_cnt = self.cache.get("test_count", 0)
        self._update_cache(True, cur_cnt, cur_cov, enforce_threshold=False, update_only=False)
        logger.info("Baseline updated. Future smart runs will consider only new changes.")
        return 0

    def _handle_cli_command(self, args: argparse.Namespace) -> int:
        """Execute the requested CLI command and return its exit code."""
        dispatch: dict[str, Callable[[], int]] = {
            "check": self._cli_smart_check_exit,
            "run": lambda: self._cli_smart_run_exit(args),
            "force": lambda: self._cli_smart_force_exit(args),
            "status": self._cli_status_with_logs,
            "threshold": self._handle_threshold_command,
            "logs": self._cli_logs_paginated,
            "latest": self._cli_show_latest_log,
            "index": self._cli_index_baseline,
        }
        handler = dispatch.get(args.command)
        if handler is None:
            logger.error("Unknown command: %s", args.command)
            logger.info("Use 'python tools/smart_test_coverage.py' without arguments to see usage")
            return 1
        return handler()


@ensure(lambda result: result is None, "main must return None")
def main() -> None:
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
        sys.exit(manager._handle_cli_command(args))

    except CoverageThresholdError as e:
        logger.error("Coverage threshold not met!")
        logger.error("%s", e)
        logger.info("To fix this issue:")
        logger.info("   1. Add more unit tests to increase coverage")
        logger.info("   2. Improve existing test coverage")
        logger.info("   3. Check for untested code paths")
        logger.info("   4. Run 'hatch run smart-test-status' to see detailed coverage")
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
