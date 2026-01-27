"""
ADO field mapper for extracting fields from Azure DevOps work items.

This mapper extracts fields from ADO work items which use separate fields
(e.g., System.Description, System.AcceptanceCriteria, Microsoft.VSTS.Common.StoryPoints)
with support for custom template field mappings.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.backlog.mappers.base import FieldMapper
from specfact_cli.backlog.mappers.template_config import FieldMappingConfig


class AdoFieldMapper(FieldMapper):
    """
    Field mapper for Azure DevOps work items.

    Extracts fields from separate ADO fields with support for:
    - Default mappings (Scrum, Agile, SAFe, Kanban)
    - Custom template mappings via YAML configuration
    - Framework-aware field extraction (work item types, value points, etc.)
    """

    # Default ADO field mappings (Scrum/Agile/SAFe)
    DEFAULT_FIELD_MAPPINGS = {
        "System.Description": "description",
        "System.AcceptanceCriteria": "acceptance_criteria",
        "Microsoft.VSTS.Common.AcceptanceCriteria": "acceptance_criteria",  # Alternative field name
        "Microsoft.VSTS.Common.StoryPoints": "story_points",
        "Microsoft.VSTS.Scheduling.StoryPoints": "story_points",  # Alternative field name
        "Microsoft.VSTS.Common.BusinessValue": "business_value",
        "Microsoft.VSTS.Common.Priority": "priority",
        "System.WorkItemType": "work_item_type",
    }

    def __init__(self, custom_mapping_file: str | Path | None = None) -> None:
        """
        Initialize ADO field mapper.

        Args:
            custom_mapping_file: Path to custom field mapping YAML file (optional).
                If None, checks for `.specfact/templates/backlog/field_mappings/ado_custom.yaml` in current directory.
        """
        self.custom_mapping: FieldMappingConfig | None = None

        # If custom_mapping_file not provided, check standard location
        if custom_mapping_file is None:
            current_dir = Path.cwd()
            standard_location = (
                current_dir / ".specfact" / "templates" / "backlog" / "field_mappings" / "ado_custom.yaml"
            )
            if standard_location.exists():
                custom_mapping_file = standard_location

        if custom_mapping_file:
            try:
                self.custom_mapping = FieldMappingConfig.from_file(custom_mapping_file)
            except (FileNotFoundError, ValueError) as e:
                # Log warning but continue with defaults
                import warnings

                warnings.warn(f"Failed to load custom field mapping: {e}. Using defaults.", UserWarning, stacklevel=2)

    @beartype
    @require(lambda self, item_data: isinstance(item_data, dict), "Item data must be dict")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def extract_fields(self, item_data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract fields from ADO work item data.

        Args:
            item_data: ADO work item data from API

        Returns:
            Dict mapping canonical field names to extracted values
        """
        fields_dict = item_data.get("fields", {})
        if not isinstance(fields_dict, dict):
            return {}

        # Use custom mapping if available, otherwise use defaults
        field_mappings = self._get_field_mappings()

        extracted_fields: dict[str, Any] = {}

        # Extract description
        description = self._extract_field(fields_dict, field_mappings, "description")
        extracted_fields["description"] = description if description else ""

        # Extract acceptance criteria
        acceptance_criteria = self._extract_field(fields_dict, field_mappings, "acceptance_criteria")
        extracted_fields["acceptance_criteria"] = acceptance_criteria if acceptance_criteria else None

        # Extract story points (validate range 0-100)
        story_points = self._extract_numeric_field(fields_dict, field_mappings, "story_points")
        if story_points is not None:
            story_points = max(0, min(100, story_points))  # Clamp to 0-100 range
        extracted_fields["story_points"] = story_points

        # Extract business value (validate range 0-100)
        business_value = self._extract_numeric_field(fields_dict, field_mappings, "business_value")
        if business_value is not None:
            business_value = max(0, min(100, business_value))  # Clamp to 0-100 range
        extracted_fields["business_value"] = business_value

        # Extract priority (validate range 1-4, 1=highest)
        priority = self._extract_numeric_field(fields_dict, field_mappings, "priority")
        if priority is not None:
            priority = max(1, min(4, priority))  # Clamp to 1-4 range
        extracted_fields["priority"] = priority

        # Calculate value points (SAFe-specific: business_value / story_points)
        business_value_val: int | None = extracted_fields.get("business_value")
        story_points_val: int | None = extracted_fields.get("story_points")
        if (
            business_value_val is not None
            and story_points_val is not None
            and story_points_val != 0
            and isinstance(business_value_val, int)
            and isinstance(story_points_val, int)
        ):
            try:
                value_points = int(business_value_val / story_points_val)
                extracted_fields["value_points"] = value_points
            except (ZeroDivisionError, TypeError):
                extracted_fields["value_points"] = None
        else:
            extracted_fields["value_points"] = None

        # Extract work item type
        work_item_type = self._extract_work_item_type(fields_dict, field_mappings)
        extracted_fields["work_item_type"] = work_item_type

        return extracted_fields

    @beartype
    @require(lambda self, canonical_fields: isinstance(canonical_fields, dict), "Canonical fields must be dict")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def map_from_canonical(self, canonical_fields: dict[str, Any]) -> dict[str, Any]:
        """
        Map canonical fields back to ADO field format.

        When multiple ADO fields map to the same canonical field, prefers System.* fields
        over Microsoft.VSTS.Common.* fields for better compatibility with Scrum templates.

        Args:
            canonical_fields: Dict of canonical field names to values

        Returns:
            Dict mapping ADO field names to values
        """
        # Use custom mapping if available, otherwise use defaults
        field_mappings = self._get_field_mappings()

        # Build reverse mapping with preference for System.* fields over Microsoft.VSTS.Common.*
        # This ensures write operations use the more common System.* fields (better Scrum compatibility)
        reverse_mappings: dict[str, str] = {}
        for ado_field, canonical in field_mappings.items():
            if canonical not in reverse_mappings:
                # First mapping for this canonical field - use it
                reverse_mappings[canonical] = ado_field
            else:
                # Multiple mappings exist - prefer System.* over Microsoft.VSTS.Common.*
                current_ado_field = reverse_mappings[canonical]
                # Prefer System.* fields for write operations (more common in Scrum)
                if ado_field.startswith("System.") and not current_ado_field.startswith("System."):
                    reverse_mappings[canonical] = ado_field

        ado_fields: dict[str, Any] = {}

        # Map each canonical field to ADO field
        for canonical_field, value in canonical_fields.items():
            if canonical_field in reverse_mappings:
                ado_field_name = reverse_mappings[canonical_field]
                ado_fields[ado_field_name] = value

        return ado_fields

    @beartype
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def _get_field_mappings(self) -> dict[str, str]:
        """
        Get field mappings (custom or default).

        Returns:
            Dict mapping ADO field names to canonical field names
        """
        if self.custom_mapping and self.custom_mapping.field_mappings:
            # Merge custom mappings with defaults (custom overrides defaults)
            mappings = self.DEFAULT_FIELD_MAPPINGS.copy()
            mappings.update(self.custom_mapping.field_mappings)
            return mappings
        return self.DEFAULT_FIELD_MAPPINGS.copy()

    @beartype
    @require(lambda self, fields_dict: isinstance(fields_dict, dict), "Fields dict must be dict")
    @require(lambda self, field_mappings: isinstance(field_mappings, dict), "Field mappings must be dict")
    @require(lambda self, canonical_field: isinstance(canonical_field, str), "Canonical field must be str")
    @ensure(lambda result: result is None or isinstance(result, str), "Must return str or None")
    def _extract_field(
        self, fields_dict: dict[str, Any], field_mappings: dict[str, str], canonical_field: str
    ) -> str | None:
        """
        Extract field value from ADO fields dict using mapping.

        Supports multiple field name alternatives for the same canonical field.
        Checks all ADO fields that map to the canonical field and returns the first found value.
        Priority: custom mapping > default mapping (handled by _get_field_mappings merge order).

        Args:
            fields_dict: ADO fields dict
            field_mappings: Field mappings (ADO field name -> canonical field name)
            canonical_field: Canonical field name to extract

        Returns:
            Field value or None if not found
        """
        # Find all ADO field names that map to this canonical field
        # Check all alternatives and return the first found value
        for ado_field, canonical in field_mappings.items():
            if canonical == canonical_field:
                value = fields_dict.get(ado_field)
                if value is not None:
                    return str(value).strip() if isinstance(value, str) else str(value)
        return None

    @beartype
    @require(lambda self, fields_dict: isinstance(fields_dict, dict), "Fields dict must be dict")
    @require(lambda self, field_mappings: isinstance(field_mappings, dict), "Field mappings must be dict")
    @require(lambda self, canonical_field: isinstance(canonical_field, str), "Canonical field must be str")
    @ensure(lambda result: result is None or isinstance(result, int), "Must return int or None")
    def _extract_numeric_field(
        self, fields_dict: dict[str, Any], field_mappings: dict[str, str], canonical_field: str
    ) -> int | None:
        """
        Extract numeric field value from ADO fields dict using mapping.

        Args:
            fields_dict: ADO fields dict
            field_mappings: Field mappings (ADO field name -> canonical field name)
            canonical_field: Canonical field name to extract

        Returns:
            Numeric value or None if not found
        """
        # Find ADO field name for this canonical field
        for ado_field, canonical in field_mappings.items():
            if canonical == canonical_field:
                value = fields_dict.get(ado_field)
                if value is not None:
                    try:
                        # Handle both int and float (ADO may return float for story points)
                        return int(float(value))
                    except (ValueError, TypeError):
                        return None
        return None

    @beartype
    @require(lambda self, fields_dict: isinstance(fields_dict, dict), "Fields dict must be dict")
    @require(lambda self, field_mappings: isinstance(field_mappings, dict), "Field mappings must be dict")
    @ensure(lambda result: result is None or isinstance(result, str), "Must return str or None")
    def _extract_work_item_type(self, fields_dict: dict[str, Any], field_mappings: dict[str, str]) -> str | None:
        """
        Extract work item type from ADO fields dict.

        Args:
            fields_dict: ADO fields dict
            field_mappings: Field mappings (ADO field name -> canonical field name)

        Returns:
            Work item type or None if not found
        """
        # Find ADO field name for work_item_type
        for ado_field, canonical in field_mappings.items():
            if canonical == "work_item_type":
                work_item_type = fields_dict.get(ado_field)
                if work_item_type:
                    # Apply work item type mapping if custom mapping is available
                    if self.custom_mapping:
                        return self.custom_mapping.map_work_item_type(str(work_item_type))
                    return str(work_item_type)
        return None
