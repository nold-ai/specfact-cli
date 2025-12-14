"""
Persona exporter for generating Markdown artifacts from project bundles.

This module provides functionality to export persona-owned sections from project
bundles to well-structured Markdown files using Jinja2 templates.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound

from specfact_cli.models.project import PersonaMapping, ProjectBundle


class PersonaExporter:
    """
    Exporter for persona-specific Markdown artifacts.

    Uses Jinja2 templates to generate structured Markdown files from project
    bundle data, filtered by persona ownership.
    """

    @beartype
    @require(
        lambda templates_dir: templates_dir is None or (isinstance(templates_dir, Path) and templates_dir.exists()),
        "Templates dir must exist if provided",
    )
    def __init__(self, templates_dir: Path | None = None, project_templates_dir: Path | None = None) -> None:
        """
        Initialize persona exporter.

        Args:
            templates_dir: Directory containing default templates (default: resources/templates/persona)
            project_templates_dir: Directory containing project-specific template overrides (default: .specfact/templates/persona)
        """
        if templates_dir is None:
            # Default to resources/templates/persona
            # Try multiple locations to handle both development and installed scenarios
            package_root = Path(__file__).parent.parent.parent  # specfact_cli/

            # Possible template locations (in order of preference):
            # 1. Installed package: specfact_cli/resources/templates/persona (when package data is included)
            # 2. Development source: <project_root>/resources/templates/persona
            # 3. Legacy path calculation
            possible_paths = [
                package_root
                / "resources"
                / "templates"
                / "persona",  # Installed package (specfact_cli/resources/templates/persona)
                package_root.parent.parent
                / "resources"
                / "templates"
                / "persona",  # Development source (resources/templates/persona from src/)
                Path(__file__).parent.parent.parent.parent
                / "resources"
                / "templates"
                / "persona",  # Legacy path (from generators/)
            ]

            # Find first existing path with template files
            templates_dir = None
            for path in possible_paths:
                path_obj = Path(path)
                if path_obj.exists() and any(path_obj.glob("*.md.j2")):
                    templates_dir = path_obj
                    break

            if templates_dir is None:
                # Fallback to package location (will raise error if templates missing)
                templates_dir = possible_paths[0]

        self.templates_dir = Path(templates_dir)
        self.project_templates_dir = project_templates_dir

        # Create Jinja2 environment with fallback support
        self.env = Environment(
            loader=FileSystemLoader(
                [str(self.templates_dir)] + ([str(self.project_templates_dir)] if project_templates_dir else [])
            ),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    @beartype
    @require(lambda bundle: isinstance(bundle, ProjectBundle), "Bundle must be ProjectBundle")
    @require(
        lambda persona_mapping: isinstance(persona_mapping, PersonaMapping), "Persona mapping must be PersonaMapping"
    )
    @require(lambda persona_name: isinstance(persona_name, str), "Persona name must be str")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def prepare_template_context(
        self, bundle: ProjectBundle, persona_mapping: PersonaMapping, persona_name: str
    ) -> dict[str, Any]:
        """
        Prepare template context from bundle data filtered by persona ownership.

        Args:
            bundle: Project bundle to export
            persona_mapping: Persona mapping with owned sections
            persona_name: Persona name

        Returns:
            Template context dictionary
        """
        from specfact_cli.commands.project_cmd import match_section_pattern

        context: dict[str, Any] = {
            "bundle_name": bundle.bundle_name,
            "persona_name": persona_name,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),  # Use current time as manifest doesn't track this
            "status": "active",
        }

        # Filter idea if persona owns it
        if bundle.idea and any(match_section_pattern(p, "idea") for p in persona_mapping.owns):
            context["idea"] = bundle.idea.model_dump()

        # Filter business if persona owns it
        if bundle.business and any(match_section_pattern(p, "business") for p in persona_mapping.owns):
            context["business"] = bundle.business.model_dump()

        # Filter product if persona owns it
        if any(match_section_pattern(p, "product") for p in persona_mapping.owns):
            context["product"] = bundle.product.model_dump() if bundle.product else None

        # Filter features by persona ownership
        filtered_features: dict[str, Any] = {}
        for feature_key, feature in bundle.features.items():
            feature_dict: dict[str, Any] = {"key": feature.key, "title": feature.title}

            # Feature model doesn't have description, but may have outcomes
            if feature.outcomes:
                feature_dict["outcomes"] = feature.outcomes

            # Include all feature fields (prioritization, business value, dependencies, planning)
            if hasattr(feature, "priority") and feature.priority:
                feature_dict["priority"] = feature.priority
            if hasattr(feature, "rank") and feature.rank is not None:
                feature_dict["rank"] = feature.rank
            if hasattr(feature, "business_value_score") and feature.business_value_score is not None:
                feature_dict["business_value_score"] = feature.business_value_score
            if hasattr(feature, "target_release") and feature.target_release:
                feature_dict["target_release"] = feature.target_release
            if hasattr(feature, "business_value_description") and feature.business_value_description:
                feature_dict["business_value_description"] = feature.business_value_description
            if hasattr(feature, "target_users") and feature.target_users:
                feature_dict["target_users"] = feature.target_users
            if hasattr(feature, "success_metrics") and feature.success_metrics:
                feature_dict["success_metrics"] = feature.success_metrics
            if hasattr(feature, "depends_on_features") and feature.depends_on_features:
                feature_dict["depends_on_features"] = feature.depends_on_features
            if hasattr(feature, "blocks_features") and feature.blocks_features:
                feature_dict["blocks_features"] = feature.blocks_features

            # Filter stories if persona owns stories
            if any(match_section_pattern(p, "features.*.stories") for p in persona_mapping.owns) and feature.stories:
                story_dicts = []
                total_story_points = 0
                for story in feature.stories:
                    story_dict = story.model_dump()
                    # Calculate DoR completion status
                    dor_status: dict[str, bool] = {}
                    if hasattr(story, "story_points"):
                        dor_status["story_points"] = story.story_points is not None
                    if hasattr(story, "value_points"):
                        dor_status["value_points"] = story.value_points is not None
                    if hasattr(story, "priority"):
                        dor_status["priority"] = story.priority is not None
                    if hasattr(story, "depends_on_stories") and hasattr(story, "blocks_stories"):
                        dor_status["dependencies"] = len(story.depends_on_stories) > 0 or len(story.blocks_stories) > 0
                    if hasattr(story, "business_value_description"):
                        dor_status["business_value"] = story.business_value_description is not None
                    if hasattr(story, "due_date"):
                        dor_status["target_date"] = story.due_date is not None
                    if hasattr(story, "target_sprint"):
                        dor_status["target_sprint"] = story.target_sprint is not None
                    story_dict["definition_of_ready"] = dor_status

                    # Include developer-specific fields (tasks, scenarios, contracts, source/test functions)
                    # These are always included if they exist, regardless of persona ownership
                    # (developers need this info to implement)
                    if hasattr(story, "tasks") and story.tasks:
                        story_dict["tasks"] = story.tasks
                    if hasattr(story, "scenarios") and story.scenarios:
                        story_dict["scenarios"] = story.scenarios
                    if hasattr(story, "contracts") and story.contracts:
                        story_dict["contracts"] = story.contracts
                    if hasattr(story, "source_functions") and story.source_functions:
                        story_dict["source_functions"] = story.source_functions
                    if hasattr(story, "test_functions") and story.test_functions:
                        story_dict["test_functions"] = story.test_functions

                    story_dicts.append(story_dict)
                    # Sum story points for feature total
                    if hasattr(story, "story_points") and story.story_points is not None:
                        total_story_points += story.story_points
                feature_dict["stories"] = story_dicts
                # Set estimated story points (sum of all stories)
                feature_dict["estimated_story_points"] = total_story_points if total_story_points > 0 else None

            # Filter outcomes if persona owns outcomes
            if any(match_section_pattern(p, "features.*.outcomes") for p in persona_mapping.owns) and feature.outcomes:
                feature_dict["outcomes"] = feature.outcomes

            # Filter constraints if persona owns constraints
            if (
                any(match_section_pattern(p, "features.*.constraints") for p in persona_mapping.owns)
                and feature.constraints
            ):
                feature_dict["constraints"] = feature.constraints

            # Filter acceptance if persona owns acceptance
            if (
                any(match_section_pattern(p, "features.*.acceptance") for p in persona_mapping.owns)
                and feature.acceptance
            ):
                feature_dict["acceptance"] = feature.acceptance

            # Filter implementation if persona owns implementation
            # Note: Feature model doesn't have implementation field yet, but we check for it for future compatibility
            if any(match_section_pattern(p, "features.*.implementation") for p in persona_mapping.owns):
                implementation = getattr(feature, "implementation", None)
                if implementation:
                    feature_dict["implementation"] = implementation

            if feature_dict:
                filtered_features[feature_key] = feature_dict

        if filtered_features:
            context["features"] = filtered_features

        # Load protocols and contracts from bundle directory if persona owns them
        protocols: dict[str, Any] = {}
        contracts: dict[str, Any] = {}

        # Check if persona owns protocols or contracts
        owns_protocols = any(match_section_pattern(p, "protocols") for p in persona_mapping.owns)
        owns_contracts = any(match_section_pattern(p, "contracts") for p in persona_mapping.owns)

        if owns_protocols or owns_contracts:
            # Get bundle directory path (construct directly to avoid type checker issues)
            from specfact_cli.utils.structure import SpecFactStructure

            # Construct path directly: .specfact/projects/<bundle_name>/
            bundle_dir = Path(".") / SpecFactStructure.PROJECTS / bundle.bundle_name

            if bundle_dir.exists():
                # Load protocols if persona owns them
                if owns_protocols:
                    protocols_dir = bundle_dir / "protocols"
                    if protocols_dir.exists():
                        from specfact_cli.utils.structured_io import load_structured_file

                        for protocol_file in protocols_dir.glob("*.yaml"):
                            try:
                                protocol_data = load_structured_file(protocol_file)
                                protocol_name = protocol_file.stem.replace(".protocol", "")
                                protocols[protocol_name] = protocol_data
                            except Exception:
                                # Skip invalid protocol files
                                pass

                # Load contracts if persona owns them
                if owns_contracts:
                    contracts_dir = bundle_dir / "contracts"
                    if contracts_dir.exists():
                        from specfact_cli.utils.structured_io import load_structured_file

                        for contract_file in contracts_dir.glob("*.yaml"):
                            try:
                                contract_data = load_structured_file(contract_file)
                                contract_name = contract_file.stem.replace(".openapi", "").replace(".asyncapi", "")
                                contracts[contract_name] = contract_data
                            except Exception:
                                # Skip invalid contract files
                                pass

        context["protocols"] = protocols
        context["contracts"] = contracts

        # Add locks information
        context["locks"] = [lock.model_dump() for lock in bundle.manifest.locks]

        return context

    @beartype
    @require(lambda persona_name: isinstance(persona_name, str), "Persona name must be str")
    @ensure(lambda result: isinstance(result, Template), "Must return Template")
    def get_template(self, persona_name: str) -> Template:
        """
        Get template for persona.

        Args:
            persona_name: Persona name

        Returns:
            Jinja2 template

        Raises:
            TemplateNotFound: If template doesn't exist
        """
        template_name = f"{persona_name}.md.j2"
        try:
            return self.env.get_template(template_name)
        except TemplateNotFound as err:
            # Try default template
            default_template = self.templates_dir / "default.md.j2"
            if default_template.exists():
                return self.env.get_template("default.md.j2")
            raise FileNotFoundError(
                f"Template not found for persona '{persona_name}' and no default template available"
            ) from err

    @beartype
    @require(lambda bundle: isinstance(bundle, ProjectBundle), "Bundle must be ProjectBundle")
    @require(
        lambda persona_mapping: isinstance(persona_mapping, PersonaMapping), "Persona mapping must be PersonaMapping"
    )
    @require(lambda persona_name: isinstance(persona_name, str), "Persona name must be str")
    @require(lambda output_path: isinstance(output_path, Path), "Output path must be Path")
    @ensure(lambda result: result is None, "Must return None")
    def export_to_file(
        self, bundle: ProjectBundle, persona_mapping: PersonaMapping, persona_name: str, output_path: Path
    ) -> None:
        """
        Export persona-owned sections to Markdown file.

        Args:
            bundle: Project bundle to export
            persona_mapping: Persona mapping with owned sections
            persona_name: Persona name
            output_path: Path to write Markdown file
        """
        context = self.prepare_template_context(bundle, persona_mapping, persona_name)
        template = self.get_template(persona_name)
        rendered = template.render(**context)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")

    @beartype
    @require(lambda bundle: isinstance(bundle, ProjectBundle), "Bundle must be ProjectBundle")
    @require(
        lambda persona_mapping: isinstance(persona_mapping, PersonaMapping), "Persona mapping must be PersonaMapping"
    )
    @require(lambda persona_name: isinstance(persona_name, str), "Persona name must be str")
    @ensure(lambda result: isinstance(result, str), "Must return str")
    def export_to_string(self, bundle: ProjectBundle, persona_mapping: PersonaMapping, persona_name: str) -> str:
        """
        Export persona-owned sections to Markdown string.

        Args:
            bundle: Project bundle to export
            persona_mapping: Persona mapping with owned sections
            persona_name: Persona name

        Returns:
            Rendered Markdown string
        """
        context = self.prepare_template_context(bundle, persona_mapping, persona_name)
        template = self.get_template(persona_name)
        return template.render(**context)
