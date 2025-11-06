"""End-to-end tests for GitHub Action workflow integration."""

from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from specfact_cli.utils.github_annotations import main as github_annotations_main
from specfact_cli.utils.yaml_utils import dump_yaml


runner = CliRunner()


class TestGitHubActionWorkflow:
    """E2E tests simulating GitHub Action workflow execution."""

    def test_complete_github_action_workflow_success(self, tmp_path: Path) -> None:
        """
        Test complete GitHub Action workflow with successful validation.

        This simulates:
        1. Running repro command in CI/CD
        2. Generating repro report
        3. Creating GitHub annotations
        4. Generating PR comment
        """
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Step 1: Create a repro report with all passed checks
            report_dir = tmp_path / ".specfact" / "reports" / "enforcement"
            report_dir.mkdir(parents=True, exist_ok=True)

            report_data = {
                "total_checks": 3,
                "passed_checks": 3,
                "failed_checks": 0,
                "timeout_checks": 0,
                "skipped_checks": 0,
                "budget_exceeded": False,
                "total_duration": 15.5,
                "checks": [
                    {
                        "name": "Ruff Check",
                        "tool": "ruff",
                        "status": "passed",
                        "duration": 5.0,
                    },
                    {
                        "name": "Semgrep Check",
                        "tool": "semgrep",
                        "status": "passed",
                        "duration": 8.0,
                    },
                    {
                        "name": "Type Check",
                        "tool": "basedpyright",
                        "status": "passed",
                        "duration": 2.5,
                    },
                ],
            }

            report_path = report_dir / "report-2025-01-31T12-00-00.yaml"
            dump_yaml(report_data, report_path)

            # Step 2: Run github_annotations script
            os.environ["SPECFACT_REPORT_PATH"] = str(report_path)
            exit_code = github_annotations_main()

            # Should return 0 (no failures)
            assert exit_code == 0

            # Step 3: Verify PR comment was generated (if in PR context)
            os.environ["GITHUB_EVENT_NAME"] = "pull_request"
            exit_code = github_annotations_main()

            comment_path = tmp_path / ".specfact" / "pr-comment.md"
            assert comment_path.exists()

            comment = comment_path.read_text(encoding="utf-8")
            assert "## SpecFact CLI Validation Report" in comment
            assert "✅ **All validations passed!**" in comment
            assert "**Duration**: 15.50s" in comment

        finally:
            os.chdir(old_cwd)
            # Clean up environment variables
            os.environ.pop("SPECFACT_REPORT_PATH", None)
            os.environ.pop("GITHUB_EVENT_NAME", None)

    def test_complete_github_action_workflow_with_failures(self, tmp_path: Path) -> None:
        """
        Test complete GitHub Action workflow with validation failures.

        This simulates:
        1. Running repro command in CI/CD
        2. Generating repro report with failures
        3. Creating GitHub annotations (error level)
        4. Generating PR comment with failure details
        5. Workflow should fail (exit code 1)
        """
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Step 1: Create a repro report with failed checks
            report_dir = tmp_path / ".specfact" / "reports" / "enforcement"
            report_dir.mkdir(parents=True, exist_ok=True)

            report_data = {
                "total_checks": 4,
                "passed_checks": 2,
                "failed_checks": 2,
                "timeout_checks": 0,
                "skipped_checks": 0,
                "budget_exceeded": False,
                "total_duration": 20.0,
                "checks": [
                    {
                        "name": "Ruff Check",
                        "tool": "ruff",
                        "status": "passed",
                        "duration": 5.0,
                    },
                    {
                        "name": "Semgrep Check",
                        "tool": "semgrep",
                        "status": "failed",
                        "error": "Found 3 async anti-patterns",
                        "duration": 8.0,
                    },
                    {
                        "name": "Type Check",
                        "tool": "basedpyright",
                        "status": "passed",
                        "duration": 2.0,
                    },
                    {
                        "name": "Contract Check",
                        "tool": "crosshair",
                        "status": "failed",
                        "output": "Contract violation detected in function foo",
                        "duration": 5.0,
                    },
                ],
            }

            report_path = report_dir / "report-2025-01-31T12-00-00.yaml"
            dump_yaml(report_data, report_path)

            # Step 2: Run github_annotations script
            os.environ["SPECFACT_REPORT_PATH"] = str(report_path)
            exit_code = github_annotations_main()

            # Should return 1 (failures detected)
            assert exit_code == 1

            # Step 3: Verify PR comment was generated with failure details
            os.environ["GITHUB_EVENT_NAME"] = "pull_request"
            exit_code = github_annotations_main()

            comment_path = tmp_path / ".specfact" / "pr-comment.md"
            assert comment_path.exists()

            comment = comment_path.read_text(encoding="utf-8")
            assert "❌ **Validation issues detected**" in comment
            assert "### ❌ Failed Checks" in comment
            assert "Semgrep Check (semgrep)" in comment
            assert "Found 3 async anti-patterns" in comment
            assert "Contract Check (crosshair)" in comment
            assert "### 💡 Suggestions" in comment

        finally:
            os.chdir(old_cwd)
            os.environ.pop("SPECFACT_REPORT_PATH", None)
            os.environ.pop("GITHUB_EVENT_NAME", None)

    def test_github_action_workflow_budget_exceeded(self, tmp_path: Path) -> None:
        """
        Test GitHub Action workflow when budget is exceeded.

        This simulates:
        1. Running repro command with budget limit
        2. Budget exceeded during validation
        3. Creating annotations for budget exceeded
        4. Generating PR comment with budget warning
        """
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Step 1: Create a repro report with budget exceeded
            report_dir = tmp_path / ".specfact" / "reports" / "enforcement"
            report_dir.mkdir(parents=True, exist_ok=True)

            report_data = {
                "total_checks": 2,
                "passed_checks": 1,
                "failed_checks": 0,
                "timeout_checks": 1,
                "skipped_checks": 0,
                "budget_exceeded": True,
                "total_duration": 95.0,
                "checks": [
                    {
                        "name": "Ruff Check",
                        "tool": "ruff",
                        "status": "passed",
                        "duration": 5.0,
                    },
                    {
                        "name": "Semgrep Check",
                        "tool": "semgrep",
                        "status": "timeout",
                        "duration": 90.0,
                    },
                ],
            }

            report_path = report_dir / "report-2025-01-31T12-00-00.yaml"
            dump_yaml(report_data, report_path)

            # Step 2: Run github_annotations script
            os.environ["SPECFACT_REPORT_PATH"] = str(report_path)
            exit_code = github_annotations_main()

            # Should return 1 (budget exceeded is a failure)
            assert exit_code == 1

            # Step 3: Verify PR comment includes budget warning
            os.environ["GITHUB_EVENT_NAME"] = "pull_request"
            exit_code = github_annotations_main()

            comment_path = tmp_path / ".specfact" / "pr-comment.md"
            assert comment_path.exists()

            comment = comment_path.read_text(encoding="utf-8")
            assert "### ⚠️ Budget Exceeded" in comment
            assert "budget was exceeded" in comment

        finally:
            os.chdir(old_cwd)
            os.environ.pop("SPECFACT_REPORT_PATH", None)
            os.environ.pop("GITHUB_EVENT_NAME", None)

    def test_github_action_workflow_auto_detect_report(self, tmp_path: Path) -> None:
        """
        Test GitHub Action workflow auto-detecting latest report.

        This simulates:
        1. Multiple reports in directory
        2. Script auto-detects latest by modification time
        3. Processes latest report
        """
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Step 1: Create multiple reports
            report_dir = tmp_path / ".specfact" / "reports" / "enforcement"
            report_dir.mkdir(parents=True, exist_ok=True)

            # Older report
            old_report = {
                "total_checks": 1,
                "passed_checks": 0,
                "failed_checks": 1,
                "checks": [{"name": "Old Check", "tool": "test", "status": "failed"}],
            }
            old_path = report_dir / "report-2025-01-31T10-00-00.yaml"
            dump_yaml(old_report, old_path)

            # Newer report (should be selected)
            new_report = {
                "total_checks": 1,
                "passed_checks": 1,
                "failed_checks": 0,
                "checks": [{"name": "New Check", "tool": "test", "status": "passed"}],
            }
            new_path = report_dir / "report-2025-01-31T12-00-00.yaml"
            dump_yaml(new_report, new_path)

            # Step 2: Run github_annotations script without SPECFACT_REPORT_PATH
            # Should auto-detect latest report
            if "SPECFACT_REPORT_PATH" in os.environ:
                del os.environ["SPECFACT_REPORT_PATH"]

            exit_code = github_annotations_main()

            # Should return 0 (latest report has no failures)
            assert exit_code == 0

        finally:
            os.chdir(old_cwd)
            os.environ.pop("SPECFACT_REPORT_PATH", None)

    def test_github_action_workflow_integration_with_repro_command(self, tmp_path: Path) -> None:
        """
        Test complete integration: repro command -> report -> annotations.

        This simulates the full GitHub Action workflow:
        1. Run repro command (would fail in real scenario, but we mock results)
        2. Read generated report
        3. Generate annotations and PR comment
        """
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Step 1: Create a minimal .specfact structure
            (tmp_path / ".specfact").mkdir()
            (tmp_path / ".specfact" / "reports" / "enforcement").mkdir(parents=True)

            # Step 2: Create a repro report (simulating what repro command would generate)
            report_data = {
                "total_checks": 2,
                "passed_checks": 1,
                "failed_checks": 1,
                "timeout_checks": 0,
                "skipped_checks": 0,
                "budget_exceeded": False,
                "total_duration": 12.3,
                "checks": [
                    {
                        "name": "Ruff Check",
                        "tool": "ruff",
                        "status": "passed",
                        "duration": 5.0,
                    },
                    {
                        "name": "Semgrep Check",
                        "tool": "semgrep",
                        "status": "failed",
                        "error": "Async anti-pattern detected",
                        "duration": 7.3,
                    },
                ],
            }

            report_path = tmp_path / ".specfact" / "reports" / "enforcement" / "report-2025-01-31T12-00-00.yaml"
            dump_yaml(report_data, report_path)

            # Step 3: Run github_annotations script
            os.environ["SPECFACT_REPORT_PATH"] = str(report_path)
            os.environ["GITHUB_EVENT_NAME"] = "pull_request"

            exit_code = github_annotations_main()

            # Should return 1 (failures detected)
            assert exit_code == 1

            # Step 4: Verify annotations and PR comment were created
            comment_path = tmp_path / ".specfact" / "pr-comment.md"
            assert comment_path.exists()

            comment = comment_path.read_text(encoding="utf-8")
            assert "Semgrep Check (semgrep)" in comment
            assert "Async anti-pattern detected" in comment

        finally:
            os.chdir(old_cwd)
            os.environ.pop("SPECFACT_REPORT_PATH", None)
            os.environ.pop("GITHUB_EVENT_NAME", None)
