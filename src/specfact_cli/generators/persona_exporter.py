"""
Persona exporter for generating Markdown artifacts from project bundles.

This module provides functionality to export persona-owned sections from project
bundles to well-structured Markdown files using Jinja2 templates.
"""

from __future__ import annotations

from collections.abc import Sequence
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

    @staticmethod
    def _dor_status_for_story(story: Any) -> dict[str, bool]:
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
        return dor_status

    @staticmethod
    def _merge_nonempty_story_fields(story: Any, story_dict: dict[str, Any]) -> None:
        for field in ("tasks", "scenarios", "contracts", "source_functions", "test_functions"):
            if hasattr(story, field) and getattr(story, field):
                story_dict[field] = getattr(story, field)

    def _build_story_dict(self, story: Any) -> tuple[dict[str, Any], int]:
        """
        Build the template dictionary for a single story, including DoR status.

        Args:
            story: Story model instance

        Returns:
            Tuple of (story_dict, story_points) where story_points is 0 if not set
        """
        story_dict = story.model_dump()
        story_dict["definition_of_ready"] = self._dor_status_for_story(story)
        self._merge_nonempty_story_fields(story, story_dict)
        points = story.story_points if (hasattr(story, "story_points") and story.story_points is not None) else 0
        return story_dict, points

    def _build_feature_dict(self, feature: Any, persona_mapping: PersonaMapping) -> dict[str, Any]:
        """
        Build the template dictionary for a single feature with persona-owned sections filtered in.

        Args:
            feature: Feature model instance from the bundle
            persona_mapping: Persona mapping with owned sections

        Returns:
            Feature context dictionary
        """

        feature_dict: dict[str, Any] = {"key": feature.key, "title": feature.title}
        if feature.outcomes:
            feature_dict["outcomes"] = feature.outcomes
        self._merge_feature_scalar_fields(feature, feature_dict)
        self._merge_feature_stories_if_owned(feature, persona_mapping, feature_dict)
        self._merge_feature_optional_sections(feature, persona_mapping, feature_dict)
        return feature_dict

    def _merge_feature_scalar_fields(self, feature: Any, feature_dict: dict[str, Any]) -> None:
        for field in (
            "priority",
            "rank",
            "business_value_score",
            "target_release",
            "business_value_description",
            "target_users",
            "success_metrics",
            "depends_on_features",
            "blocks_features",
        ):
            value = getattr(feature, field, None)
            if value is not None and value != [] and value != "":
                feature_dict[field] = value

    def _merge_feature_stories_if_owned(
        self, feature: Any, persona_mapping: PersonaMapping, feature_dict: dict[str, Any]
    ) -> None:
        from specfact_cli.utils.persona_ownership import match_section_pattern

        if not (any(match_section_pattern(p, "features.*.stories") for p in persona_mapping.owns) and feature.stories):
            return
        story_dicts: list[dict[str, Any]] = []
        total_story_points = 0
        for story in feature.stories:
            story_dict, points = self._build_story_dict(story)
            story_dicts.append(story_dict)
            total_story_points += points
        feature_dict["stories"] = story_dicts
        feature_dict["estimated_story_points"] = total_story_points if total_story_points > 0 else None

    def _merge_owned_feature_field(
        self,
        owns: Sequence[str],
        pattern: str,
        feature: Any,
        feature_dict: dict[str, Any],
        field_name: str,
        *,
        value: Any | None = None,
        use_getattr: bool = False,
    ) -> None:
        from specfact_cli.utils.persona_ownership import match_section_pattern

        if not any(match_section_pattern(p, pattern) for p in owns):
            return
        if use_getattr:
            val = getattr(feature, field_name, None)
            if val:
                feature_dict[field_name] = val
            return
        if value:
            feature_dict[field_name] = value

    def _merge_feature_optional_sections(
        self, feature: Any, persona_mapping: PersonaMapping, feature_dict: dict[str, Any]
    ) -> None:
        owns = persona_mapping.owns
        self._merge_owned_feature_field(
            owns, "features.*.outcomes", feature, feature_dict, "outcomes", value=feature.outcomes
        )
        self._merge_owned_feature_field(
            owns, "features.*.constraints", feature, feature_dict, "constraints", value=feature.constraints
        )
        self._merge_owned_feature_field(
            owns, "features.*.acceptance", feature, feature_dict, "acceptance", value=feature.acceptance
        )
        self._merge_owned_feature_field(
            owns, "features.*.implementation", feature, feature_dict, "implementation", use_getattr=True
        )

    def _load_bundle_protocols(self, bundle_dir: Path) -> dict[str, Any]:
        """
        Load protocol YAML files from the bundle's protocols directory.

        Args:
            bundle_dir: Bundle directory path

        Returns:
            Mapping of protocol_name -> protocol data dict
        """
        from specfact_cli.utils.structured_io import load_structured_file

        protocols: dict[str, Any] = {}
        protocols_dir = bundle_dir / "protocols"
        if not protocols_dir.exists():
            return protocols
        for protocol_file in protocols_dir.glob("*.yaml"):
            try:
                protocol_data = load_structured_file(protocol_file)
                protocol_name = protocol_file.stem.replace(".protocol", "")
                protocols[protocol_name] = protocol_data
            except Exception:
                pass
        return protocols

    def _load_bundle_contracts(self, bundle_dir: Path) -> dict[str, Any]:
        """
        Load contract YAML files from the bundle's contracts directory.

        Args:
            bundle_dir: Bundle directory path

        Returns:
            Mapping of contract_name -> contract data dict
        """
        from specfact_cli.utils.structured_io import load_structured_file

        contracts: dict[str, Any] = {}
        contracts_dir = bundle_dir / "contracts"
        if not contracts_dir.exists():
            return contracts
        for contract_file in contracts_dir.glob("*.yaml"):
            try:
                contract_data = load_structured_file(contract_file)
                contract_name = contract_file.stem.replace(".openapi", "").replace(".asyncapi", "")
                contracts[contract_name] = contract_data
            except Exception:
                pass
        return contracts

    def _base_template_context(self, bundle: ProjectBundle, persona_name: str) -> dict[str, Any]:
        return {
            "bundle_name": bundle.bundle_name,
            "persona_name": persona_name,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "status": "active",
        }

    def _merge_owned_bundle_sections(self, context: dict[str, Any], bundle: ProjectBundle, owns: Sequence[str]) -> None:
        from specfact_cli.utils.persona_ownership import match_section_pattern

        if bundle.idea and any(match_section_pattern(p, "idea") for p in owns):
            context["idea"] = bundle.idea.model_dump()
        if bundle.business and any(match_section_pattern(p, "business") for p in owns):
            context["business"] = bundle.business.model_dump()
        if any(match_section_pattern(p, "product") for p in owns):
            context["product"] = bundle.product.model_dump() if bundle.product else None

    def _filtered_features_for_context(self, bundle: ProjectBundle, persona_mapping: PersonaMapping) -> dict[str, Any]:
        filtered: dict[str, Any] = {}
        for feature_key, feature in bundle.features.items():
            feature_dict = self._build_feature_dict(feature, persona_mapping)
            if feature_dict:
                filtered[feature_key] = feature_dict
        return filtered

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
        context = self._base_template_context(bundle, persona_name)
        owns = persona_mapping.owns
        self._merge_owned_bundle_sections(context, bundle, owns)
        filtered_features = self._filtered_features_for_context(bundle, persona_mapping)
        if filtered_features:
            context["features"] = filtered_features

        protocols, contracts = self._protocols_and_contracts_for_context(bundle, persona_mapping)
        context["protocols"] = protocols
        context["contracts"] = contracts
        context["locks"] = [lock.model_dump() for lock in bundle.manifest.locks]

        return context

    def _protocols_and_contracts_for_context(
        self, bundle: ProjectBundle, persona_mapping: PersonaMapping
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        from specfact_cli.utils.persona_ownership import match_section_pattern
        from specfact_cli.utils.structure import SpecFactStructure

        owns_protocols = any(match_section_pattern(p, "protocols") for p in persona_mapping.owns)
        owns_contracts = any(match_section_pattern(p, "contracts") for p in persona_mapping.owns)
        if not owns_protocols and not owns_contracts:
            return {}, {}
        bundle_dir = Path(".") / SpecFactStructure.PROJECTS / bundle.bundle_name
        if not bundle_dir.exists():
            return {}, {}
        protocols = self._load_bundle_protocols(bundle_dir) if owns_protocols else {}
        contracts = self._load_bundle_contracts(bundle_dir) if owns_contracts else {}
        return protocols, contracts

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
