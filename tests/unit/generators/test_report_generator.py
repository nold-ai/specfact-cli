"""Unit tests for ReportGenerator.

Focus: Business logic and edge cases only (@beartype handles type validation).
"""

import pytest
from beartype.roar import BeartypeCallHintParamViolation

from specfact_cli.generators.report_generator import ReportFormat, ReportGenerator
from specfact_cli.models.deviation import Deviation, DeviationReport, DeviationSeverity, DeviationType, ValidationReport


class TestReportGenerator:
    """Test suite for ReportGenerator."""

    @pytest.fixture
    def sample_validation_report(self):
        """Create a sample validation report for testing."""
        report = ValidationReport()
        report.add_deviation(
            Deviation(
                type=DeviationType.FSM_MISMATCH,
                severity=DeviationSeverity.HIGH,
                description="Invalid transition detected",
                location="state_machine.py:42",
                fix_hint="Add missing transition from INIT to RUNNING",
            )
        )
        report.add_deviation(
            Deviation(
                type=DeviationType.MISSING_FEATURE,
                severity=DeviationSeverity.MEDIUM,
                description="Feature not implemented",
                location="features.py:15",
                fix_hint="Implement feature FEATURE-1",
            )
        )
        return report

    @pytest.fixture
    def sample_deviation_report(self):
        """Create a sample deviation report for testing."""
        return DeviationReport(
            manual_plan="/path/to/manual/plan.yaml",
            auto_plan="/path/to/auto/plan.yaml",
            deviations=[
                Deviation(
                    type=DeviationType.MISSING_FEATURE,
                    severity=DeviationSeverity.HIGH,
                    description="Feature missing from implementation",
                    location="api.py:100",
                    fix_hint="Implement missing feature",
                ),
                Deviation(
                    type=DeviationType.FSM_MISMATCH,
                    severity=DeviationSeverity.MEDIUM,
                    description="Unexpected state transition",
                    location="workflow.py:50",
                    fix_hint="Update state machine definition",
                ),
            ],
        )

    @pytest.fixture
    def generator(self):
        """Create a ReportGenerator instance."""
        return ReportGenerator()

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create a temporary output directory."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        return output_dir

    def test_generate_validation_report_markdown(self, generator, sample_validation_report, output_dir):
        """Test generating validation report in markdown format."""
        output_path = output_dir / "report.md"

        generator.generate_validation_report(sample_validation_report, output_path, ReportFormat.MARKDOWN)

        assert output_path.exists()
        content = output_path.read_text()
        assert "Validation Report" in content
        assert "PASSED" in content or "FAILED" in content
        assert "Invalid transition detected" in content
        assert "Feature not implemented" in content

    def test_generate_deviation_report_markdown(self, generator, sample_deviation_report, output_dir):
        """Test generating deviation report in markdown format."""
        output_path = output_dir / "deviations.md"

        generator.generate_deviation_report(sample_deviation_report, output_path, ReportFormat.MARKDOWN)

        assert output_path.exists()
        content = output_path.read_text()
        assert "Deviation Report" in content
        assert "/path/to/manual/plan.yaml" in content
        assert "Feature missing from implementation" in content

    def test_generate_creates_parent_dirs(self, generator, sample_validation_report, output_dir):
        """Test that generate creates parent directories if they don't exist."""
        output_path = output_dir / "nested" / "dirs" / "report.md"

        generator.generate_validation_report(sample_validation_report, output_path, ReportFormat.MARKDOWN)

        assert output_path.exists()
        assert output_path.parent.exists()

    def test_unsupported_format_raises_error(self, generator, sample_validation_report, output_dir):
        """Test that unsupported format is caught by @beartype contract (edge case)."""
        output_path = output_dir / "report.txt"

        # Contract-first: @beartype catches invalid type before ValueError
        with pytest.raises(BeartypeCallHintParamViolation):
            generator.generate_validation_report(sample_validation_report, output_path, "txt")  # type: ignore

    def test_markdown_report_includes_severity_counts(self, generator, sample_validation_report, output_dir):
        """Test that markdown report includes severity breakdown."""
        output_path = output_dir / "report.md"

        generator.generate_validation_report(sample_validation_report, output_path, ReportFormat.MARKDOWN)

        content = output_path.read_text()
        assert "HIGH:" in content
        assert "MEDIUM:" in content
        assert "Deviations by Severity" in content

    def test_markdown_report_groups_by_type(self, generator, sample_deviation_report, output_dir):
        """Test that markdown deviation report groups deviations by type."""
        output_path = output_dir / "deviations.md"

        generator.generate_deviation_report(sample_deviation_report, output_path, ReportFormat.MARKDOWN)

        content = output_path.read_text()
        assert "Deviations by Type" in content
        assert "missing_feature" in content
        assert "fsm_mismatch" in content
