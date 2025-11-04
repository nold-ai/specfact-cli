"""Protocol generator using Jinja2 templates."""

from __future__ import annotations

from pathlib import Path

from beartype import beartype
from icontract import ensure, require
from jinja2 import Environment, FileSystemLoader

from specfact_cli.models.protocol import Protocol


class ProtocolGenerator:
    """
    Generator for protocol YAML files.

    Uses Jinja2 templates to render protocols from Protocol models.
    """

    @beartype
    def __init__(self, templates_dir: Path | None = None) -> None:
        """
        Initialize protocol generator.

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
    @require(lambda protocol: isinstance(protocol, Protocol), "Must be Protocol instance")
    @require(lambda output_path: output_path is not None, "Output path must not be None")
    @require(lambda protocol: len(protocol.states) > 0, "Protocol must have at least one state")
    @ensure(lambda output_path: output_path.exists(), "Output file must exist after generation")
    def generate(self, protocol: Protocol, output_path: Path) -> None:
        """
        Generate protocol YAML file from model.

        Args:
            protocol: Protocol model to generate from
            output_path: Path to write the generated YAML file

        Raises:
            FileNotFoundError: If template file doesn't exist
            IOError: If unable to write output file
        """
        # Convert model to dict, excluding None values
        protocol_data = protocol.model_dump(exclude_none=True, mode="json")

        # Render template
        template = self.env.get_template("protocol.yaml.j2")
        rendered = template.render(**protocol_data)

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")

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
    @require(lambda protocol: isinstance(protocol, Protocol), "Must be Protocol instance")
    @require(lambda protocol: len(protocol.states) > 0, "Protocol must have at least one state")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    @ensure(lambda result: len(result) > 0, "Result must be non-empty")
    def render_string(self, protocol: Protocol) -> str:
        """
        Render protocol to YAML string without writing to file.

        Args:
            protocol: Protocol model to render

        Returns:
            Rendered YAML string

        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        protocol_data = protocol.model_dump(exclude_none=True, mode="json")
        template = self.env.get_template("protocol.yaml.j2")
        return template.render(**protocol_data)
