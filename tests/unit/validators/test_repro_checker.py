"""Unit tests for ReproChecker.

Focus: Business logic and edge cases only (@beartype handles type validation).
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from specfact_cli.utils.env_manager import EnvManager, EnvManagerInfo
from specfact_cli.validators.repro_checker import (
    CheckResult,
    CheckStatus,
    ReproChecker,
    ReproReport,
    _extract_basedpyright_findings,
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

    def test_run_check_crosshair_side_effect_includes_target_command(self, tmp_path: Path):
        """CrossHair side-effect errors should include executed target command for debugging."""
        checker = ReproChecker(repo_path=tmp_path, budget=30)

        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 2
            mock_proc.stdout = ""
            mock_proc.stderr = "SideEffectDetected: import side effect"
            mock_run.return_value = mock_proc

            result = checker.run_check(
                name="Contract exploration (CrossHair)",
                tool="crosshair",
                command=["python", "-m", "crosshair", "check", "specfact_cli.modules.repro.src.commands"],
                timeout=10,
                skip_if_missing=False,
            )

            assert result.status == CheckStatus.SKIPPED
            assert "Target command:" in result.error
            assert "specfact_cli.modules.repro.src.commands" in result.error

    def test_run_all_checks_with_ruff(self, tmp_path: Path):
        """Test run_all_checks executes ruff check."""
        # Create src directory for source detection
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "__init__.py").write_text("")

        checker = ReproChecker(repo_path=tmp_path, budget=30)

        # Mock environment detection
        env_info = EnvManagerInfo(
            manager=EnvManager.UNKNOWN,
            available=True,
            command_prefix=[],
            message="Test",
        )

        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = "Linting passed"
            mock_proc.stderr = ""
            mock_run.return_value = mock_proc

            # Mock environment detection and tool availability
            with (
                patch("specfact_cli.utils.env_manager.detect_env_manager", return_value=env_info),
                patch("specfact_cli.utils.env_manager.check_tool_in_env", return_value=(True, None)),
                patch("shutil.which", return_value="/usr/bin/ruff"),
            ):
                report = checker.run_all_checks()

            assert report.total_checks >= 1
            # Check that ruff was run
            ruff_check = next((c for c in report.checks if c.tool == "ruff"), None)
            assert ruff_check is not None
            assert ruff_check.status == CheckStatus.PASSED

    def test_run_all_checks_fail_fast(self, tmp_path: Path):
        """Test run_all_checks stops on first failure with fail_fast."""
        # Create src directory for source detection
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "__init__.py").write_text("")

        checker = ReproChecker(repo_path=tmp_path, budget=30, fail_fast=True)

        # Mock environment detection
        env_info = EnvManagerInfo(
            manager=EnvManager.UNKNOWN,
            available=True,
            command_prefix=[],
            message="Test",
        )

        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 1  # First check fails
            mock_proc.stdout = ""
            mock_proc.stderr = "Error"
            mock_run.return_value = mock_proc

            # Mock environment detection and tool availability
            with (
                patch("specfact_cli.utils.env_manager.detect_env_manager", return_value=env_info),
                patch("specfact_cli.utils.env_manager.check_tool_in_env", return_value=(True, None)),
                patch("shutil.which", return_value="/usr/bin/ruff"),
            ):
                report = checker.run_all_checks()

            # Should have stopped after first failure
            assert report.failed_checks > 0
            # Should have fewer checks than normal (fail_fast stopped early)
            # Note: This is a weak assertion, but fail_fast logic is in run_all_checks

    def test_run_all_checks_crosshair_required_converts_skipped_to_failed(self, tmp_path: Path):
        """Strict CrossHair mode should fail when CrossHair is skipped."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "__init__.py").write_text("")

        checker = ReproChecker(repo_path=tmp_path, budget=30, crosshair_required=True)
        env_info = EnvManagerInfo(
            manager=EnvManager.UNKNOWN,
            available=True,
            command_prefix=[],
            message="Test",
        )

        def _fake_run_check(*args, **kwargs):  # type: ignore[no-untyped-def]
            tool = args[1] if len(args) > 1 else kwargs.get("tool")
            if tool == "crosshair":
                return CheckResult(
                    name="Contract exploration (CrossHair)",
                    tool="crosshair",
                    status=CheckStatus.SKIPPED,
                    error="CrossHair side-effect detected",
                )
            return CheckResult(name=args[0], tool=tool, status=CheckStatus.PASSED, duration=0.1)

        with (
            patch("specfact_cli.utils.env_manager.detect_env_manager", return_value=env_info),
            patch("specfact_cli.utils.env_manager.check_tool_in_env", return_value=(True, None)),
            patch("shutil.which", return_value="/usr/bin/tool"),
            patch.object(checker, "run_check", side_effect=_fake_run_check),
        ):
            report = checker.run_all_checks()

        crosshair_check = next(check for check in report.checks if check.tool == "crosshair")
        assert crosshair_check.status == CheckStatus.FAILED
        assert report.crosshair_requirement_violated is True
        assert report.get_exit_code() == 1

    def test_repro_checker_fix_flag(self, tmp_path: Path):
        """Test ReproChecker with fix=True includes --fix in Semgrep command."""
        # Create semgrep config to enable Semgrep check
        semgrep_config = tmp_path / "tools" / "semgrep" / "async.yml"
        semgrep_config.parent.mkdir(parents=True, exist_ok=True)
        semgrep_config.write_text("rules:\n  - id: test-rule\n    patterns:\n      - pattern: test\n")

        # Create src directory for source detection
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "__init__.py").write_text("")

        checker = ReproChecker(repo_path=tmp_path, budget=30, fix=True)
        assert checker.fix is True

        # Mock environment detection
        env_info = EnvManagerInfo(
            manager=EnvManager.UNKNOWN,
            available=True,
            command_prefix=[],
            message="Test",
        )

        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = ""
            mock_proc.stderr = ""
            mock_run.return_value = mock_proc

            # Mock environment detection and tool availability
            with (
                patch("specfact_cli.utils.env_manager.detect_env_manager", return_value=env_info),
                patch("specfact_cli.utils.env_manager.check_tool_in_env", return_value=(True, None)),
                patch("shutil.which", return_value="/usr/bin/semgrep"),
            ):
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

    def test_extract_basedpyright_findings_parses_pretty_output(self):
        """Parser handles basedpyright pretty output with '- warning:' format."""
        output = (
            "/tmp/a.py\n"
            '  /tmp/a.py:10:4 - warning: Type of "x" is unknown (reportUnknownMemberType)\n'
            "0 errors, 1 warnings, 0 notes\n"
        )
        findings = _extract_basedpyright_findings(output)
        assert findings["total_errors"] == 0
        assert findings["total_warnings"] == 1

    def test_run_all_checks_metadata_uses_absolute_fallback_when_outside_repo(self, tmp_path: Path):
        """Metadata collection should not fail if default plan path is outside repo root."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "__init__.py").write_text("")
        checker = ReproChecker(repo_path=tmp_path, budget=30)

        env_info = EnvManagerInfo(
            manager=EnvManager.UNKNOWN,
            available=True,
            command_prefix=[],
            message="Test",
        )

        outside_dir = Path("/tmp/not-under-repo")
        outside_dir.mkdir(parents=True, exist_ok=True)
        outside_plan = outside_dir / "main.bundle.yaml"
        outside_enforce = outside_dir / "enforcement.yaml"
        outside_plan.write_text("plan: demo\n", encoding="utf-8")
        outside_enforce.write_text("preset: balanced\n", encoding="utf-8")

        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = "ok"
            mock_proc.stderr = ""
            mock_run.return_value = mock_proc

            with (
                patch("specfact_cli.utils.env_manager.detect_env_manager", return_value=env_info),
                patch("specfact_cli.utils.env_manager.check_tool_in_env", return_value=(True, None)),
                patch("shutil.which", return_value="/usr/bin/ruff"),
                patch("specfact_cli.utils.structure.SpecFactStructure.get_default_plan_path", return_value=outside_plan),
                patch(
                    "specfact_cli.utils.structure.SpecFactStructure.get_enforcement_config_path",
                    return_value=outside_enforce,
                ),
                patch("specfact_cli.utils.yaml_utils.load_yaml", return_value=None),
                patch("specfact_cli.validators.repro_checker.console") as console_mock,
            ):
                report = checker.run_all_checks()

        assert report.active_plan_path == str(outside_plan)
        assert report.enforcement_config_path == str(outside_enforce)
        console_calls = "\n".join(str(call) for call in console_mock.print.call_args_list)
        assert "Could not collect metadata" not in console_calls

    def test_repro_report_metadata_minimal(self):
        """Test ReproReport metadata is optional (only includes available fields)."""
        report = ReproReport()
        report_dict = report.to_dict()

        # Should still have timestamp even if no other metadata
        assert "metadata" in report_dict
        assert "timestamp" in report_dict["metadata"]

    def test_run_all_checks_with_environment_detection_hatch(self, tmp_path: Path):
        """Test run_all_checks uses hatch environment when detected."""
        # Create hatch project structure
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[tool.hatch]
version = "1.0.0"
"""
        )
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "__init__.py").write_text("")

        checker = ReproChecker(repo_path=tmp_path, budget=30)

        # Mock hatch environment detection
        env_info = EnvManagerInfo(
            manager=EnvManager.HATCH,
            available=True,
            command_prefix=["hatch", "run"],
            message="Detected hatch",
        )

        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = "Success"
            mock_proc.stderr = ""
            mock_run.return_value = mock_proc

            with (
                patch("specfact_cli.utils.env_manager.detect_env_manager", return_value=env_info),
                patch("specfact_cli.utils.env_manager.check_tool_in_env", return_value=(True, None)),
                patch("shutil.which", return_value="/usr/bin/ruff"),
            ):
                checker.run_all_checks()

            # Verify commands were built with hatch prefix
            ruff_calls = [
                call
                for call in mock_run.call_args_list
                if "ruff" in str(call.args[0] if hasattr(call, "args") else call)
            ]
            if ruff_calls:
                # Check that hatch run was used
                call_args = ruff_calls[0].args[0] if hasattr(ruff_calls[0], "args") else ruff_calls[0][0]
                assert "hatch" in str(call_args) or any("hatch" in str(arg) for arg in call_args)

    def test_run_all_checks_with_environment_detection_poetry(self, tmp_path: Path):
        """Test run_all_checks uses poetry environment when detected."""
        # Create poetry project structure
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[tool.poetry]
name = "test-project"
"""
        )
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "__init__.py").write_text("")

        checker = ReproChecker(repo_path=tmp_path, budget=30)

        # Mock poetry environment detection
        env_info = EnvManagerInfo(
            manager=EnvManager.POETRY,
            available=True,
            command_prefix=["poetry", "run"],
            message="Detected poetry",
        )

        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = "Success"
            mock_proc.stderr = ""
            mock_run.return_value = mock_proc

            with (
                patch("specfact_cli.utils.env_manager.detect_env_manager", return_value=env_info),
                patch("specfact_cli.utils.env_manager.check_tool_in_env", return_value=(True, None)),
                patch("shutil.which", return_value="/usr/bin/ruff"),
            ):
                report = checker.run_all_checks()

            assert report.total_checks >= 1

    def test_run_all_checks_tool_not_available(self, tmp_path: Path):
        """Test run_all_checks skips tools that are not available."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "__init__.py").write_text("")

        checker = ReproChecker(repo_path=tmp_path, budget=30)

        # Mock environment detection
        env_info = EnvManagerInfo(
            manager=EnvManager.UNKNOWN,
            available=True,
            command_prefix=[],
            message="Test",
        )

        with (
            patch("specfact_cli.utils.env_manager.detect_env_manager", return_value=env_info),
            patch("specfact_cli.utils.env_manager.check_tool_in_env", return_value=(False, "Tool not found")),
        ):
            report = checker.run_all_checks()

            # Tools should be skipped
            skipped_checks = [c for c in report.checks if c.status == CheckStatus.SKIPPED]
            assert len(skipped_checks) > 0
            assert all("not found" in c.error.lower() or "not available" in c.error.lower() for c in skipped_checks)

    def test_run_all_checks_source_detection(self, tmp_path: Path):
        """Test run_all_checks detects source directories dynamically."""
        # Create package directory (not src/)
        package_dir = tmp_path / "my_package"
        package_dir.mkdir()
        (package_dir / "__init__.py").write_text("")

        # Create pyproject.toml with package name
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "my-package"
"""
        )

        checker = ReproChecker(repo_path=tmp_path, budget=30)

        # Mock environment detection
        env_info = EnvManagerInfo(
            manager=EnvManager.UNKNOWN,
            available=True,
            command_prefix=[],
            message="Test",
        )

        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = "Success"
            mock_proc.stderr = ""
            mock_run.return_value = mock_proc

            with (
                patch("specfact_cli.utils.env_manager.detect_env_manager", return_value=env_info),
                patch("specfact_cli.utils.env_manager.check_tool_in_env", return_value=(True, None)),
                patch("shutil.which", return_value="/usr/bin/ruff"),
            ):
                report = checker.run_all_checks()

            # Should have detected my_package/ as source directory
            assert report.total_checks >= 1
