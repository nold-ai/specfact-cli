"""Unit tests for GitHub annotations utilities."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from specfact_cli.utils.github_annotations import (
    create_annotation,
    create_annotations_from_report,
    generate_pr_comment,
    parse_repro_report,
)


class TestCreateAnnotation:
    """Tests for create_annotation function."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_create_error_annotation(self, mock_stdout: StringIO) -> None:
        """Test creating an error annotation."""
        create_annotation("Test error message", level="error")
        output = mock_stdout.getvalue()
        assert "::error" in output
        assert "Test error message" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_create_warning_annotation(self, mock_stdout: StringIO) -> None:
        """Test creating a warning annotation."""
        create_annotation("Test warning", level="warning")
        output = mock_stdout.getvalue()
        assert "::warning" in output
        assert "Test warning" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_create_notice_annotation(self, mock_stdout: StringIO) -> None:
        """Test creating a notice annotation."""
        create_annotation("Test notice", level="notice")
        output = mock_stdout.getvalue()
        assert "::notice" in output
        assert "Test notice" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_create_annotation_with_file_location(self, mock_stdout: StringIO) -> None:
        """Test creating annotation with file location."""
        create_annotation(
            "Test message",
            level="error",
            file="src/test.py",
            line=10,
            col=5,
            title="Test Title",
        )
        output = mock_stdout.getvalue()
        assert "::error" in output
        assert "file=src/test.py" in output
        assert "line=10" in output
        assert "col=5" in output
        assert "title=Test Title" in output
        assert "Test message" in output


class TestParseReproReport:
    """Tests for parse_repro_report function."""

    def test_parse_valid_report(self, tmp_path: Path) -> None:
        """Test parsing a valid repro report."""
        report_path = tmp_path / "report.yaml"
        report_data = {
            "total_checks": 5,
            "passed_checks": 4,
            "failed_checks": 1,
            "checks": [
                {
                    "name": "Ruff Check",
                    "tool": "ruff",
                    "status": "passed",
                },
                {
                    "name": "Semgrep Check",
                    "tool": "semgrep",
                    "status": "failed",
                    "error": "Found issues",
                },
            ],
        }

        from specfact_cli.utils.yaml_utils import dump_yaml

        dump_yaml(report_data, report_path)

        result = parse_repro_report(report_path)
        assert isinstance(result, dict)
        assert result["total_checks"] == 5
        assert len(result["checks"]) == 2

    def test_parse_report_nonexistent_file(self, tmp_path: Path) -> None:
        """Test parsing a non-existent report file."""
        report_path = tmp_path / "nonexistent.yaml"
        # The contract requires the file to exist, so we expect a ViolationError
        # from the contract checker, not a ValueError
        with pytest.raises((ValueError, Exception)):  # Contract violation or ValueError
            parse_repro_report(report_path)

    def test_parse_report_invalid_yaml(self, tmp_path: Path) -> None:
        """Test parsing invalid YAML."""
        report_path = tmp_path / "invalid.yaml"
        report_path.write_text("invalid: yaml: content: [", encoding="utf-8")
        with pytest.raises(ValueError, match="Failed to parse"):
            parse_repro_report(report_path)

    def test_parse_report_not_dict(self, tmp_path: Path) -> None:
        """Test parsing YAML that's not a dictionary."""
        report_path = tmp_path / "not_dict.yaml"
        report_path.write_text("- item1\n- item2\n", encoding="utf-8")
        with pytest.raises(ValueError, match="Report must be a dictionary"):
            parse_repro_report(report_path)


class TestCreateAnnotationsFromReport:
    """Tests for create_annotations_from_report function."""

    @patch("specfact_cli.utils.github_annotations.create_annotation")
    def test_create_annotations_all_passed(self, mock_create: MagicMock) -> None:
        """Test creating annotations when all checks passed."""
        report = {
            "total_checks": 3,
            "passed_checks": 3,
            "failed_checks": 0,
            "timeout_checks": 0,
            "budget_exceeded": False,
            "checks": [
                {"name": "Check 1", "tool": "tool1", "status": "passed"},
                {"name": "Check 2", "tool": "tool2", "status": "passed"},
                {"name": "Check 3", "tool": "tool3", "status": "passed"},
            ],
        }

        result = create_annotations_from_report(report)
        assert result is False  # No failures
        assert mock_create.call_count == 1  # Only summary annotation

    @patch("specfact_cli.utils.github_annotations.create_annotation")
    def test_create_annotations_with_failures(self, mock_create: MagicMock) -> None:
        """Test creating annotations when checks failed."""
        report = {
            "total_checks": 3,
            "passed_checks": 1,
            "failed_checks": 2,
            "timeout_checks": 0,
            "budget_exceeded": False,
            "checks": [
                {"name": "Check 1", "tool": "tool1", "status": "passed"},
                {
                    "name": "Check 2",
                    "tool": "tool2",
                    "status": "failed",
                    "error": "Test error",
                },
                {
                    "name": "Check 3",
                    "tool": "tool3",
                    "status": "failed",
                    "output": "Test output",
                },
            ],
        }

        result = create_annotations_from_report(report)
        assert result is True  # Has failures
        assert mock_create.call_count == 3  # 2 failed checks + 1 summary

    @patch("specfact_cli.utils.github_annotations.create_annotation")
    def test_create_annotations_with_timeouts(self, mock_create: MagicMock) -> None:
        """Test creating annotations when checks timed out."""
        report = {
            "total_checks": 2,
            "passed_checks": 1,
            "failed_checks": 0,
            "timeout_checks": 1,
            "budget_exceeded": False,
            "checks": [
                {"name": "Check 1", "tool": "tool1", "status": "passed"},
                {"name": "Check 2", "tool": "tool2", "status": "timeout"},
            ],
        }

        result = create_annotations_from_report(report)
        assert result is True  # Has timeouts (treated as failures)
        assert mock_create.call_count == 2  # 1 timeout + 1 summary

    @patch("specfact_cli.utils.github_annotations.create_annotation")
    def test_create_annotations_budget_exceeded(self, mock_create: MagicMock) -> None:
        """Test creating annotations when budget exceeded."""
        report = {
            "total_checks": 2,
            "passed_checks": 1,
            "failed_checks": 0,
            "timeout_checks": 0,
            "budget_exceeded": True,
            "checks": [
                {"name": "Check 1", "tool": "tool1", "status": "passed"},
            ],
        }

        result = create_annotations_from_report(report)
        assert result is True  # Budget exceeded is a failure
        # Budget exceeded annotation + summary
        assert mock_create.call_count == 2


