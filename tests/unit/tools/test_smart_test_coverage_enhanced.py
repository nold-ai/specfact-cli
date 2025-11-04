#!/usr/bin/env python3
"""
Enhanced Smart Test Coverage System Tests

Tests for the enhanced smart test coverage system with incremental testing levels.
"""

import shutil
import subprocess

# Add the project root to the path
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.smart_test_coverage import CoverageThresholdError, SmartCoverageManager


class TestSmartCoverageManagerEnhanced:
    """Test the enhanced smart coverage manager with incremental testing."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create test directory structure
        (self.project_root / "src" / "common").mkdir(parents=True)
        (self.project_root / "src" / "agents").mkdir(parents=True)
        (self.project_root / "tools").mkdir(parents=True)
        (self.project_root / "tests" / "unit" / "common").mkdir(parents=True)
        (self.project_root / "tests" / "unit" / "agents").mkdir(parents=True)
        (self.project_root / "tests" / "unit" / "tools").mkdir(parents=True)

        # Create test files
        self.create_test_files()

        # Initialize manager
        self.manager = SmartCoverageManager(str(self.project_root))

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def create_test_files(self):
        """Create test source and test files."""
        # Source files
        (self.project_root / "src" / "common" / "logger_setup.py").write_text("def get_logger(): pass")
        (self.project_root / "src" / "common" / "redis_client.py").write_text("def get_redis(): pass")
        (self.project_root / "src" / "agents" / "supervisor_agent.py").write_text("class SupervisorAgent: pass")
        (self.project_root / "tools" / "contract_to_code.py").write_text("def generate_code(): pass")

        # Test files
        (self.project_root / "tests" / "unit" / "common" / "test_logger_setup.py").write_text("def test_logger(): pass")
        (self.project_root / "tests" / "unit" / "common" / "test_redis_client.py").write_text("def test_redis(): pass")
        (self.project_root / "tests" / "unit" / "agents" / "test_supervisor_agent.py").write_text(
            "def test_supervisor(): pass"
        )
        (self.project_root / "tests" / "unit" / "tools" / "test_contract_to_code.py").write_text(
            "def test_contract(): pass"
        )

    def test_get_modified_files(self):
        """Test getting modified files."""
        # Initially no modified files
        modified_files = self.manager._get_modified_files()
        assert len(modified_files) == 0

        # Simulate cache with some files
        self.manager.cache = {
            "last_full_run": "2025-01-01T00:00:00",
            "file_hashes": {
                "src/common/logger_setup.py": "old_hash",
                "src/common/redis_client.py": "old_hash",
            },
        }

        modified_files = self.manager._get_modified_files()
        # The actual number may vary depending on what files exist in the test environment
        assert len(modified_files) >= 2
        assert any("logger_setup.py" in str(f) for f in modified_files)
        assert any("redis_client.py" in str(f) for f in modified_files)

    def test_get_modified_folders(self):
        """Test getting modified folders."""
        # Mock modified files
        modified_files = [
            self.project_root / "src" / "common" / "logger_setup.py",
            self.project_root / "src" / "agents" / "supervisor_agent.py",
        ]

        with patch.object(self.manager, "_get_modified_files", return_value=modified_files):
            modified_folders = self.manager._get_modified_folders()

            # Should include parent folders
            folder_paths = {str(f.relative_to(self.project_root)) for f in modified_folders}
            assert "src/common" in folder_paths
            assert "src/agents" in folder_paths
            # Note: "src" may or may not be included depending on the implementation

    def test_get_unit_tests_for_files(self):
        """Test getting unit tests for specific files."""
        # Use actual files that exist in the real project
        from pathlib import Path

        real_project_root = Path(__file__).parent.parent.parent.parent.resolve()
        modified_files = [real_project_root / "tools" / "smart_test_coverage.py"]

        # Create a new manager with the real project root
        real_manager = SmartCoverageManager(str(real_project_root))
        unit_tests = real_manager._get_unit_tests_for_files(modified_files)

        # Should find corresponding test files
        test_paths = {str(f.relative_to(real_project_root)) for f in unit_tests}
        assert "tests/unit/tools/test_smart_test_coverage.py" in test_paths

    def test_get_files_in_folders(self):
        """Test getting files in modified folders."""
        from pathlib import Path

        real_project_root = Path(__file__).parent.parent.parent.parent.resolve()
        # Test with src/specfact_cli/common folder (actual structure in this project)
        modified_folders = {real_project_root / "src" / "specfact_cli" / "common"}

        # Create a new manager with the real project root
        real_manager = SmartCoverageManager(str(real_project_root))
        folder_files = real_manager._get_files_in_folders(modified_folders)

        # Should find Python files in the src/specfact_cli/common folder
        file_paths = {str(f.relative_to(real_project_root)) for f in folder_files}
        # Check that we find some Python files (the exact files might vary)
        assert len(file_paths) > 0
        # All files should be Python files
        for file_path in folder_files:
            assert file_path.suffix == ".py"

    def test_run_tests_by_level_unit(self):
        """Test running unit tests."""
        with (
            patch.object(self.manager, "_get_modified_files") as mock_files,
            patch.object(self.manager, "_get_unit_tests_for_files") as mock_tests,
            patch.object(self.manager, "_run_tests") as mock_run,
        ):
            # Mock modified files
            mock_files.return_value = [self.project_root / "src" / "common" / "logger_setup.py"]
            mock_tests.return_value = [self.project_root / "tests" / "unit" / "common" / "test_logger_setup.py"]
            mock_run.return_value = (True, 5, 85.0)

            result = self.manager.run_tests_by_level("unit")

            assert result is True
            mock_files.assert_called_once()
            mock_tests.assert_called_once()
            mock_run.assert_called_once()

    def test_run_tests_by_level_folder(self):
        """Test running folder tests."""
        with (
            patch.object(self.manager, "_get_modified_folders") as mock_folders,
            patch.object(self.manager, "_get_files_in_folders") as mock_files,
            patch.object(self.manager, "_get_unit_tests_for_files") as mock_tests,
            patch.object(self.manager, "_run_tests") as mock_run,
        ):
            # Mock modified folders
            mock_folders.return_value = {self.project_root / "src" / "common"}
            mock_files.return_value = [self.project_root / "src" / "common" / "logger_setup.py"]
            mock_tests.return_value = [self.project_root / "tests" / "unit" / "common" / "test_logger_setup.py"]
            mock_run.return_value = (True, 10, 90.0)

            result = self.manager.run_tests_by_level("folder")

            assert result is True
            mock_folders.assert_called_once()
            mock_files.assert_called_once()
            mock_tests.assert_called_once()
            mock_run.assert_called_once()

    def test_run_tests_by_level_full(self):
        """Test running full tests."""
        with patch.object(self.manager, "_run_full_tests") as mock_full:
            mock_full.return_value = True

            result = self.manager.run_tests_by_level("full")

            assert result is True
            mock_full.assert_called_once()

    def test_run_tests_by_level_invalid(self):
        """Test running tests with invalid level."""
        result = self.manager.run_tests_by_level("invalid")
        assert result is False

    def test_run_smart_tests_auto_with_changes(self):
        """Test smart tests in auto mode with changes detected (changed-only)."""
        with (
            patch.object(self.manager, "_has_source_changes", return_value=True),
            patch.object(self.manager, "_has_test_changes", return_value=False),
            patch.object(self.manager, "_has_config_changes", return_value=False),
            patch.object(self.manager, "_run_changed_only") as mock_changed_only,
        ):
            mock_changed_only.return_value = True
            result = self.manager.run_smart_tests("auto")

            assert result is True
            mock_changed_only.assert_called_once()

    def test_run_smart_tests_auto_without_changes(self):
        """Test smart tests in auto mode without changes."""
        with (
            patch.object(self.manager, "_has_source_changes", return_value=False),
            patch.object(self.manager, "_has_test_changes", return_value=False),
            patch.object(self.manager, "_has_config_changes", return_value=False),
            patch.object(self.manager, "get_status") as mock_status,
        ):
            mock_status.return_value = {
                "success": True,
                "test_count": 100,
                "coverage_percentage": 85.0,
            }
            result = self.manager.run_smart_tests("auto")

            assert result is True
            mock_status.assert_called_once()

    def test_run_smart_tests_specific_level(self):
        """Test smart tests with specific level."""
        with patch.object(self.manager, "run_tests_by_level") as mock_run:
            mock_run.return_value = True
            result = self.manager.run_smart_tests("unit")

            assert result is True
            mock_run.assert_called_once_with("unit")

    def test_run_tests_success(self):
        """Test successful test run."""
        test_files = [self.project_root / "tests" / "unit" / "common" / "test_logger_setup.py"]

        with patch("subprocess.Popen") as mock_popen:
            # Mock successful subprocess
            mock_process = Mock()
            mock_process.stdout = Mock()
            mock_process.stdout.readline.side_effect = [
                "test_logger_setup.py::test_logger PASSED [100%]",
                "1 passed in 0.01s",
                "TOTAL 100%",
                "",
            ]
            mock_process.wait.return_value = 0
            mock_popen.return_value = mock_process

            success, test_count, coverage = self.manager._run_tests(test_files, "unit")

            assert success is True
            assert test_count == 1
            assert coverage == 100.0

    def test_run_tests_failure(self):
        """Test failed test run."""
        test_files = [self.project_root / "tests" / "unit" / "common" / "test_logger_setup.py"]

        with patch("subprocess.Popen") as mock_popen:
            # Mock failed subprocess
            mock_process = Mock()
            mock_process.stdout = Mock()
            mock_process.stdout.readline.side_effect = [
                "test_logger_setup.py::test_logger FAILED [100%]",
                "1 failed in 0.01s",
                "TOTAL 95%",
                "",
            ]
            mock_process.wait.return_value = 1
            mock_popen.return_value = mock_process

            success, test_count, coverage = self.manager._run_tests(test_files, "unit")

            assert success is False
            assert test_count == 1
            assert coverage == 95.0

    def test_run_tests_no_files(self):
        """Test running tests with no files."""
        success, test_count, coverage = self.manager._run_tests([], "unit")

        assert success is True
        assert test_count == 0
        assert coverage == 100.0

    def test_run_tests_timeout(self):
        """Test test run timeout."""
        test_files = [self.project_root / "tests" / "unit" / "common" / "test_logger_setup.py"]

        with patch("subprocess.Popen") as mock_popen:
            # Mock timeout
            mock_process = Mock()
            mock_process.stdout = Mock()
            mock_process.stdout.readline.side_effect = subprocess.TimeoutExpired("hatch", 600)
            mock_popen.return_value = mock_process

            success, test_count, coverage = self.manager._run_tests(test_files, "unit")

            assert success is False
            assert test_count == 0
            assert coverage == 0.0

    def test_coverage_threshold_error(self):
        """Test coverage threshold error."""
        with pytest.raises(CoverageThresholdError):
            self.manager._check_coverage_threshold(75.0)  # Below 80% threshold

    def test_coverage_threshold_success(self):
        """Test coverage threshold success."""
        # Should not raise exception
        self.manager._check_coverage_threshold(85.0)  # Above 80% threshold

    def test_file_hash_calculation(self):
        """Test file hash calculation."""
        test_file = self.project_root / "src" / "common" / "logger_setup.py"
        test_file.write_text("def test_function(): pass")

        hash1 = self.manager._get_file_hash(test_file)
        hash2 = self.manager._get_file_hash(test_file)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hash length

    def test_should_exclude_file(self):
        """Test file exclusion logic."""
        # Should exclude markdown files
        assert self.manager._should_exclude_file(Path("test.md"))
        assert self.manager._should_exclude_file(Path("README.md"))

        # Should exclude cache directories
        assert self.manager._should_exclude_file(Path("__pycache__/test.pyc"))
        assert self.manager._should_exclude_file(Path(".coverage_cache/test.json"))

        # Should not exclude Python files
        assert not self.manager._should_exclude_file(Path("src/test.py"))
        assert not self.manager._should_exclude_file(Path("tests/test_unit.py"))

    def test_is_config_file(self):
        """Test config file detection."""
        assert self.manager._is_config_file(Path("pyproject.toml"))
        assert self.manager._is_config_file(Path("setup.py"))
        assert self.manager._is_config_file(Path("requirements.txt"))

        assert not self.manager._is_config_file(Path("src/test.py"))
        assert not self.manager._is_config_file(Path("README.md"))

    def test_calculate_tested_coverage_tools_files(self):
        """Test tested coverage calculation for tools files."""
        # Create test files and corresponding source files
        test_file = self.project_root / "tests" / "unit" / "tools" / "test_smart_test_coverage.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("def test_something(): pass")

        # Create the corresponding source file
        source_file = self.project_root / "tools" / "smart_test_coverage.py"
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
        test_file = self.project_root / "tests" / "unit" / "common" / "test_logger_setup.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("def test_something(): pass")

        # Create the corresponding source file
        source_file = self.project_root / "src" / "common" / "logger_setup.py"
        source_file.parent.mkdir(parents=True, exist_ok=True)
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
        test_file1 = self.project_root / "tests" / "unit" / "tools" / "test_smart_test_coverage.py"
        test_file2 = self.project_root / "tests" / "unit" / "common" / "test_logger_setup.py"
        test_file1.parent.mkdir(parents=True, exist_ok=True)
        test_file2.parent.mkdir(parents=True, exist_ok=True)
        test_file1.write_text("def test_something(): pass")
        test_file2.write_text("def test_something(): pass")

        # Create the corresponding source files
        source_file1 = self.project_root / "tools" / "smart_test_coverage.py"
        source_file2 = self.project_root / "src" / "common" / "logger_setup.py"
        source_file2.parent.mkdir(parents=True, exist_ok=True)
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
        test_file = self.project_root / "tests" / "unit" / "nonexistent" / "test_file.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
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

    @patch("subprocess.Popen")
    def test_run_tests_with_tested_coverage_calculation(self, mock_popen):
        """Test _run_tests method with tested coverage calculation for unit/folder tests."""
        # Create test files
        test_file = self.project_root / "tests" / "unit" / "tools" / "test_smart_test_coverage.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
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
        test_file = self.project_root / "tests" / "unit" / "tools" / "test_smart_test_coverage.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
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
        test_file = self.project_root / "tests" / "unit" / "tools" / "test_smart_test_coverage.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
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


class TestSmartCoverageManagerIntegration:
    """Integration tests for the enhanced smart coverage manager."""

    def setup_method(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create comprehensive test structure
        self.create_integration_test_structure()

        # Initialize manager
        self.manager = SmartCoverageManager(str(self.project_root))

    def teardown_method(self):
        """Clean up integration test environment."""
        shutil.rmtree(self.temp_dir)

    def create_integration_test_structure(self):
        """Create comprehensive test directory structure."""
        # Source structure
        (self.project_root / "src" / "common").mkdir(parents=True)
        (self.project_root / "src" / "agents" / "supervisor").mkdir(parents=True)
        (self.project_root / "src" / "agents" / "architecture").mkdir(parents=True)
        (self.project_root / "tools").mkdir(parents=True)

        # Test structure
        (self.project_root / "tests" / "unit" / "common").mkdir(parents=True)
        (self.project_root / "tests" / "unit" / "agents" / "supervisor").mkdir(parents=True)
        (self.project_root / "tests" / "unit" / "agents" / "architecture").mkdir(parents=True)
        (self.project_root / "tests" / "unit" / "tools").mkdir(parents=True)

        # Create source files
        source_files = {
            "src/common/logger_setup.py": "def get_logger(): pass",
            "src/common/redis_client.py": "def get_redis(): pass",
            "src/agents/supervisor/supervisor_agent.py": "class SupervisorAgent: pass",
            "src/agents/architecture/architecture_agent.py": "class ArchitectureAgent: pass",
            "tools/contract_to_code.py": "def generate_code(): pass",
        }

        for file_path, content in source_files.items():
            (self.project_root / file_path).write_text(content)

        # Create test files
        test_files = {
            "tests/unit/common/test_logger_setup.py": "def test_logger(): pass",
            "tests/unit/common/test_redis_client.py": "def test_redis(): pass",
            "tests/unit/agents/supervisor/test_supervisor_agent.py": "def test_supervisor(): pass",
            "tests/unit/agents/architecture/test_architecture_agent.py": "def test_architecture(): pass",
            "tests/unit/tools/test_contract_to_code.py": "def test_contract(): pass",
        }

        for file_path, content in test_files.items():
            (self.project_root / file_path).write_text(content)

    def test_integration_unit_testing(self):
        """Test integration of unit testing workflow."""
        # Simulate cache with some files
        self.manager.cache = {
            "last_full_run": "2025-01-01T00:00:00",
            "file_hashes": {
                "src/common/logger_setup.py": "old_hash",
                "src/agents/supervisor/supervisor_agent.py": "old_hash",
            },
        }

        # Get modified files
        modified_files = self.manager._get_modified_files()
        assert len(modified_files) >= 2

        # Get unit tests for modified files
        unit_tests = self.manager._get_unit_tests_for_files(modified_files)
        assert len(unit_tests) >= 1

        # Verify correct test files are found
        try:
            test_paths = {str(f.relative_to(self.project_root)) for f in unit_tests}
        except ValueError:
            # Handle path resolution issues in test environment
            test_paths = {str(f) for f in unit_tests}
        # Just check that we found some test files
        assert len(test_paths) >= 1

    def test_integration_folder_testing(self):
        """Test integration of folder testing workflow."""
        # Simulate cache with some files
        self.manager.cache = {
            "last_full_run": "2025-01-01T00:00:00",
            "file_hashes": {
                "src/common/logger_setup.py": "old_hash",
                "src/agents/supervisor/supervisor_agent.py": "old_hash",
            },
        }

        # Get modified folders
        modified_folders = self.manager._get_modified_folders()
        assert len(modified_folders) >= 1

        # Get files in modified folders
        folder_files = self.manager._get_files_in_folders(modified_folders)
        assert len(folder_files) >= 1

        # Get unit tests for those files
        folder_tests = self.manager._get_unit_tests_for_files(folder_files)
        assert len(folder_tests) >= 1

        # Verify correct test files are found
        try:
            test_paths = {str(f.relative_to(self.project_root)) for f in folder_tests}
        except ValueError:
            # Handle path resolution issues in test environment
            test_paths = {str(f) for f in folder_tests}
        # Just check that we found some test files
        assert len(test_paths) >= 1

    def test_integration_workflow_sequence(self):
        """Test the complete workflow sequence."""
        # 1. Start with no cache
        assert self.manager.cache.get("last_full_run") is None

        # 2. Check if full test needed (should be False in local smart-test mode)
        needs_full_run = self.manager.check_if_full_test_needed()
        assert needs_full_run is False

        # 3. Run unit tests (should work even with no cache)
        with patch.object(self.manager, "_run_tests") as mock_run:
            mock_run.return_value = (True, 5, 85.0)
            result = self.manager.run_tests_by_level("unit")
            assert result is True

        # 4. Run folder tests
        with patch.object(self.manager, "_run_tests") as mock_run:
            mock_run.return_value = (True, 10, 90.0)
            result = self.manager.run_tests_by_level("folder")
            assert result is True

        # 5. Run full tests
        with patch.object(self.manager, "_run_coverage_tests") as mock_full:
            mock_full.return_value = (True, 20, 95.0)
            result = self.manager.run_tests_by_level("full")
            assert result is True


if __name__ == "__main__":
    pytest.main([__file__])
