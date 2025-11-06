#!/usr/bin/env python3
"""
Unit tests for smart_test_coverage.py

Tests the SmartCoverageManager class and its functionality including:
- Cache management
- File change detection
- Test execution
- Status reporting
"""

import json
import os
import shutil
import subprocess
import sys

# Import the module under test
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


# Add project root to path for tools imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import contextlib

from tools.smart_test_coverage import SmartCoverageManager


class TestSmartCoverageManager:
    """Test cases for SmartCoverageManager class."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir).resolve()  # Resolve symlinks

        # Create test directory structure
        (self.temp_path / "src").mkdir()
        (self.temp_path / "tools").mkdir()
        (self.temp_path / "tests").mkdir()
        (self.temp_path / "logs" / "tests").mkdir(parents=True)

        # Initialize manager with temp directory
        self.manager = SmartCoverageManager(str(self.temp_path))

    def teardown_method(self):
        """Clean up after each test."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test SmartCoverageManager initialization."""
        assert self.manager.project_root == self.temp_path
        assert self.manager.cache_dir == self.temp_path / ".coverage_cache"
        assert self.manager.cache_file == self.temp_path / ".coverage_cache" / "coverage_cache.json"
        assert self.manager.source_dirs == ["src", "tools"]
        assert self.manager.test_dirs == ["tests"]

        # Check that cache directory was created
        assert self.manager.cache_dir.exists()

        # Check initial cache state
        assert self.manager.cache["last_full_run"] is None
        assert self.manager.cache["coverage_percentage"] == 0
        assert self.manager.cache["file_hashes"] == {}
        assert self.manager.cache["test_count"] == 0

    def test_load_cache_empty(self):
        """Test loading cache when no cache file exists."""
        # Remove cache file if it exists
        if self.manager.cache_file.exists():
            self.manager.cache_file.unlink()

        cache = self.manager._load_cache()
        expected = {
            "last_full_run": None,
            "coverage_percentage": 0,
            "file_hashes": {},
            "test_count": 0,
            "coverage_data": {},
        }
        assert cache == expected

    def test_load_cache_existing(self):
        """Test loading cache from existing file."""
        test_cache = {
            "last_full_run": "2025-01-01T12:00:00",
            "coverage_percentage": 85.5,
            "file_hashes": {"src/test.py": "abc123"},
            "test_count": 150,
            "coverage_data": {"src/test.py": 0.9},
        }

        with open(self.manager.cache_file, "w") as f:
            json.dump(test_cache, f)

        cache = self.manager._load_cache()
        assert cache == test_cache

    def test_load_cache_invalid_json(self):
        """Test loading cache with invalid JSON."""
        with open(self.manager.cache_file, "w") as f:
            f.write("invalid json content")

        cache = self.manager._load_cache()
        expected = {
            "last_full_run": None,
            "coverage_percentage": 0,
            "file_hashes": {},
            "test_count": 0,
            "coverage_data": {},
        }
        assert cache == expected

    def test_save_cache(self):
        """Test saving cache to file."""
        test_cache = {
            "last_full_run": "2025-01-01T12:00:00",
            "coverage_percentage": 85.5,
            "file_hashes": {"src/test.py": "abc123"},
            "test_count": 150,
        }

        self.manager.cache = test_cache
        self.manager._save_cache()

        with open(self.manager.cache_file) as f:
            saved_cache = json.load(f)

        assert saved_cache == test_cache

    def test_get_file_hash(self):
        """Test file hash calculation."""
        test_file = self.temp_path / "test_file.py"
        test_content = "print('hello world')"

        with open(test_file, "w") as f:
            f.write(test_content)

        file_hash = self.manager._get_file_hash(test_file)
        assert isinstance(file_hash, str)
        assert len(file_hash) == 64  # SHA256 hash length

        # Test with non-existent file
        non_existent = self.temp_path / "non_existent.py"
        hash_result = self.manager._get_file_hash(non_existent)
        assert hash_result == ""

    def test_get_source_files(self):
        """Test getting source files."""
        # Create test files
        (self.temp_path / "src" / "module1.py").write_text("print('module1')")
        (self.temp_path / "src" / "subdir").mkdir()  # Create subdirectory first
        (self.temp_path / "src" / "subdir" / "module2.py").write_text("print('module2')")
        (self.temp_path / "tools" / "tool1.py").write_text("print('tool1')")
        (self.temp_path / "tests" / "test_module.py").write_text("print('test')")

        source_files = self.manager._get_source_files()
        source_paths = [str(f.relative_to(self.temp_path)) for f in source_files]

        assert "src/module1.py" in source_paths
        assert "src/subdir/module2.py" in source_paths
        assert "tools/tool1.py" in source_paths
        assert "tests/test_module.py" not in source_paths  # Not a source file

    def test_get_test_files(self):
        """Test getting test files including fixtures and helpers."""
        # Create test files
        (self.temp_path / "tests" / "test_module.py").write_text("def test_something(): pass")
        (self.temp_path / "tests" / "conftest.py").write_text("import pytest")
        (self.temp_path / "tests" / "helpers").mkdir()  # Create subdirectory first
        (self.temp_path / "tests" / "helpers" / "test_utils.py").write_text("def helper(): pass")
        (self.temp_path / "tests" / "unit").mkdir()  # Create subdirectory first
        (self.temp_path / "tests" / "unit" / "test_unit.py").write_text("def test_unit(): pass")
        (self.temp_path / "src" / "module.py").write_text("def func(): pass")  # Not a test file

        test_files = self.manager._get_test_files()
        test_paths = [str(f.relative_to(self.temp_path)) for f in test_files]

        assert "tests/test_module.py" in test_paths
        assert "tests/conftest.py" in test_paths
        assert "tests/helpers/test_utils.py" in test_paths
        assert "tests/unit/test_unit.py" in test_paths
        assert "src/module.py" not in test_paths  # Not a test file

    def test_has_source_changes_no_cache(self):
        """Test source change detection when no cache exists."""
        # No cache means changes detected
        assert self.manager._has_source_changes() is True

    def test_has_source_changes_no_changes(self):
        """Test source change detection when no changes exist."""
        # Set up cache with current file hashes
        (self.temp_path / "src" / "test.py").write_text("print('test')")

        # Update cache with current state
        source_files = self.manager._get_source_files()
        file_hashes = {}
        for file_path in source_files:
            file_hash = self.manager._get_file_hash(file_path)
            if file_hash:
                file_hashes[str(file_path.relative_to(self.temp_path))] = file_hash

        self.manager.cache["last_full_run"] = "2025-01-01T12:00:00"
        self.manager.cache["file_hashes"] = file_hashes

        assert self.manager._has_source_changes() is False

    def test_has_source_changes_file_modified(self):
        """Test source change detection when file is modified."""
        test_file = self.temp_path / "src" / "test.py"
        test_file.write_text("print('original')")

        # Set up cache with original content
        source_files = self.manager._get_source_files()
        file_hashes = {}
        for file_path in source_files:
            file_hash = self.manager._get_file_hash(file_path)
            if file_hash:
                file_hashes[str(file_path.relative_to(self.temp_path))] = file_hash

        self.manager.cache["last_full_run"] = "2025-01-01T12:00:00"
        self.manager.cache["file_hashes"] = file_hashes

        # Modify file
        test_file.write_text("print('modified')")

        assert self.manager._has_source_changes() is True

    def test_has_test_changes_no_cache(self):
        """Test test change detection when no cache exists."""
        assert self.manager._has_test_changes() is True

    def test_has_test_changes_no_changes(self):
        """Test test change detection when no changes exist."""
        # Set up cache with current test file hashes
        (self.temp_path / "tests" / "test_file.py").write_text("def test_something(): pass")

        # Update cache with current state
        test_files = self.manager._get_test_files()
        test_file_hashes = {}
        for file_path in test_files:
            file_hash = self.manager._get_file_hash(file_path)
            if file_hash:
                test_file_hashes[str(file_path.relative_to(self.temp_path))] = file_hash

        self.manager.cache["last_full_run"] = "2025-01-01T12:00:00"
        self.manager.cache["test_file_hashes"] = test_file_hashes

        assert self.manager._has_test_changes() is False

    def test_has_test_changes_file_modified(self):
        """Test test change detection when test file is modified."""
        test_file = self.temp_path / "tests" / "test_file.py"
        test_file.write_text("def test_original(): pass")

        # Set up cache with original content
        test_files = self.manager._get_test_files()
        test_file_hashes = {}
        for file_path in test_files:
            file_hash = self.manager._get_file_hash(file_path)
            if file_hash:
                test_file_hashes[str(file_path.relative_to(self.temp_path))] = file_hash

        self.manager.cache["last_full_run"] = "2025-01-01T12:00:00"
        self.manager.cache["test_file_hashes"] = test_file_hashes

        # Modify test file
        test_file.write_text("def test_modified(): pass")

        assert self.manager._has_test_changes() is True

    @patch("subprocess.Popen")
    def test_run_coverage_tests_success(self, mock_popen):
        """Test running coverage tests successfully."""
        # Mock successful test run
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_process.stdout.readline.side_effect = [
            "test_module.py::test_function PASSED [50%]",
            "test_module.py::test_another PASSED [100%]",
            "TOTAL 2 passed in 0.01s",
            "TOTAL 85.5%",
        ]
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process

        success, test_count, coverage_percentage = self.manager._run_coverage_tests()

        assert success is True
        assert test_count == 2
        assert coverage_percentage == 85.5

    @patch("subprocess.Popen")
    def test_run_coverage_tests_failure(self, mock_popen):
        """Test running coverage tests with failure."""
        # Mock failed test run
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_process.stdout.readline.side_effect = [
            "test_module.py::test_function FAILED [50%]",
            "test_module.py::test_another FAILED [100%]",
            "TOTAL 2 failed in 0.01s",
        ]
        mock_process.wait.return_value = 1
        mock_popen.return_value = mock_process

        success, test_count, coverage_percentage = self.manager._run_coverage_tests()

        assert success is False
        assert test_count == 2
        assert coverage_percentage == 0

    def test_update_cache(self):
        """Test updating cache with new coverage data."""
        # Create test files
        (self.temp_path / "src" / "test.py").write_text("print('test')")
        (self.temp_path / "tests" / "test_file.py").write_text("def test_something(): pass")

        success = True
        test_count = 150
        coverage_percentage = 85.5

        self.manager._update_cache(success, test_count, coverage_percentage)

        assert self.manager.cache["last_full_run"] is not None
        assert self.manager.cache["coverage_percentage"] == 85.5
        assert self.manager.cache["test_count"] == 150
        assert self.manager.cache["success"] is True
        assert "file_hashes" in self.manager.cache
        assert "test_file_hashes" in self.manager.cache

    def test_check_if_full_test_needed(self):
        """Test checking if full test run is needed."""
        # Test with no cache (should NOT need full run in local smart-test mode)
        assert self.manager.check_if_full_test_needed() is False

        # Test with no changes
        self.manager.cache["last_full_run"] = "2025-01-01T12:00:00"
        self.manager.cache["file_hashes"] = {}
        self.manager.cache["test_file_hashes"] = {}

        with (
            patch.object(self.manager, "_has_source_changes", return_value=False),
            patch.object(self.manager, "_has_test_changes", return_value=False),
        ):
            assert self.manager.check_if_full_test_needed() is False

    def test_get_status(self):
        """Test getting coverage status."""
        # Set up test cache
        self.manager.cache = {
            "last_full_run": "2025-01-01T12:00:00",
            "coverage_percentage": 85.5,
            "test_count": 150,
        }

        with (
            patch.object(self.manager, "_has_source_changes", return_value=True),
            patch.object(self.manager, "_has_test_changes", return_value=False),
            patch.object(self.manager, "check_if_full_test_needed", return_value=True),
        ):
            status = self.manager.get_status()

            assert status["last_run"] == "2025-01-01T12:00:00"
            assert status["coverage_percentage"] == 85.5
            assert status["test_count"] == 150
            assert status["source_changed"] is True
            assert status["test_changed"] is False
            assert status["needs_full_run"] is True

    def test_get_recent_logs(self):
        """Test getting recent log files."""
        # Create test log files
        logs_dir = self.temp_path / "logs" / "tests"
        log1 = logs_dir / "test_run_20250101_120000.log"
        log2 = logs_dir / "test_run_20250101_130000.log"
        log3 = logs_dir / "test_run_20250101_140000.log"

        # Create files with small delays to ensure different modification times
        import time

        log1.write_text("test log 1")
        time.sleep(0.01)  # Small delay to ensure different mtime
        log2.write_text("test log 2")
        time.sleep(0.01)  # Small delay to ensure different mtime
        log3.write_text("test log 3")

        recent_logs = self.manager.get_recent_logs(2)

        assert len(recent_logs) == 2
        # Should be sorted by modification time (most recent first)
        # Since we created them sequentially with delays, the last created should be first
        assert recent_logs[0].name == "test_run_20250101_140000.log"
        assert recent_logs[1].name == "test_run_20250101_130000.log"

    def test_show_recent_logs(self, capsys):
        """Test showing recent log files."""
        # Create test log files
        logs_dir = self.temp_path / "logs" / "tests"
        log1 = logs_dir / "test_run_20250101_120000.log"
        log2 = logs_dir / "test_run_20250101_130000.log"

        log1.write_text("Test Run Completed: 2025-01-01T12:00:00\nExit Code: 0")
        log2.write_text("Test Run Completed: 2025-01-01T13:00:00\nExit Code: 1")

        self.manager.show_recent_logs(2)

        captured = capsys.readouterr()
        assert "Recent test logs" in captured.out
        assert "test_run_20250101_130000.log" in captured.out
        assert "test_run_20250101_120000.log" in captured.out

    def test_show_latest_log(self, capsys):
        """Test showing latest log content."""
        # Create test log file
        logs_dir = self.temp_path / "logs" / "tests"
        log_file = logs_dir / "test_run_20250101_120000.log"
        log_content = (
            "Test Run Started: 2025-01-01T12:00:00\n"
            + "=" * 80
            + "\n"
            + "Test output line 1\n"
            + "Test output line 2\n"
            + "=" * 80
            + "\n"
            + "Test Run Completed: 2025-01-01T12:00:00\nExit Code: 0"
        )
        log_file.write_text(log_content)

        self.manager.show_latest_log()

        captured = capsys.readouterr()
        assert "Latest test log" in captured.out
        assert "Test output line 1" in captured.out
        assert "Test output line 2" in captured.out

    @patch.object(SmartCoverageManager, "_run_changed_only")
    def test_run_smart_tests_with_changes(self, mock_changed_only):
        """Test running smart tests when changes are detected (changed-only mode)."""
        mock_changed_only.return_value = True

        with (
            patch.object(self.manager, "_has_source_changes", return_value=True),
            patch.object(self.manager, "_has_test_changes", return_value=False),
            patch.object(self.manager, "_has_config_changes", return_value=False),
        ):
            result = self.manager.run_smart_tests()

        assert result is True
        mock_changed_only.assert_called_once()

    @patch.object(SmartCoverageManager, "_run_coverage_tests")
    def test_run_smart_tests_no_changes(self, mock_run_tests):
        """Test running smart tests when no changes are detected."""
        # Set up cache with success status
        self.manager.cache["success"] = True
        self.manager.cache["test_count"] = 150
        self.manager.cache["coverage_percentage"] = 85.5

        with (
            patch.object(self.manager, "_has_source_changes", return_value=False),
            patch.object(self.manager, "_has_test_changes", return_value=False),
            patch.object(self.manager, "_has_config_changes", return_value=False),
            patch.object(self.manager, "get_status") as mock_get_status,
        ):
            mock_get_status.return_value = {
                "test_count": 150,
                "coverage_percentage": 85.5,
                "success": True,
            }
            result = self.manager.run_smart_tests()

        assert result is True
        mock_run_tests.assert_not_called()

    @patch.object(SmartCoverageManager, "_run_coverage_tests")
    def test_force_full_run(self, mock_run_tests):
        """Test forcing a full test run."""
        mock_run_tests.return_value = (True, 150, 85.5)

        result = self.manager.force_full_run()

        assert result is True
        mock_run_tests.assert_called_once()

    def test_get_coverage_threshold_from_env(self):
        """Test getting coverage threshold from environment variable."""
        with patch.dict(os.environ, {"COVERAGE_THRESHOLD": "90.5"}):
            threshold = self.manager._get_coverage_threshold()
            assert threshold == 90.5

    def test_get_coverage_threshold_invalid_env(self, capsys):
        """Test handling invalid environment variable."""
        with patch.dict(os.environ, {"COVERAGE_THRESHOLD": "invalid"}):
            threshold = self.manager._get_coverage_threshold()
            assert threshold == 80.0  # Should fallback to default

            captured = capsys.readouterr()
            assert "Invalid COVERAGE_THRESHOLD environment variable" in captured.out

    def test_get_coverage_threshold_from_pyproject(self):
        """Test getting coverage threshold from pyproject.toml."""
        # Create a mock pyproject.toml
        pyproject_content = """
[tool.coverage.report]
fail_under = 85.0
"""
        pyproject_path = self.temp_path / "pyproject.toml"
        pyproject_path.write_text(pyproject_content)

        # Create new manager to test pyproject reading
        manager = SmartCoverageManager(str(self.temp_path))
        threshold = manager._get_coverage_threshold()
        assert threshold == 85.0

    def test_get_coverage_threshold_pyproject_invalid_toml(self, capsys):
        """Test handling invalid TOML in pyproject.toml."""
        # Create invalid TOML
        pyproject_path = self.temp_path / "pyproject.toml"
        pyproject_path.write_text("invalid toml content [")

        # Create new manager to test pyproject reading
        manager = SmartCoverageManager(str(self.temp_path))
        threshold = manager._get_coverage_threshold()
        assert threshold == 80.0  # Should fallback to default

        captured = capsys.readouterr()
        assert "Could not read coverage threshold from pyproject.toml" in captured.out

    def test_get_coverage_threshold_pyproject_missing_section(self):
        """Test handling missing coverage section in pyproject.toml."""
        # Create pyproject.toml without coverage section
        pyproject_content = """
[build-system]
requires = ["hatchling"]
"""
        pyproject_path = self.temp_path / "pyproject.toml"
        pyproject_path.write_text(pyproject_content)

        # Create new manager to test pyproject reading
        manager = SmartCoverageManager(str(self.temp_path))
        threshold = manager._get_coverage_threshold()
        assert threshold == 80.0  # Should fallback to default

    def test_get_coverage_threshold_pyproject_missing_fail_under(self):
        """Test handling missing fail_under in pyproject.toml."""
        # Create pyproject.toml with coverage section but no fail_under
        pyproject_content = """
[tool.coverage.report]
show_missing = true
"""
        pyproject_path = self.temp_path / "pyproject.toml"
        pyproject_path.write_text(pyproject_content)

        # Create new manager to test pyproject reading
        manager = SmartCoverageManager(str(self.temp_path))
        threshold = manager._get_coverage_threshold()
        assert threshold == 80.0  # Should fallback to default

    def test_check_coverage_threshold_success(self):
        """Test coverage threshold check when coverage meets threshold."""
        # Should not raise exception
        self.manager._check_coverage_threshold(85.0)

    def test_check_coverage_threshold_failure(self):
        """Test coverage threshold check when coverage is below threshold."""
        with pytest.raises(Exception) as exc_info:
            self.manager._check_coverage_threshold(75.0)

        assert "Coverage 75.0% is below required threshold" in str(exc_info.value)
        assert "Please add more tests" in str(exc_info.value)

    @patch("subprocess.Popen")
    def test_run_coverage_tests_timeout(self, mock_popen):
        """Test running coverage tests with timeout."""
        # Mock timeout exception
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_process.stdout.readline.side_effect = []
        mock_process.wait.side_effect = subprocess.TimeoutExpired("hatch", 600)
        mock_popen.return_value = mock_process

        success, test_count, coverage_percentage = self.manager._run_coverage_tests()

        assert success is False
        assert test_count == 0
        assert coverage_percentage == 0

    @patch("subprocess.Popen")
    def test_run_coverage_tests_exception(self, mock_popen):
        """Test running coverage tests with general exception."""
        # Mock general exception
        mock_popen.side_effect = Exception("Test exception")

        success, test_count, coverage_percentage = self.manager._run_coverage_tests()

        assert success is False
        assert test_count == 0
        assert coverage_percentage == 0

    def test_update_cache_with_threshold_error(self):
        """Test update cache when coverage threshold is not met."""
        # Set a high threshold
        self.manager.coverage_threshold = 90.0

        # Try to update with low coverage
        with pytest.raises(Exception) as exc_info:
            self.manager._update_cache(True, 100, 75.0)

        assert "Coverage 75.0% is below required threshold" in str(exc_info.value)

    def test_show_recent_logs_no_logs(self, capsys):
        """Test showing recent logs when no logs exist."""
        # Remove logs directory
        logs_dir = self.temp_path / "logs" / "tests"
        if logs_dir.exists():
            shutil.rmtree(logs_dir)

        self.manager.show_recent_logs()

        captured = capsys.readouterr()
        assert "No test logs found" in captured.out

    def test_show_latest_log_no_logs(self, capsys):
        """Test showing latest log when no logs exist."""
        # Remove logs directory
        logs_dir = self.temp_path / "logs" / "tests"
        if logs_dir.exists():
            shutil.rmtree(logs_dir)

        self.manager.show_latest_log()

        captured = capsys.readouterr()
        assert "No test logs found" in captured.out

    def test_show_latest_log_read_error(self, capsys):
        """Test showing latest log with read error."""
        # Create a log file that will cause read error
        logs_dir = self.temp_path / "logs" / "tests"
        log_file = logs_dir / "test_run_20250101_120000.log"

        # Create a file that can't be read (simulate permission error)
        log_file.write_text("test content")
        log_file.chmod(0o000)  # Remove read permission

        try:
            self.manager.show_latest_log()

            captured = capsys.readouterr()
            assert "Error reading log file" in captured.out
        finally:
            # Restore permissions for cleanup
            log_file.chmod(0o644)

    def test_show_recent_logs_with_status_detection(self, capsys):
        """Test showing recent logs with status detection."""
        # Create test log files with different statuses
        logs_dir = self.temp_path / "logs" / "tests"
        log1 = logs_dir / "test_run_20250101_120000.log"
        log2 = logs_dir / "test_run_20250101_130000.log"
        log3 = logs_dir / "test_run_20250101_140000.log"

        # Log with success
        log1.write_text("Test Run Started: 2025-01-01T12:00:00\nTest output\nExit Code: 0")
        # Log with failure
        log2.write_text("Test Run Started: 2025-01-01T13:00:00\nTest output\nExit Code: 1")
        # Log with unknown status
        log3.write_text("Test Run Started: 2025-01-01T14:00:00\nTest output")

        self.manager.show_recent_logs(3)

        captured = capsys.readouterr()
        assert "Recent test logs" in captured.out
        assert "✅ Passed" in captured.out
        assert "❌ Failed" in captured.out
        assert "❓ Unknown" in captured.out

    def test_should_exclude_file(self):
        """Test file exclusion logic."""
        # Test markdown files
        assert self.manager._should_exclude_file(Path("docs/README.md")) is True
        assert self.manager._should_exclude_file(Path("docs/guide.rst")) is True

        # Test image files
        assert self.manager._should_exclude_file(Path("images/logo.png")) is True
        assert self.manager._should_exclude_file(Path("assets/icon.svg")) is True

        # Test log files
        assert self.manager._should_exclude_file(Path("logs/test.log")) is True
        assert self.manager._should_exclude_file(Path("temp.cache")) is True

        # Test Python files (should not be excluded)
        assert self.manager._should_exclude_file(Path("src/module.py")) is False
        assert self.manager._should_exclude_file(Path("tools/script.py")) is False
        assert self.manager._should_exclude_file(Path("tests/test_module.py")) is False

        # Test directories
        assert self.manager._should_exclude_file(Path("docs")) is True
        assert self.manager._should_exclude_file(Path("papers")) is True
        assert self.manager._should_exclude_file(Path("images")) is True

        # Test cache directories
        assert self.manager._should_exclude_file(Path(".coverage_cache")) is True
        assert self.manager._should_exclude_file(Path("__pycache__")) is True

    def test_is_config_file(self):
        """Test configuration file detection."""
        # Test configuration files
        assert self.manager._is_config_file(Path("pyproject.toml")) is True
        assert self.manager._is_config_file(Path("setup.py")) is True
        assert self.manager._is_config_file(Path("requirements.txt")) is True
        assert self.manager._is_config_file(Path("pytest.ini")) is True
        assert self.manager._is_config_file(Path("conftest.py")) is True

        # Test non-configuration files
        assert self.manager._is_config_file(Path("src/module.py")) is False
        assert self.manager._is_config_file(Path("tests/test_module.py")) is False
        assert self.manager._is_config_file(Path("README.md")) is False

    def test_get_config_files(self):
        """Test getting configuration files."""
        # Create some configuration files
        (self.temp_path / "pyproject.toml").write_text("[project]\nname = 'test'")
        (self.temp_path / "setup.py").write_text("from setuptools import setup")
        (self.temp_path / "requirements.txt").write_text("pytest>=6.0")
        (self.temp_path / "pytest.ini").write_text("[pytest]")
        (self.temp_path / "conftest.py").write_text("import pytest")

        # Create non-config files
        (self.temp_path / "README.md").write_text("# Test")
        (self.temp_path / "src" / "module.py").write_text("def func(): pass")

        config_files = self.manager._get_config_files()
        config_paths = [str(f.relative_to(self.temp_path)) for f in config_files]

        assert "pyproject.toml" in config_paths
        assert "setup.py" in config_paths
        assert "requirements.txt" in config_paths
        assert "pytest.ini" in config_paths
        assert "conftest.py" in config_paths
        assert "README.md" not in config_paths
        assert "src/module.py" not in config_paths

    def test_has_config_changes_no_cache(self):
        """Test config change detection when no cache exists."""
        assert self.manager._has_config_changes() is True

    def test_has_config_changes_no_changes(self):
        """Test config change detection when no changes exist."""
        # Create configuration file
        (self.temp_path / "pyproject.toml").write_text("[project]\nname = 'test'")

        # Set up cache with current config file hashes
        config_files = self.manager._get_config_files()
        config_file_hashes = {}
        for file_path in config_files:
            file_hash = self.manager._get_file_hash(file_path)
            if file_hash:
                config_file_hashes[str(file_path.relative_to(self.temp_path))] = file_hash

        self.manager.cache["last_full_run"] = "2025-01-01T12:00:00"
        self.manager.cache["config_file_hashes"] = config_file_hashes

        assert self.manager._has_config_changes() is False

    def test_has_config_changes_file_modified(self):
        """Test config change detection when config file is modified."""
        config_file = self.temp_path / "pyproject.toml"
        config_file.write_text("[project]\nname = 'original'")

        # Set up cache with original content
        config_files = self.manager._get_config_files()
        config_file_hashes = {}
        for file_path in config_files:
            file_hash = self.manager._get_file_hash(file_path)
            if file_hash:
                config_file_hashes[str(file_path.relative_to(self.temp_path))] = file_hash

        self.manager.cache["last_full_run"] = "2025-01-01T12:00:00"
        self.manager.cache["config_file_hashes"] = config_file_hashes

        # Modify config file
        config_file.write_text("[project]\nname = 'modified'")

        assert self.manager._has_config_changes() is True

    def test_get_source_files_excludes_documentation(self):
        """Test that source file detection excludes documentation files."""
        # Create source files
        (self.temp_path / "src" / "module.py").write_text("def func(): pass")
        (self.temp_path / "tools" / "script.py").write_text("def main(): pass")

        # Create documentation files in source directories (should be excluded)
        (self.temp_path / "src" / "README.md").write_text("# Module docs")
        (self.temp_path / "src" / "docs").mkdir()  # Create directory first
        (self.temp_path / "src" / "docs" / "guide.md").write_text("# Guide")
        (self.temp_path / "tools" / "help.txt").write_text("Help text")

        source_files = self.manager._get_source_files()
        source_paths = [str(f.relative_to(self.temp_path)) for f in source_files]

        # Should include Python files
        assert "src/module.py" in source_paths
        assert "tools/script.py" in source_paths

        # Should exclude documentation files
        assert "src/README.md" not in source_paths
        assert "src/docs/guide.md" not in source_paths
        assert "tools/help.txt" not in source_paths

    def test_get_test_files_excludes_documentation(self):
        """Test that test file detection excludes documentation files."""
        # Create test files
        (self.temp_path / "tests" / "test_module.py").write_text("def test_func(): pass")
        (self.temp_path / "tests" / "conftest.py").write_text("import pytest")

        # Create documentation files in test directories (should be excluded)
        (self.temp_path / "tests" / "README.md").write_text("# Test docs")
        (self.temp_path / "tests" / "docs").mkdir()  # Create directory first
        (self.temp_path / "tests" / "docs" / "guide.md").write_text("# Test guide")

        test_files = self.manager._get_test_files()
        test_paths = [str(f.relative_to(self.temp_path)) for f in test_files]

        # Should include Python files
        assert "tests/test_module.py" in test_paths
        assert "tests/conftest.py" in test_paths

        # Should exclude documentation files
        assert "tests/README.md" not in test_paths
        assert "tests/docs/guide.md" not in test_paths

    def test_check_if_full_test_needed_includes_config_changes(self):
        """Test that config changes do not trigger full test runs in local smart-test mode."""
        # Test with config changes
        with (
            patch.object(self.manager, "_has_source_changes", return_value=False),
            patch.object(self.manager, "_has_test_changes", return_value=False),
            patch.object(self.manager, "_has_config_changes", return_value=True),
        ):
            assert self.manager.check_if_full_test_needed() is False

    def test_get_status_includes_config_changes(self):
        """Test that status includes config change information."""
        with (
            patch.object(self.manager, "_has_source_changes", return_value=True),
            patch.object(self.manager, "_has_test_changes", return_value=False),
            patch.object(self.manager, "_has_config_changes", return_value=True),
            patch.object(self.manager, "check_if_full_test_needed", return_value=True),
        ):
            status = self.manager.get_status()

            assert status["source_changed"] is True
            assert status["test_changed"] is False
            assert status["config_changed"] is True
            assert status["needs_full_run"] is True

    def test_update_cache_includes_config_hashes(self):
        """Test that cache update includes configuration file hashes."""
        # Create test files
        (self.temp_path / "src" / "test.py").write_text("print('test')")
        (self.temp_path / "tests" / "test_file.py").write_text("def test_something(): pass")
        (self.temp_path / "pyproject.toml").write_text("[project]\nname = 'test'")

        success = True
        test_count = 150
        coverage_percentage = 85.5

        self.manager._update_cache(success, test_count, coverage_percentage)

        assert self.manager.cache["last_full_run"] is not None
        assert self.manager.cache["coverage_percentage"] == 85.5
        assert self.manager.cache["test_count"] == 150
        assert self.manager.cache["success"] is True
        assert "file_hashes" in self.manager.cache
        assert "test_file_hashes" in self.manager.cache
        assert "config_file_hashes" in self.manager.cache

    def test_calculate_tested_coverage_no_test_files(self):
        """Test tested coverage calculation with no test files."""
        output_lines = [
            "Name                                                   Stmts   Miss Branch BrPart  Cover   Missing",
            "--------------------------------------------------------------------------------------------------",
            "tools/smart_test_coverage.py                             100     20     10      2    80%   1-10",
            "--------------------------------------------------------------------------------------------------",
            "TOTAL                                                  100     20     10      2    80%",
        ]

        tested_coverage = self.manager._calculate_tested_coverage([], output_lines)
        assert tested_coverage == 0.0

    def test_calculate_tested_coverage_tools_files(self):
        """Test tested coverage calculation for tools files."""
        # Create test files and corresponding source files
        test_file = self.temp_path / "tests" / "unit" / "tools" / "test_smart_test_coverage.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("def test_something(): pass")

        # Create the corresponding source file
        source_file = self.temp_path / "tools" / "smart_test_coverage.py"
        source_file.write_text("def some_function(): pass")

        output_lines = [
            "Name                                                   Stmts   Miss Branch BrPart  Cover   Missing",
            "--------------------------------------------------------------------------------------------------",
            "tools/smart_test_coverage.py                             100     20     10      2    80%   1-10",
            "tools/other_tool.py                                      50     10      5      1    80%   1-5",
            "src/common/logger_setup.py                               200     40     20      4    80%   1-20",
            "--------------------------------------------------------------------------------------------------",
            "TOTAL                                                  350     70     35      7    80%",
        ]

        tested_coverage = self.manager._calculate_tested_coverage([test_file], output_lines)
        # Should only count tools/smart_test_coverage.py (100 statements, 20 missed = 80% coverage)
        assert tested_coverage == 80.0

    def test_calculate_tested_coverage_src_files(self):
        """Test tested coverage calculation for src files."""
        # Create test files and corresponding source files
        test_file = self.temp_path / "tests" / "unit" / "common" / "test_logger_setup.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("def test_something(): pass")

        # Create the corresponding source file
        source_file = self.temp_path / "src" / "common" / "logger_setup.py"
        source_file.parent.mkdir(parents=True)
        source_file.write_text("def get_logger(): pass")

        output_lines = [
            "Name                                                   Stmts   Miss Branch BrPart  Cover   Missing",
            "--------------------------------------------------------------------------------------------------",
            "src/common/logger_setup.py                               200     40     20      4    80%   1-20",
            "src/common/redis_client.py                               150     30     15      3    80%   1-15",
            "tools/smart_test_coverage.py                             100     20     10      2    80%   1-10",
            "--------------------------------------------------------------------------------------------------",
            "TOTAL                                                  450     90     45      9    80%",
        ]

        tested_coverage = self.manager._calculate_tested_coverage([test_file], output_lines)
        # Should only count src/common/logger_setup.py (200 statements, 40 missed = 80% coverage)
        assert tested_coverage == 80.0

    def test_calculate_tested_coverage_multiple_files(self):
        """Test tested coverage calculation for multiple files."""
        # Create test files and corresponding source files
        test_file1 = self.temp_path / "tests" / "unit" / "tools" / "test_smart_test_coverage.py"
        test_file2 = self.temp_path / "tests" / "unit" / "common" / "test_logger_setup.py"
        test_file1.parent.mkdir(parents=True)
        test_file2.parent.mkdir(parents=True)
        test_file1.write_text("def test_something(): pass")
        test_file2.write_text("def test_something(): pass")

        # Create the corresponding source files
        source_file1 = self.temp_path / "tools" / "smart_test_coverage.py"
        source_file2 = self.temp_path / "src" / "common" / "logger_setup.py"
        source_file2.parent.mkdir(parents=True)
        source_file1.write_text("def some_function(): pass")
        source_file2.write_text("def get_logger(): pass")

        output_lines = [
            "Name                                                   Stmts   Miss Branch BrPart  Cover   Missing",
            "--------------------------------------------------------------------------------------------------",
            "tools/smart_test_coverage.py                             100     20     10      2    80%   1-10",
            "src/common/logger_setup.py                               200     40     20      4    80%   1-20",
            "src/common/redis_client.py                               150     30     15      3    80%   1-15",
            "--------------------------------------------------------------------------------------------------",
            "TOTAL                                                  450     90     45      9    80%",
        ]

        tested_coverage = self.manager._calculate_tested_coverage([test_file1, test_file2], output_lines)
        # Should count both tools/smart_test_coverage.py (100-20=80) and src/common/logger_setup.py (200-40=160)
        # Total: 240 covered out of 300 statements = 80%
        assert tested_coverage == 80.0

    def test_calculate_tested_coverage_no_matching_files(self):
        """Test tested coverage calculation when no files match."""
        # Create test file that doesn't match any coverage output
        test_file = self.temp_path / "tests" / "unit" / "nonexistent" / "test_file.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("def test_something(): pass")

        output_lines = [
            "Name                                                   Stmts   Miss Branch BrPart  Cover   Missing",
            "--------------------------------------------------------------------------------------------------",
            "tools/smart_test_coverage.py                             100     20     10      2    80%   1-10",
            "--------------------------------------------------------------------------------------------------",
            "TOTAL                                                  100     20     10      2    80%",
        ]

        tested_coverage = self.manager._calculate_tested_coverage([test_file], output_lines)
        assert tested_coverage == 0.0

    def test_calculate_tested_coverage_malformed_output(self):
        """Test tested coverage calculation with malformed output."""
        test_file = self.temp_path / "tests" / "unit" / "tools" / "test_smart_test_coverage.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("def test_something(): pass")

        # Malformed output with invalid numbers
        output_lines = [
            "Name                                                   Stmts   Miss Branch BrPart  Cover   Missing",
            "--------------------------------------------------------------------------------------------------",
            "tools/smart_test_coverage.py                             invalid 20     10      2    80%   1-10",
            "--------------------------------------------------------------------------------------------------",
            "TOTAL                                                  100     20     10      2    80%",
        ]

        tested_coverage = self.manager._calculate_tested_coverage([test_file], output_lines)
        assert tested_coverage == 0.0

    def test_calculate_tested_coverage_no_coverage_table(self):
        """Test tested coverage calculation when no coverage table is found."""
        test_file = self.temp_path / "tests" / "unit" / "tools" / "test_smart_test_coverage.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("def test_something(): pass")

        output_lines = [
            "============================= test session starts =============================",
            "test_smart_test_coverage.py::test_something PASSED [100%]",
            "============================= 1 passed in 0.01s =============================",
        ]

        tested_coverage = self.manager._calculate_tested_coverage([test_file], output_lines)
        assert tested_coverage == 0.0

    @patch("subprocess.Popen")
    def test_run_tests_with_tested_coverage_calculation(self, mock_popen):
        """Test _run_tests method with tested coverage calculation for unit/folder tests."""
        # Create test files
        test_file = self.temp_path / "tests" / "unit" / "tools" / "test_smart_test_coverage.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("def test_something(): pass")

        # Mock successful test run with coverage output
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_process.stdout.readline.side_effect = [
            "test_smart_test_coverage.py::test_something PASSED [100%]",
            "1 passed in 0.01s",
            "Name                                                   Stmts   Miss Branch BrPart  Cover   Missing",
            "--------------------------------------------------------------------------------------------------",
            "tools/smart_test_coverage.py                             100     20     10      2    80%   1-10",
            "src/common/logger_setup.py                               200     40     20      4    80%   1-20",
            "--------------------------------------------------------------------------------------------------",
            "TOTAL                                                  300     60     30      6    80%",
            "",
        ]
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process

        success, test_count, coverage_percentage = self.manager._run_tests([test_file], "unit")

        assert success is True
        assert test_count == 1
        assert coverage_percentage == 80.0  # Overall coverage

    @patch("subprocess.Popen")
    def test_run_tests_coverage_threshold_failure_handling(self, mock_popen):
        """Test _run_tests method handling coverage threshold failures for unit/folder tests."""
        # Create test files
        test_file = self.temp_path / "tests" / "unit" / "tools" / "test_smart_test_coverage.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("def test_something(): pass")

        # Mock test run that fails due to coverage threshold but tests pass
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_process.stdout.readline.side_effect = [
            "test_smart_test_coverage.py::test_something PASSED [100%]",
            "1 passed in 0.01s",
            "Name                                                   Stmts   Miss Branch BrPart  Cover   Missing",
            "--------------------------------------------------------------------------------------------------",
            "tools/smart_test_coverage.py                             100     20     10      2    80%   1-10",
            "--------------------------------------------------------------------------------------------------",
            "TOTAL                                                  100     20     10      2    80%",
            "Coverage failure: total of 80 is less than fail-under=85",
            "",
        ]
        mock_process.wait.return_value = 2  # Coverage threshold failure
        mock_popen.return_value = mock_process

        success, test_count, coverage_percentage = self.manager._run_tests([test_file], "unit")

        # Should succeed for unit tests even with coverage threshold failure
        assert success is True
        assert test_count == 1
        assert coverage_percentage == 80.0

    @patch("subprocess.Popen")
    def test_run_tests_full_test_coverage_threshold_enforcement(self, mock_popen):
        """Test _run_tests method enforces coverage threshold for full tests."""
        # Create test files
        test_file = self.temp_path / "tests" / "unit" / "tools" / "test_smart_test_coverage.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("def test_something(): pass")

        # Mock test run that fails due to coverage threshold
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_process.stdout.readline.side_effect = [
            "test_smart_test_coverage.py::test_something PASSED [100%]",
            "1 passed in 0.01s",
            "Name                                                   Stmts   Miss Branch BrPart  Cover   Missing",
            "--------------------------------------------------------------------------------------------------",
            "tools/smart_test_coverage.py                             100     20     10      2    80%   1-10",
            "--------------------------------------------------------------------------------------------------",
            "TOTAL                                                  100     20     10      2    80%",
            "Coverage failure: total of 80 is less than fail-under=85",
            "",
        ]
        mock_process.wait.return_value = 2  # Coverage threshold failure
        mock_popen.return_value = mock_process

        success, test_count, coverage_percentage = self.manager._run_tests([test_file], "full")

        # Should fail for full tests with coverage threshold failure
        assert success is False
        assert test_count == 1
        assert coverage_percentage == 80.0


