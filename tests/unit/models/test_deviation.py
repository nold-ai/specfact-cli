"""
Unit tests for deviation data models.

Focus: Business logic and edge cases only (Pydantic handles type/field validation).
"""

from specfact_cli.models.deviation import (
    Deviation,
    DeviationSeverity,
    DeviationType,
    ValidationReport,
)


class TestValidationReport:
    """Tests for ValidationReport model."""

    def test_validation_report_add_deviation(self):
        """Test ValidationReport.add_deviation() method."""
        report = ValidationReport()

        # Add HIGH severity
        report.add_deviation(
            Deviation(
                type=DeviationType.MISSING_FEATURE,
                severity=DeviationSeverity.HIGH,
                description="High severity issue",
                location="test",
                fix_hint=None,
            )
        )

        assert report.high_count == 1
        assert report.passed is False

        # Add MEDIUM severity
        report.add_deviation(
            Deviation(
                type=DeviationType.ACCEPTANCE_DRIFT,
                severity=DeviationSeverity.MEDIUM,
                description="Medium severity issue",
                location="test",
                fix_hint=None,
            )
        )

        assert report.medium_count == 1

        # Add LOW severity
        report.add_deviation(
            Deviation(
                type=DeviationType.EXTRA_STORY,
                severity=DeviationSeverity.LOW,
                description="Low severity issue",
                location="test",
                fix_hint=None,
            )
        )

        assert report.low_count == 1
        assert len(report.deviations) == 3

    def test_validation_report_passed_logic(self):
        """Test ValidationReport passed logic."""
        report = ValidationReport()

        # Initially passes
        assert report.passed is True

        # Adding LOW doesn't fail
        report.add_deviation(
            Deviation(
                type=DeviationType.EXTRA_STORY,
                severity=DeviationSeverity.LOW,
                description="Low",
                location="test",
                fix_hint=None,
            )
        )
        assert report.passed is True

        # Adding MEDIUM doesn't fail
        report.add_deviation(
            Deviation(
                type=DeviationType.ACCEPTANCE_DRIFT,
                severity=DeviationSeverity.MEDIUM,
                description="Medium",
                location="test",
                fix_hint=None,
            )
        )
        assert report.passed is True

        # Adding HIGH fails
        report.add_deviation(
            Deviation(
                type=DeviationType.MISSING_FEATURE,
                severity=DeviationSeverity.HIGH,
                description="High",
                location="test",
                fix_hint=None,
            )
        )
        assert report.passed is False
