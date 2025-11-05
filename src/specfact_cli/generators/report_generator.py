"""Report generator for validation reports and deviation reports."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path

from beartype import beartype
from icontract import ensure, require
from jinja2 import Environment, FileSystemLoader

from specfact_cli.models.deviation import Deviation, DeviationReport, ValidationReport
from specfact_cli.utils.yaml_utils import dump_yaml


class ReportFormat(str, Enum):
    """Report output format."""

    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"


class ReportGenerator:
    """
    Generator for validation and deviation reports.

    Supports multiple output formats: Markdown, JSON, YAML.
    """

    @beartype
    def __init__(self, templates_dir: Path | None = None) -> None:
        """
        Initialize report generator.

        Args:
            templates_dir: Directory containing Jinja2 templates (default: resources/templates)
        """
        if templates_dir is None:
            # Default to resources/templates relative to project root
            templates_dir = Path(__file__).parent.parent.parent.parent / "resources" / "templates"

        self.templates_dir = Path(templates_dir)
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    @beartype
    @require(lambda report: isinstance(report, ValidationReport), "Must be ValidationReport instance")
    @require(lambda output_path: output_path is not None, "Output path must not be None")
    @require(lambda format: format in ReportFormat, "Format must be valid ReportFormat")
    @ensure(lambda output_path: output_path.exists(), "Output file must exist after generation")
    def generate_validation_report(
        self, report: ValidationReport, output_path: Path, format: ReportFormat = ReportFormat.MARKDOWN
    ) -> None:
        """
        Generate validation report file.

        Args:
            report: ValidationReport model to generate from
            output_path: Path to write the generated report file
            format: Output format (markdown, json, yaml)

        Raises:
            ValueError: If format is unsupported
            IOError: If unable to write output file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == ReportFormat.MARKDOWN:
            self._generate_markdown_report(report, output_path)
        elif format == ReportFormat.JSON:
            self._generate_json_report(report, output_path)
        elif format == ReportFormat.YAML:
            self._generate_yaml_report(report, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    @beartype
    @require(lambda report: isinstance(report, DeviationReport), "Must be DeviationReport instance")
    @require(lambda output_path: output_path is not None, "Output path must not be None")
    @require(lambda format: format in ReportFormat, "Format must be valid ReportFormat")
    @ensure(lambda output_path: output_path.exists(), "Output file must exist after generation")
    def generate_deviation_report(
        self, report: DeviationReport, output_path: Path, format: ReportFormat = ReportFormat.MARKDOWN
    ) -> None:
        """
        Generate deviation report file.

        Args:
            report: DeviationReport model to generate from
            output_path: Path to write the generated report file
            format: Output format (markdown, json, yaml)

        Raises:
            ValueError: If format is unsupported
            IOError: If unable to write output file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == ReportFormat.MARKDOWN:
            self._generate_deviation_markdown(report, output_path)
        elif format == ReportFormat.JSON:
            self._generate_json_report(report, output_path)
        elif format == ReportFormat.YAML:
            self._generate_yaml_report(report, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_markdown_report(self, report: ValidationReport, output_path: Path) -> None:
        """Generate markdown validation report."""
        lines: list[str] = []
        lines.append("# Validation Report\n")
        lines.append(f"**Status**: {'✅ PASSED' if report.passed else '❌ FAILED'}\n")
        total_count = len(report.deviations)
        lines.append(f"**Total Deviations**: {total_count}\n")

        if total_count > 0:
            lines.append("\n## Deviations by Severity\n")
            lines.append(f"- 🔴 **HIGH**: {report.high_count}")
            lines.append(f"- 🟡 **MEDIUM**: {report.medium_count}")
            lines.append(f"- 🔵 **LOW**: {report.low_count}\n")

            lines.append("\n## Detailed Deviations\n")
            for deviation in report.deviations:
                lines.append(f"### {deviation.severity.value.upper()}: {deviation.description}\n")
                if deviation.location:
                    lines.append(f"**Location**: `{deviation.location}`\n")
                if deviation.fix_hint:
                    lines.append(f"**Fix Hint**: {deviation.fix_hint}\n")
                lines.append("")

        output_path.write_text("\n".join(lines), encoding="utf-8")

    def _generate_deviation_markdown(self, report: DeviationReport, output_path: Path) -> None:
        """Generate markdown deviation report."""
        lines: list[str] = []
        lines.append("# Deviation Report\n")
        lines.append(f"**Manual Plan**: {report.manual_plan}")
        lines.append(f"**Auto Plan**: {report.auto_plan}")
        lines.append(f"**Total Deviations**: {len(report.deviations)}\n")

        # Group by type
        by_type: dict[str, list[Deviation]] = {}
        for deviation in report.deviations:
            type_key = deviation.type.value
            if type_key not in by_type:
                by_type[type_key] = []
            by_type[type_key].append(deviation)

        lines.append("\n## Deviations by Type\n")
        for type_key, devs in by_type.items():
            lines.append(f"### {type_key} ({len(devs)} issues)\n")
            for dev in devs:
                lines.append(f"- **{dev.severity.value.upper()}**: {dev.description}")
                if dev.location:
                    lines.append(f"  - Location: `{dev.location}`")
                if dev.fix_hint:
                    lines.append(f"  - Fix: {dev.fix_hint}")
                lines.append("")

        output_path.write_text("\n".join(lines), encoding="utf-8")

    def _generate_json_report(self, report: ValidationReport | DeviationReport, output_path: Path) -> None:
        """Generate JSON report."""
        report_data = report.model_dump(mode="json")
        output_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")

    def _generate_yaml_report(self, report: ValidationReport | DeviationReport, output_path: Path) -> None:
        """Generate YAML report."""
        dump_yaml(report.model_dump(mode="json"), output_path)

    def render_markdown_string(self, report: ValidationReport | DeviationReport) -> str:
        """
        Render report to markdown string without writing to file.

        Args:
            report: ValidationReport or DeviationReport model to render

        Returns:
            Rendered markdown string
        """
        from io import StringIO

        output = StringIO()

        if isinstance(report, ValidationReport):
            output.write("# Validation Report\n\n")
            output.write(f"**Status**: {'✅ PASSED' if report.passed else '❌ FAILED'}\n\n")
            output.write(f"**Total Deviations**: {len(report.deviations)}\n\n")
        elif isinstance(report, DeviationReport):
            output.write("# Deviation Report\n\n")
            output.write(f"**Manual Plan**: {report.manual_plan}\n")
            output.write(f"**Auto Plan**: {report.auto_plan}\n")
            output.write(f"**Total Deviations**: {len(report.deviations)}\n\n")

        return output.getvalue()
