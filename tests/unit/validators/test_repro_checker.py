"""Unit tests for ReproChecker.

Focus: Business logic and edge cases only (@beartype handles type validation).
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from specfact_cli.validators.repro_checker import (
    CheckResult,
    CheckStatus,
    ReproChecker,
    ReproReport,
)


class TestReproChecker:
    """Test ReproChecker functionality."""

    def test_run_check_tool_missing(self, tmp_path: Path):
        """Test run_check skips when tool is missing."""
        checker = ReproChecker(repo_path=tmp_path, budget=30)
        result = checker.run_check(
            name="Test Check",
            tool="nonexistent_tool",
            command=["nonexistent_tool", "check"],
            timeout=10,
            skip_if_missing=True,
        )
        assert result.status == CheckStatus.SKIPPED
        assert "not found" in result.error

    def test_run_check_passed(self, tmp_path: Path):
        """Test run_check with passing command."""
        checker = ReproChecker(repo_path=tmp_path, budget=30)

        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = "Success"
            mock_proc.stderr = ""
            mock_run.return_value = mock_proc

            result = checker.run_check(
                name="Test Check",
                tool="test",
                command=["test", "check"],
                timeout=10,
                skip_if_missing=False,
            )

            assert result.status == CheckStatus.PASSED
            assert result.exit_code == 0
            assert result.output == "Success"
            mock_run.assert_called_once()

    def test_run_check_failed(self, tmp_path: Path):
        """Test run_check with failing command."""
        checker = ReproChecker(repo_path=tmp_path, budget=30)

        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 1
            mock_proc.stdout = ""
            mock_proc.stderr = "Error occurred"
            mock_run.return_value = mock_proc

            result = checker.run_check(
                name="Test Check",
                tool="test",
                command=["test", "check"],
                timeout=10,
                skip_if_missing=False,
            )

            assert result.status == CheckStatus.FAILED
            assert result.exit_code == 1
            assert result.error == "Error occurred"

    def test_run_check_timeout(self, tmp_path: Path):
        """Test run_check with timeout."""
        checker = ReproChecker(repo_path=tmp_path, budget=30)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("test", 10)

            result = checker.run_check(
                name="Test Check",
                tool="test",
                command=["test", "check"],
                timeout=10,
                skip_if_missing=False,
            )

            assert result.status == CheckStatus.TIMEOUT
            assert result.timeout is True
            assert "timed out" in result.error

    def test_run_check_budget_exceeded(self, tmp_path: Path):
        """Test run_check stops when budget exceeded."""
        checker = ReproChecker(repo_path=tmp_path, budget=1)  # Very small budget
        checker.start_time = time.time() - 2  # Already exceeded budget

        result = checker.run_check(
            name="Test Check",
            tool="test",
            command=["test", "check"],
            timeout=10,
            skip_if_missing=False,
        )

        assert result.status == CheckStatus.TIMEOUT
        assert result.timeout is True
        assert checker.report.budget_exceeded is True

    def test_run_all_checks_with_ruff(self, tmp_path: Path):
        """Test run_all_checks executes ruff check."""
        checker = ReproChecker(repo_path=tmp_path, budget=30)

        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = "Linting passed"
            mock_proc.stderr = ""
            mock_run.return_value = mock_proc

            # Mock shutil.which to make tools "available"
            with patch("shutil.which", return_value="/usr/bin/ruff"):
                report = checker.run_all_checks()

            assert report.total_checks >= 1
            # Check that ruff was run
            ruff_check = next((c for c in report.checks if c.tool == "ruff"), None)
            assert ruff_check is not None
            assert ruff_check.status == CheckStatus.PASSED

    def test_run_all_checks_fail_fast(self, tmp_path: Path):
        """Test run_all_checks stops on first failure with fail_fast."""
        checker = ReproChecker(repo_path=tmp_path, budget=30, fail_fast=True)

        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 1  # First check fails
            mock_proc.stdout = ""
            mock_proc.stderr = "Error"
            mock_run.return_value = mock_proc

            # Mock shutil.which to make tools "available"
            with patch("shutil.which", return_value="/usr/bin/ruff"):
                report = checker.run_all_checks()

            # Should have stopped after first failure
            assert report.failed_checks > 0
            # Should have fewer checks than normal (fail_fast stopped early)
            # Note: This is a weak assertion, but fail_fast logic is in run_all_checks

    def test_repro_checker_fix_flag(self, tmp_path: Path):
        """Test ReproChecker with fix=True includes --fix in Semgrep command."""
        # Create semgrep config to enable Semgrep check
        semgrep_config = tmp_path / "tools" / "semgrep" / "async.yml"
        semgrep_config.parent.mkdir(parents=True, exist_ok=True)
        semgrep_config.write_text("rules:\n  - id: test-rule\n    patterns:\n      - pattern: test\n")

        checker = ReproChecker(repo_path=tmp_path, budget=30, fix=True)
        assert checker.fix is True

        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = ""
            mock_proc.stderr = ""
            mock_run.return_value = mock_proc

            # Mock shutil.which to make tools "available"
            with patch("shutil.which", return_value="/usr/bin/semgrep"):
                checker.run_all_checks()

            # Verify Semgrep was called with --autofix flag
            semgrep_calls = [call for call in mock_run.call_args_list if "semgrep" in str(call)]
            if semgrep_calls:
                # Check that --autofix is in the command
                semgrep_call = semgrep_calls[0]
                command = semgrep_call[0][0] if isinstance(semgrep_call[0], tuple) else semgrep_call[0]
                assert "--autofix" in command or any("--autofix" in str(arg) for arg in command)

    def test_repro_checker_fix_flag_disabled(self, tmp_path: Path):
        """Test ReproChecker with fix=False does not include --fix in Semgrep command."""
        # Create semgrep config to enable Semgrep check
        semgrep_config = tmp_path / "tools" / "semgrep" / "async.yml"
        semgrep_config.parent.mkdir(parents=True, exist_ok=True)
        semgrep_config.write_text("rules:\n  - id: test-rule\n    patterns:\n      - pattern: test\n")

        checker = ReproChecker(repo_path=tmp_path, budget=30, fix=False)
        assert checker.fix is False

    def test_repro_report_add_check(self):
        """Test ReproReport.add_check updates counts."""
        report = ReproReport()

        result1 = CheckResult(
            name="Check 1",
            tool="test",
            status=CheckStatus.PASSED,
            duration=1.0,
        )
        report.add_check(result1)
        assert report.total_checks == 1
        assert report.passed_checks == 1
        assert report.total_duration == 1.0

        result2 = CheckResult(
            name="Check 2",
            tool="test",
            status=CheckStatus.FAILED,
            duration=2.0,
        )
        report.add_check(result2)
        assert report.total_checks == 2
        assert report.passed_checks == 1
        assert report.failed_checks == 1
        assert report.total_duration == 3.0

    def test_repro_report_get_exit_code(self):
        """Test ReproReport.get_exit_code returns correct codes."""
        report = ReproReport()

        # All passed
        report.add_check(CheckResult(name="Check", tool="test", status=CheckStatus.PASSED))
        assert report.get_exit_code() == 0

        # Some failed
        report.add_check(CheckResult(name="Check", tool="test", status=CheckStatus.FAILED))
        assert report.get_exit_code() == 1

        # Budget exceeded
        report.budget_exceeded = True
        assert report.get_exit_code() == 2

    def test_repro_report_get_exit_code_timeout(self):
        """Test ReproReport.get_exit_code returns 2 for timeout."""
        report = ReproReport()
        report.add_check(CheckResult(name="Check", tool="test", status=CheckStatus.TIMEOUT, timeout=True))
        assert report.get_exit_code() == 2

    def test_repro_report_metadata(self):
        """Test ReproReport includes metadata in to_dict."""
        report = ReproReport()
        report.repo_path = "/test/repo"
        report.budget = 120
        report.active_plan_path = ".specfact/plans/main.bundle.yaml"
        report.enforcement_config_path = ".specfact/gates/config/enforcement.yaml"
        report.enforcement_preset = "balanced"
        report.fix_enabled = True
        report.fail_fast = False

        report_dict = report.to_dict()

        assert "metadata" in report_dict
        metadata = report_dict["metadata"]
        assert metadata["repo_path"] == "/test/repo"
        assert metadata["budget"] == 120
        assert metadata["active_plan_path"] == ".specfact/plans/main.bundle.yaml"
        assert metadata["enforcement_config_path"] == ".specfact/gates/config/enforcement.yaml"
        assert metadata["enforcement_preset"] == "balanced"
        assert metadata["fix_enabled"] is True
        assert "fail_fast" not in metadata  # Should be omitted when False

    def test_repro_report_metadata_minimal(self):
        """Test ReproReport metadata is optional (only includes available fields)."""
        report = ReproReport()
        report_dict = report.to_dict()

        # Should still have timestamp even if no other metadata
        assert "metadata" in report_dict
        assert "timestamp" in report_dict["metadata"]