class TestGeneratePRComment:
    """Tests for generate_pr_comment function."""

    def test_generate_comment_all_passed(self) -> None:
        """Test generating PR comment when all checks passed."""
        report = {
            "total_checks": 5,
            "passed_checks": 5,
            "failed_checks": 0,
            "timeout_checks": 0,
            "skipped_checks": 0,
            "budget_exceeded": False,
            "total_duration": 10.5,
            "checks": [],
        }

        comment = generate_pr_comment(report)
        assert comment.startswith("## SpecFact CLI Validation Report")
        assert "✅ **All validations passed!**" in comment
        assert "**Duration**: 10.50s" in comment
        assert "**Checks**: 5 total (5 passed)" in comment

    def test_generate_comment_with_failures(self) -> None:
        """Test generating PR comment when checks failed."""
        report = {
            "total_checks": 5,
            "passed_checks": 3,
            "failed_checks": 2,
            "timeout_checks": 0,
            "skipped_checks": 0,
            "budget_exceeded": False,
            "total_duration": 15.2,
            "checks": [
                {
                    "name": "Ruff Check",
                    "tool": "ruff",
                    "status": "failed",
                    "error": "Found 5 linting errors",
                },
                {
                    "name": "Semgrep Check",
                    "tool": "semgrep",
                    "status": "failed",
                    "output": "Found 2 async anti-patterns",
                },
            ],
        }

        comment = generate_pr_comment(report)
        assert "❌ **Validation issues detected**" in comment
        assert "### ❌ Failed Checks" in comment
        assert "Ruff Check (ruff)" in comment
        assert "Semgrep Check (semgrep)" in comment
        assert "Found 5 linting errors" in comment
        assert "### 💡 Suggestions" in comment

    def test_generate_comment_with_timeouts(self) -> None:
        """Test generating PR comment when checks timed out."""
        report = {
            "total_checks": 3,
            "passed_checks": 1,
            "failed_checks": 0,
            "timeout_checks": 2,
            "skipped_checks": 0,
            "budget_exceeded": False,
            "total_duration": 90.0,
            "checks": [
                {"name": "Check 1", "tool": "tool1", "status": "passed"},
                {"name": "Check 2", "tool": "tool2", "status": "timeout"},
                {"name": "Check 3", "tool": "tool3", "status": "timeout"},
            ],
        }

        comment = generate_pr_comment(report)
        assert "### ⏱️ Timeout Checks" in comment
        assert "Check 2" in comment
        assert "tool2" in comment
        assert "Check 3" in comment
        assert "tool3" in comment

    def test_generate_comment_budget_exceeded(self) -> None:
        """Test generating PR comment when budget exceeded."""
        report = {
            "total_checks": 3,
            "passed_checks": 2,
            "failed_checks": 0,
            "timeout_checks": 0,
            "skipped_checks": 0,
            "budget_exceeded": True,
            "total_duration": 95.0,
            "checks": [],
        }

        comment = generate_pr_comment(report)
        assert "### ⚠️ Budget Exceeded" in comment
        assert "budget was exceeded" in comment

    def test_generate_comment_with_skipped_checks(self) -> None:
        """Test generating PR comment with skipped checks."""
        report = {
            "total_checks": 5,
            "passed_checks": 3,
            "failed_checks": 0,
            "timeout_checks": 0,
            "skipped_checks": 2,
            "budget_exceeded": False,
            "total_duration": 20.0,
            "checks": [],
        }

        comment = generate_pr_comment(report)
        assert "**Checks**: 5 total (3 passed) (2 skipped)" in comment

    def test_generate_comment_truncates_long_output(self) -> None:
        """Test that PR comment truncates very long output."""
        long_output = "x" * 3000
        report = {
            "total_checks": 1,
            "passed_checks": 0,
            "failed_checks": 1,
            "timeout_checks": 0,
            "skipped_checks": 0,
            "budget_exceeded": False,
            "total_duration": 5.0,
            "checks": [
                {
                    "name": "Test Check",
                    "tool": "test",
                    "status": "failed",
                    "output": long_output,
                },
            ],
        }

        comment = generate_pr_comment(report)
        assert "... (truncated)" in comment
        assert len(comment) < 5000  # Reasonable limit
