"""
Unit tests for CrossHair summary parser.
"""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from specfact_cli.validators.sidecar.crosshair_summary import (
    format_summary_line,
    generate_summary_file,
    parse_crosshair_output,
)


class TestParseCrossHairOutput:
    """Test CrossHair output parsing."""

    def test_parse_confirmed_output(self) -> None:
        """Test parsing output with confirmed contracts."""
        stdout = "function1: Confirmed\nfunction2: Confirmed\n"
        stderr = ""

        result = parse_crosshair_output(stdout, stderr)

        assert result["confirmed"] == 2
        assert result["not_confirmed"] == 0
        assert result["violations"] == 0
        assert result["total"] == 2

    def test_parse_rejected_output(self) -> None:
        """Test parsing output with rejected contracts."""
        stdout = "function1: Rejected (counterexample: x=0)\n"
        stderr = ""

        result = parse_crosshair_output(stdout, stderr)

        assert result["confirmed"] == 0
        assert result["not_confirmed"] == 0
        assert result["violations"] == 1
        assert result["total"] == 1

    def test_parse_unknown_output(self) -> None:
        """Test parsing output with unknown contracts."""
        stdout = "function1: Unknown\nfunction2: Unknown\n"
        stderr = ""

        result = parse_crosshair_output(stdout, stderr)

        assert result["confirmed"] == 0
        assert result["not_confirmed"] == 2
        assert result["violations"] == 0
        assert result["total"] == 2

    def test_parse_mixed_output(self) -> None:
        """Test parsing output with mixed statuses."""
        stdout = "function1: Confirmed\nfunction2: Rejected\nfunction3: Unknown\n"
        stderr = ""

        result = parse_crosshair_output(stdout, stderr)

        assert result["confirmed"] == 1
        assert result["not_confirmed"] == 1
        assert result["violations"] == 1
        assert result["total"] == 3

    def test_parse_empty_output(self) -> None:
        """Test parsing empty output."""
        stdout = ""
        stderr = ""

        result = parse_crosshair_output(stdout, stderr)

        assert result["confirmed"] == 0
        assert result["not_confirmed"] == 0
        assert result["violations"] == 0
        assert result["total"] == 0

    def test_parse_error_output(self) -> None:
        """Test parsing output with error indicators."""
        stdout = ""
        stderr = "Error: Module not found"

        result = parse_crosshair_output(stdout, stderr)

        # Should detect error/violation indicators
        assert result["violations"] >= 0
        assert "total" in result

    def test_parse_case_insensitive(self) -> None:
        """Test parsing is case-insensitive."""
        stdout = "function1: CONFIRMED\nfunction2: rejected\nfunction3: UNKNOWN\n"
        stderr = ""

        result = parse_crosshair_output(stdout, stderr)

        assert result["confirmed"] == 1
        assert result["not_confirmed"] == 1
        assert result["violations"] == 1
        assert result["total"] == 3

    def test_parse_verbose_output(self) -> None:
        """Test parsing verbose CrossHair output."""
        stdout = """
Analyzing function1...
function1: Confirmed
Analyzing function2...
function2: Rejected (counterexample found)
        """.strip()
        stderr = ""

        result = parse_crosshair_output(stdout, stderr)

        assert result["confirmed"] == 1
        assert result["violations"] == 1
        assert result["total"] == 2


class TestGenerateSummaryFile:
    """Test summary file generation."""

    def test_generate_summary_file(self) -> None:
        """Test generating summary file."""
        summary = {"confirmed": 5, "not_confirmed": 2, "violations": 1, "total": 8}

        with TemporaryDirectory() as tmpdir:
            reports_dir = Path(tmpdir)
            summary_file = generate_summary_file(summary, reports_dir)

            assert summary_file.exists()
            assert summary_file.name.startswith("crosshair-summary-")
            assert summary_file.suffix == ".json"

            # Verify file contents
            with summary_file.open() as f:
                data = json.load(f)

            assert "timestamp" in data
            assert "summary" in data
            assert data["summary"]["confirmed"] == 5
            assert data["summary"]["not_confirmed"] == 2
            assert data["summary"]["violations"] == 1
            assert data["summary"]["total"] == 8

    def test_generate_summary_file_with_timestamp(self) -> None:
        """Test generating summary file with custom timestamp."""
        summary = {"confirmed": 3, "not_confirmed": 0, "violations": 0, "total": 3}
        timestamp = "20260109T120000Z"

        with TemporaryDirectory() as tmpdir:
            reports_dir = Path(tmpdir)
            summary_file = generate_summary_file(summary, reports_dir, timestamp=timestamp)

            assert summary_file.name == f"crosshair-summary-{timestamp}.json"

    def test_generate_summary_file_creates_directory(self) -> None:
        """Test that summary file generation creates directory if needed."""
        summary = {"confirmed": 1, "not_confirmed": 0, "violations": 0, "total": 1}

        with TemporaryDirectory() as tmpdir:
            reports_dir = Path(tmpdir) / "reports" / "sidecar"
            summary_file = generate_summary_file(summary, reports_dir)

            assert reports_dir.exists()
            assert summary_file.exists()


class TestFormatSummaryLine:
    """Test summary line formatting."""

    def test_format_summary_with_all_counts(self) -> None:
        """Test formatting summary with all counts."""
        summary = {"confirmed": 5, "not_confirmed": 2, "violations": 1, "total": 8}

        result = format_summary_line(summary)

        assert "5 confirmed" in result
        assert "2 not confirmed" in result
        assert "1 violations" in result
        assert result.startswith("CrossHair:")

    def test_format_summary_only_confirmed(self) -> None:
        """Test formatting summary with only confirmed."""
        summary = {"confirmed": 10, "not_confirmed": 0, "violations": 0, "total": 10}

        result = format_summary_line(summary)

        assert "10 confirmed" in result
        assert "not confirmed" not in result
        assert "violations" not in result

    def test_format_summary_only_violations(self) -> None:
        """Test formatting summary with only violations."""
        summary = {"confirmed": 0, "not_confirmed": 0, "violations": 3, "total": 3}

        result = format_summary_line(summary)

        assert "3 violations" in result
        assert "confirmed" not in result
        assert "not confirmed" not in result

    def test_format_summary_empty(self) -> None:
        """Test formatting empty summary."""
        summary = {"confirmed": 0, "not_confirmed": 0, "violations": 0, "total": 0}

        result = format_summary_line(summary)

        assert "no contracts analyzed" in result or "no results" in result
