"""
Persona importer for parsing and validating Markdown artifacts.

This module provides functionality to import persona-edited Markdown files back
into project bundles with template-based validation and ownership checks.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.persona_template import PersonaTemplate
from specfact_cli.models.project import PersonaMapping, ProjectBundle
from specfact_cli.validators.agile_validation import AgileValidator


class PersonaImportError(Exception):
    """Error during persona import validation."""


class PersonaImporter:
    """
    Importer for persona-specific Markdown artifacts.

    Validates Markdown structure against template schema and transforms
    Markdown content back to YAML bundle format.
    """

    @beartype
    @require(lambda template: isinstance(template, PersonaTemplate), "Template must be PersonaTemplate")
    def __init__(self, template: PersonaTemplate, validate_agile: bool = True) -> None:
        """
        Initialize persona importer.

        Args:
            template: Persona template schema for validation
            validate_agile: Whether to validate agile/scrum requirements (DoR, dependencies, etc.)
        """
        self.template = template
        self.agile_validator = AgileValidator() if validate_agile else None

    @beartype
    @require(lambda markdown_content: isinstance(markdown_content, str), "Markdown content must be str")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def parse_markdown(self, markdown_content: str) -> dict[str, Any]:
        """
        Parse Markdown content into structured dictionary.

        Args:
            markdown_content: Markdown content to parse

        Returns:
            Parsed content dictionary keyed by section names
        """
        sections: dict[str, Any] = {}
        lines = markdown_content.split("\n")
        current_section: str | None = None
        current_content: list[str] = []

        for line in lines:
            # Check for section headings (## or ###)
            heading_match = re.match(r"^(#{2,3})\s+(.+)$", line.strip())
            if heading_match:
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()

                # Start new section
                heading_text = heading_match.group(2).strip()
                # Remove markers like "*(mandatory)*" or "(mandatory)" - handle both formats
                # First try to match the asterisk format: *(mandatory)*
                heading_text = re.sub(r"\s*\*\([^)]+\)\*\s*", " ", heading_text)
                # Then try regular format: (mandatory)
                heading_text = re.sub(r"\s*\([^)]+\)\s*", " ", heading_text)
                # Clean up any extra spaces
                heading_text = re.sub(r"\s+", " ", heading_text).strip()
                current_section = self._normalize_section_name(heading_text)
                current_content = []
            elif current_section:
                current_content.append(line)

        # Save last section
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    @beartype
    @require(lambda section_name: isinstance(section_name, str), "Section name must be str")
    @ensure(lambda result: isinstance(result, str), "Must return str")
    def _normalize_section_name(self, section_name: str) -> str:
        """
        Normalize section name to match template section names.

        Args:
            section_name: Raw section name from Markdown

        Returns:
            Normalized section name
        """
        # Convert to lowercase and replace spaces/special chars with underscores
        normalized = section_name.lower().replace(" ", "_").replace("&", "and")
        # Remove common prefixes/suffixes
        normalized = re.sub(r"^idea_?and_?business_context$", "idea_business_context", normalized)
        normalized = re.sub(r"^features_?and_?user_stories$", "features", normalized)
        normalized = re.sub(
            r"^acceptance_criteria_?and_?implementation_details$", "acceptance_implementation", normalized
        )
        return re.sub(r"^technical_constraints_?and_?requirements$", "constraints_requirements", normalized)

    @beartype
    @require(lambda sections: isinstance(sections, dict), "Sections must be dict")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def validate_structure(self, sections: dict[str, Any]) -> list[str]:
        """
        Validate Markdown structure against template schema.

        Args:
            sections: Parsed sections dictionary

        Returns:
            List of validation errors (empty if valid)
        """
        errors: list[str] = []

        # Check required sections
        required_sections = self.template.get_required_sections()
        for required_section in required_sections:
            template_section = self.template.get_section(required_section)
            if template_section:
                # Try to match section name (may have variations)
                found = False
                for section_name in sections:
                    if self._normalize_section_name(section_name) == required_section:
                        found = True
                        break
                    # Also check if section name contains required section keywords
                    if required_section.replace("_", " ") in section_name.lower():
                        found = True
                        break

                if not found:
                    errors.append(f"Missing required section: '{template_section.heading}'")

        return errors

    @beartype
    @require(lambda sections: isinstance(sections, dict), "Sections must be dict")
    @require(
        lambda persona_mapping: isinstance(persona_mapping, PersonaMapping), "Persona mapping must be PersonaMapping"
    )
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def extract_owned_sections(self, sections: dict[str, Any], persona_mapping: PersonaMapping) -> dict[str, Any]:
        """
        Extract persona-owned sections from parsed Markdown.

        Args:
            sections: Parsed sections dictionary
            persona_mapping: Persona mapping with owned sections

        Returns:
            Extracted sections dictionary for bundle update
        """
        from specfact_cli.commands.project_cmd import match_section_pattern

        extracted: dict[str, Any] = {}

        # Extract idea if persona owns it
        if any(match_section_pattern(p, "idea") for p in persona_mapping.owns):
            idea_section = sections.get("idea_business_context") or sections.get("idea")
            if idea_section:
                extracted["idea"] = self._parse_idea_section(idea_section)

        # Extract business if persona owns it
        if any(match_section_pattern(p, "business") for p in persona_mapping.owns):
            business_section = sections.get("idea_business_context") or sections.get("business")
            if business_section:
                extracted["business"] = self._parse_business_section(business_section)

        # Extract features if persona owns any feature sections
        features_section = sections.get("features") or sections.get("features_user_stories")
        if features_section:
            extracted["features"] = self._parse_features_section(features_section, persona_mapping)

        return extracted

    @beartype
    @require(lambda content: isinstance(content, str), "Content must be str")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def _parse_idea_section(self, content: str) -> dict[str, Any]:
        """Parse idea section content."""
        # Basic parsing - can be enhanced with more sophisticated extraction
        idea: dict[str, Any] = {}
        lines = content.split("\n")

        current_subsection: str | None = None
        for line in lines:
            if line.startswith("###"):
                current_subsection = line.replace("###", "").strip().lower().replace(" ", "_")
            elif current_subsection == "problem_statement" and not idea.get("problem_statement"):
                idea["problem_statement"] = line.strip()
            elif current_subsection == "solution_vision" and not idea.get("solution_vision"):
                idea["solution_vision"] = line.strip()

        return idea

    @beartype
    @require(lambda content: isinstance(content, str), "Content must be str")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def _parse_business_section(self, content: str) -> dict[str, Any]:
        """Parse business section content."""
        business: dict[str, Any] = {}
        # Basic parsing - can be enhanced
        return business

    @beartype
    @require(lambda content: isinstance(content, str), "Content must be str")
    @require(
        lambda persona_mapping: isinstance(persona_mapping, PersonaMapping), "Persona mapping must be PersonaMapping"
    )
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def _parse_features_section(self, content: str, persona_mapping: PersonaMapping) -> dict[str, Any]:
        """Parse features section content."""
        from specfact_cli.commands.project_cmd import match_section_pattern

        features: dict[str, Any] = {}
        # Basic parsing - extract feature keys and titles
        feature_pattern = re.compile(r"###\s+([A-Z]+-\d+):\s+(.+)")
        matches = feature_pattern.findall(content)

        for feature_key, feature_title in matches:
            feature: dict[str, Any] = {"key": feature_key, "title": feature_title}

            # Extract stories if persona owns stories
            if any(match_section_pattern(p, "features.*.stories") for p in persona_mapping.owns):
                stories = self._parse_stories(content, feature_key)
                if stories:
                    feature["stories"] = stories

            # Extract acceptance criteria if persona owns acceptance
            if any(match_section_pattern(p, "features.*.acceptance") for p in persona_mapping.owns):
                acceptance = self._parse_acceptance_criteria(content, feature_key)
                if acceptance:
                    feature["acceptance"] = acceptance

            features[feature_key] = feature

        return features

    @beartype
    @require(lambda content: isinstance(content, str), "Content must be str")
    @require(lambda feature_key: isinstance(feature_key, str), "Feature key must be str")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def _parse_stories(self, content: str, feature_key: str) -> list[dict[str, Any]]:
        """Parse user stories from content."""
        stories: list[dict[str, Any]] = []
        # Extract stories between feature header and next feature
        feature_section = re.search(rf"###\s+{re.escape(feature_key)}:.*?(?=###|\Z)", content, re.DOTALL)
        if feature_section:
            story_text = feature_section.group(0)
            # Extract story titles and acceptance criteria
            story_pattern = re.compile(r"\*\*Story\s+\d+:\*\*\s+(.+?)(?=\*\*Story|\*\*Acceptance|\Z)", re.DOTALL)
            for match in story_pattern.finditer(story_text):
                story_title = match.group(1).strip()
                stories.append({"title": story_title, "description": ""})
        return stories

    @beartype
    @require(lambda content: isinstance(content, str), "Content must be str")
    @require(lambda feature_key: isinstance(feature_key, str), "Feature key must be str")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def _parse_acceptance_criteria(self, content: str, feature_key: str) -> list[str]:
        """Parse acceptance criteria from content."""
        criteria: list[str] = []
        # Extract acceptance criteria checkboxes
        feature_section = re.search(rf"###\s+{re.escape(feature_key)}:.*?(?=###|\Z)", content, re.DOTALL)
        if feature_section:
            story_text = feature_section.group(0)
            # Extract checkbox items
            checkbox_pattern = re.compile(r"- \[[ x]\]\s+(.+)")
            for match in checkbox_pattern.finditer(story_text):
                criteria.append(match.group(1).strip())
        return criteria

    @beartype
    @require(lambda markdown_path: isinstance(markdown_path, Path), "Markdown path must be Path")
    @require(lambda bundle: isinstance(bundle, ProjectBundle), "Bundle must be ProjectBundle")
    @require(
        lambda persona_mapping: isinstance(persona_mapping, PersonaMapping), "Persona mapping must be PersonaMapping"
    )
    @require(lambda persona_name: isinstance(persona_name, str), "Persona name must be str")
    @ensure(lambda result: isinstance(result, ProjectBundle), "Must return ProjectBundle")
    def import_from_file(
        self, markdown_path: Path, bundle: ProjectBundle, persona_mapping: PersonaMapping, persona_name: str
    ) -> ProjectBundle:
        """
        Import persona-edited Markdown file back into bundle.

        Args:
            markdown_path: Path to Markdown file
            bundle: Existing project bundle to update
            persona_mapping: Persona mapping with owned sections
            persona_name: Persona name

        Returns:
            Updated project bundle

        Raises:
            PersonaImportError: If validation fails
        """
        if not markdown_path.exists():
            raise PersonaImportError(f"Markdown file not found: {markdown_path}")

        markdown_content = markdown_path.read_text(encoding="utf-8")
        sections = self.parse_markdown(markdown_content)

        # Validate structure
        validation_errors = self.validate_structure(sections)
        if validation_errors:
            raise PersonaImportError("Template validation failed:\n" + "\n".join(f"  - {e}" for e in validation_errors))

        # Extract owned sections
        extracted = self.extract_owned_sections(sections, persona_mapping)

        # Validate agile/scrum requirements if enabled
        if self.agile_validator:
            agile_errors = self._validate_agile_requirements(extracted, bundle)
            if agile_errors:
                raise PersonaImportError(
                    "Agile/Scrum validation failed:\n" + "\n".join(f"  - {e}" for e in agile_errors)
                )

        # Update bundle (basic implementation - can be enhanced)
        # This is a simplified update - in production, would need more sophisticated merging
        updated_bundle = bundle.model_copy(deep=True)

        if "idea" in extracted and updated_bundle.idea:
            # Update idea fields
            for key, value in extracted["idea"].items():
                if hasattr(updated_bundle.idea, key):
                    setattr(updated_bundle.idea, key, value)

        if "business" in extracted and updated_bundle.business:
            # Update business fields
            for key, value in extracted["business"].items():
                if hasattr(updated_bundle.business, key):
                    setattr(updated_bundle.business, key, value)

        if "features" in extracted:
            # Update features
            for feature_key, feature_data in extracted["features"].items():
                if feature_key in updated_bundle.features:
                    feature = updated_bundle.features[feature_key]
                    # Update feature fields
                    for key, value in feature_data.items():
                        if key == "stories" and hasattr(feature, "stories"):
                            # Update stories
                            pass  # Would need proper story model updates
                        elif key == "acceptance" and hasattr(feature, "acceptance"):
                            feature.acceptance = value
                        elif hasattr(feature, key):
                            setattr(feature, key, value)

        return updated_bundle

    @beartype
    @require(lambda extracted: isinstance(extracted, dict), "Extracted must be dict")
    @require(lambda bundle: isinstance(bundle, ProjectBundle), "Bundle must be ProjectBundle")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def _validate_agile_requirements(self, extracted: dict[str, Any], bundle: ProjectBundle) -> list[str]:
        """
        Validate agile/scrum requirements for extracted data.

        Args:
            extracted: Extracted sections dictionary
            bundle: Existing bundle for reference validation

        Returns:
            List of validation errors (empty if valid)
        """
        if not self.agile_validator:
            return []

        errors: list[str] = []

        # Build bundle data structure for validation
        bundle_data: dict[str, Any] = {"features": {}}

        # Collect features and stories from extracted data
        if "features" in extracted:
            for feature_key, feature_data in extracted["features"].items():
                feature_dict: dict[str, Any] = {
                    "key": feature_key,
                    "priority": feature_data.get("priority"),
                    "rank": feature_data.get("rank"),
                    "business_value_score": feature_data.get("business_value_score"),
                    "business_value_description": feature_data.get("business_value_description"),
                    "depends_on_features": feature_data.get("depends_on_features", []),
                    "blocks_features": feature_data.get("blocks_features", []),
                    "stories": [],
                }

                # Collect stories from feature
                stories = feature_data.get("stories", [])
                for story in stories:
                    story_dict: dict[str, Any] = {
                        "key": story.get("key"),
                        "title": story.get("title"),
                        "story_points": story.get("story_points"),
                        "value_points": story.get("value_points"),
                        "priority": story.get("priority"),
                        "rank": story.get("rank"),
                        "due_date": story.get("due_date"),
                        "target_sprint": story.get("target_sprint"),
                        "target_release": story.get("target_release"),
                        "depends_on_stories": story.get("depends_on_stories", []),
                        "blocks_stories": story.get("blocks_stories", []),
                        "business_value_description": story.get("business_value_description"),
                        "business_metrics": story.get("business_metrics", []),
                    }
                    feature_dict["stories"].append(story_dict)

                bundle_data["features"][feature_key] = feature_dict

        # Also include existing bundle features for dependency validation
        for feature_key, feature in bundle.features.items():
            if feature_key not in bundle_data["features"]:
                # Convert existing feature to dict format
                existing_feature_dict: dict[str, Any] = {
                    "key": feature_key,
                    "priority": getattr(feature, "priority", None),
                    "rank": getattr(feature, "rank", None),
                    "business_value_score": getattr(feature, "business_value_score", None),
                    "business_value_description": getattr(feature, "business_value_description", None),
                    "depends_on_features": getattr(feature, "depends_on_features", []),
                    "blocks_features": getattr(feature, "blocks_features", []),
                    "stories": [],
                }

                # Convert existing stories
                for story in feature.stories:
                    existing_story_dict: dict[str, Any] = {
                        "key": story.key,
                        "title": story.title,
                        "story_points": story.story_points,
                        "value_points": story.value_points,
                        "priority": getattr(story, "priority", None),
                        "rank": getattr(story, "rank", None),
                        "due_date": getattr(story, "due_date", None),
                        "target_sprint": getattr(story, "target_sprint", None),
                        "target_release": getattr(story, "target_release", None),
                        "depends_on_stories": getattr(story, "depends_on_stories", []),
                        "blocks_stories": getattr(story, "blocks_stories", []),
                        "business_value_description": getattr(story, "business_value_description", None),
                        "business_metrics": getattr(story, "business_metrics", []),
                    }
                    existing_feature_dict["stories"].append(existing_story_dict)

                bundle_data["features"][feature_key] = existing_feature_dict

        # Run agile validation
        agile_errors = self.agile_validator.validate_bundle_agile_requirements(bundle_data)
        errors.extend(agile_errors)

        return errors
