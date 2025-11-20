"""Plan bundle generator using direct YAML serialization."""

from __future__ import annotations

from pathlib import Path

from beartype import beartype
from icontract import ensure, require
from jinja2 import Environment, FileSystemLoader

from specfact_cli.models.plan import PlanBundle
from specfact_cli.utils.structured_io import StructuredFormat, dump_structured_file, dumps_structured_data


class PlanGenerator:
    """
    Generator for plan bundle YAML files.

    Uses direct YAML serialization for reliable output.
    """

    @beartype
    def __init__(self, templates_dir: Path | None = None) -> None:
        """
        Initialize plan generator.

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
    @require(lambda plan_bundle: isinstance(plan_bundle, PlanBundle), "Must be PlanBundle instance")
    @require(lambda output_path: output_path is not None, "Output path must not be None")
    @ensure(lambda output_path: output_path.exists(), "Output file must exist after generation")
    def generate(
        self,
        plan_bundle: PlanBundle,
        output_path: Path,
        update_summary: bool = True,
        format: StructuredFormat | None = None,
    ) -> None:
        """
        Generate plan bundle YAML file from model.

        Args:
            plan_bundle: PlanBundle model to generate from
            output_path: Path to write the generated YAML file
            update_summary: Whether to update summary metadata before writing (default: True)

        Raises:
            IOError: If unable to write output file
        """
        # Update summary metadata before writing (for fast access without full parsing)
        if update_summary:
            # Include hash for integrity verification (only when writing, not when reading)
            plan_bundle.update_summary(include_hash=True)

        # Ensure version is set to current schema version
        from specfact_cli.migrations.plan_migrator import get_current_schema_version

        plan_bundle.version = get_current_schema_version()

        # Convert model to dict, excluding None values
        plan_data = plan_bundle.model_dump(exclude_none=True)

        # Write to file using YAML dump
        resolved_format = format or StructuredFormat.from_path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        dump_structured_file(plan_data, output_path, resolved_format)

    @beartype
    @require(
        lambda template_name: isinstance(template_name, str) and len(template_name) > 0,
        "Template name must be non-empty string",
    )
    @require(lambda context: isinstance(context, dict), "Context must be dictionary")
    @require(lambda output_path: output_path is not None, "Output path must not be None")
    @ensure(lambda output_path: output_path.exists(), "Output file must exist after generation")
    def generate_from_template(self, template_name: str, context: dict, output_path: Path) -> None:
        """
        Generate file from custom template.

        Args:
            template_name: Name of the template file
            context: Context dictionary for template rendering
            output_path: Path to write the generated file

        Raises:
            FileNotFoundError: If template file doesn't exist
            IOError: If unable to write output file
        """
        template = self.env.get_template(template_name)
        rendered = template.render(**context)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")

    @beartype
    @require(lambda plan_bundle: isinstance(plan_bundle, PlanBundle), "Must be PlanBundle instance")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    @ensure(lambda result: len(result) > 0, "Result must be non-empty")
    def render_string(self, plan_bundle: PlanBundle, format: StructuredFormat = StructuredFormat.YAML) -> str:
        """
        Render plan bundle to YAML string without writing to file.

        Args:
            plan_bundle: PlanBundle model to render

        Returns:
            Rendered YAML string
        """
        plan_data = plan_bundle.model_dump(exclude_none=True)
        return dumps_structured_data(plan_data, format)