class TestMainFunction:
    """Test cases for the main function and CLI interface."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Create test directory structure
        (self.temp_path / "src").mkdir()
        (self.temp_path / "tools").mkdir()
        (self.temp_path / "tests").mkdir()
        (self.temp_path / "logs" / "tests").mkdir(parents=True)

    def teardown_method(self):
        """Clean up after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("sys.argv", ["smart_test_coverage.py", "status"])
    @patch("tools.smart_test_coverage.SmartCoverageManager")
    def test_main_status_command(self, mock_manager_class):
        """Test main function with status command."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.coverage_threshold = 80.0
        mock_manager.get_status.return_value = {
            "last_run": "2025-01-01T12:00:00",
            "coverage_percentage": 85.5,
            "test_count": 150,
            "source_changed": False,
            "test_changed": False,
            "config_changed": False,
            "needs_full_run": False,
        }

        with patch("tools.smart_test_coverage.sys.exit") as mock_exit:
            from tools.smart_test_coverage import main

            main()

        mock_manager.get_status.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch("sys.argv", ["smart_test_coverage.py", "check"])
    @patch("tools.smart_test_coverage.SmartCoverageManager")
    def test_main_check_command(self, mock_manager_class):
        """Test main function with check command."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.check_if_full_test_needed.return_value = True

        with patch("tools.smart_test_coverage.sys.exit") as mock_exit:
            from tools.smart_test_coverage import main

            main()

        mock_manager.check_if_full_test_needed.assert_called_once()
        mock_exit.assert_called_once_with(1)  # Exit code 1 when full test needed

    @patch("sys.argv", ["smart_test_coverage.py", "run"])
    @patch("tools.smart_test_coverage.SmartCoverageManager")
    def test_main_run_command(self, mock_manager_class):
        """Test main function with run command."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.run_smart_tests.return_value = True

        with patch("tools.smart_test_coverage.sys.exit") as mock_exit:
            from tools.smart_test_coverage import main

            main()

        mock_manager.run_smart_tests.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch("sys.argv", ["smart_test_coverage.py", "force"])
    @patch("tools.smart_test_coverage.SmartCoverageManager")
    def test_main_force_command(self, mock_manager_class):
        """Test main function with force command."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.run_smart_tests.return_value = True

        with patch("tools.smart_test_coverage.sys.exit") as mock_exit:
            from tools.smart_test_coverage import main

            main()

        mock_manager.run_smart_tests.assert_called_once_with("auto", force=True)
        mock_exit.assert_called_once_with(0)

    @patch("sys.argv", ["smart_test_coverage.py", "logs", "3"])
    @patch("tools.smart_test_coverage.SmartCoverageManager")
    def test_main_logs_command(self, mock_manager_class):
        """Test main function with logs command."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        with patch("tools.smart_test_coverage.sys.exit") as mock_exit:
            from tools.smart_test_coverage import main

            main()

        mock_manager.show_recent_logs.assert_called_once_with(3)
        # The logs command calls sys.exit(0) at the end
        mock_exit.assert_called_with(0)

    @patch("sys.argv", ["smart_test_coverage.py", "latest"])
    @patch("tools.smart_test_coverage.SmartCoverageManager")
    def test_main_latest_command(self, mock_manager_class):
        """Test main function with latest command."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        with patch("tools.smart_test_coverage.sys.exit") as mock_exit:
            from tools.smart_test_coverage import main

            main()

        mock_manager.show_latest_log.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch("sys.argv", ["smart_test_coverage.py"])
    def test_main_no_arguments(self, capsys):
        """Test main function with no arguments."""
        with patch("tools.smart_test_coverage.sys.exit", side_effect=SystemExit(2)) as mock_exit:
            from tools.smart_test_coverage import main

            with contextlib.suppress(SystemExit):
                main()  # Expected behavior

        captured = capsys.readouterr()
        # The error message is now in stderr, not stdout
        assert "the following arguments are required: command" in captured.err
        mock_exit.assert_called_once_with(2)

    @patch("sys.argv", ["smart_test_coverage.py", "unknown_command"])
    def test_main_unknown_command(self, capsys):
        """Test main function with unknown command."""
        with patch("tools.smart_test_coverage.sys.exit", side_effect=SystemExit(2)) as mock_exit:
            from tools.smart_test_coverage import main

            with contextlib.suppress(SystemExit):
                main()  # Expected behavior

        captured = capsys.readouterr()
        # The error message is now in stderr due to argparse
        assert "invalid choice: 'unknown_command'" in captured.err
        mock_exit.assert_called_once_with(2)

    @patch("sys.argv", ["smart_test_coverage.py", "threshold"])
    @patch("tools.smart_test_coverage.SmartCoverageManager")
    def test_main_threshold_command_success(self, mock_manager_class):
        """Test main function with threshold command when coverage meets threshold."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.coverage_threshold = 80.0
        mock_manager.get_status.return_value = {"coverage_percentage": 85.0}

        with patch("tools.smart_test_coverage.sys.exit") as mock_exit:
            from tools.smart_test_coverage import main

            main()

        mock_manager.get_status.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch("sys.argv", ["smart_test_coverage.py", "threshold"])
    @patch("tools.smart_test_coverage.SmartCoverageManager")
    def test_main_threshold_command_failure(self, mock_manager_class):
        """Test main function with threshold command when coverage is below threshold."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.coverage_threshold = 80.0
        mock_manager.get_status.return_value = {"coverage_percentage": 75.0}

        with patch("tools.smart_test_coverage.sys.exit") as mock_exit:
            from tools.smart_test_coverage import main

            main()

        mock_manager.get_status.assert_called_once()
        mock_exit.assert_called_once_with(1)

    @patch("sys.argv", ["smart_test_coverage.py", "threshold"])
    @patch("tools.smart_test_coverage.SmartCoverageManager")
    def test_main_threshold_command_output(self, mock_manager_class, capsys):
        """Test main function with threshold command output."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.coverage_threshold = 80.0
        mock_manager.get_status.return_value = {"coverage_percentage": 85.0}

        with patch("tools.smart_test_coverage.sys.exit", side_effect=SystemExit(0)):
            from tools.smart_test_coverage import main

            with contextlib.suppress(SystemExit):
                main()

        captured = capsys.readouterr()
        assert "Coverage Threshold Check:" in captured.out
        assert "Current Coverage: 85.0%" in captured.out
        assert "Required Threshold: 80.0%" in captured.out
        assert "✅ Coverage meets threshold!" in captured.out
        assert "Margin: 5.0% above threshold" in captured.out

    @patch("sys.argv", ["smart_test_coverage.py", "threshold"])
    @patch("tools.smart_test_coverage.SmartCoverageManager")
    def test_main_threshold_command_below_threshold_output(self, mock_manager_class, capsys):
        """Test main function with threshold command output when below threshold."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.coverage_threshold = 80.0
        mock_manager.get_status.return_value = {"coverage_percentage": 75.0}

        with patch("tools.smart_test_coverage.sys.exit", side_effect=SystemExit(1)):
            from tools.smart_test_coverage import main

            with contextlib.suppress(SystemExit):
                main()

        captured = capsys.readouterr()
        assert "Coverage Threshold Check:" in captured.out
        assert "Current Coverage: 75.0%" in captured.out
        assert "Required Threshold: 80.0%" in captured.out
        assert "❌ Coverage below threshold!" in captured.out
        assert "Difference: 5.0% needed" in captured.out

    @patch("sys.argv", ["smart_test_coverage.py", "run"])
    @patch("tools.smart_test_coverage.SmartCoverageManager")
    def test_main_run_command_with_threshold_error(self, mock_manager_class, capsys):
        """Test main function with run command when threshold error occurs."""
        from tools.smart_test_coverage import CoverageThresholdError

        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.run_smart_tests.side_effect = CoverageThresholdError(
            "Coverage 75.0% is below required threshold of 80.0%"
        )

        with patch("tools.smart_test_coverage.sys.exit", side_effect=SystemExit(1)):
            from tools.smart_test_coverage import main

            with contextlib.suppress(SystemExit):
                main()

        captured = capsys.readouterr()
        assert "❌ Coverage threshold not met!" in captured.out
        assert "Coverage 75.0% is below required threshold" in captured.out
        assert "💡 To fix this issue:" in captured.out
        assert "Add more unit tests to increase coverage" in captured.out
        assert "Run 'hatch run smart-test-status' to see detailed coverage" in captured.out


if __name__ == "__main__":
    pytest.main([__file__])
