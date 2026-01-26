"""
Abstract field mapper base class.

This module defines the abstract FieldMapper interface that all provider-specific
field mappers must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from beartype import beartype
from icontract import ensure, require


class FieldMapper(ABC):
    """
    Abstract base class for provider-specific field mappers.

    Field mappers normalize provider-specific field structures to canonical field names,
    enabling provider-agnostic backlog item handling while preserving provider-specific
    structures for round-trip sync.

    Canonical field names:
    - description: Main description/content of the backlog item
    - acceptance_criteria: Acceptance criteria for the item
    - story_points: Story points estimate (0-100, Scrum/SAFe)
    - business_value: Business value estimate (0-100, Scrum/SAFe)
    - priority: Priority level (1-4, 1=highest, all frameworks)
    - value_points: Value points (SAFe-specific, calculated from business_value / story_points)
    - work_item_type: Work item type (Epic, Feature, User Story, Task, Bug, etc., framework-aware)
    """

    # Canonical field names for Kanban/Scrum/SAFe alignment
    CANONICAL_FIELDS = {
        "description",
        "acceptance_criteria",
        "story_points",
        "business_value",
        "priority",
        "value_points",
        "work_item_type",
    }

    @beartype
    @abstractmethod
    @require(lambda self, item_data: isinstance(item_data, dict), "Item data must be dict")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def extract_fields(self, item_data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract fields from provider-specific item data.

        Args:
            item_data: Provider-specific item data (GitHub issue, ADO work item, etc.)

        Returns:
            Dict mapping canonical field names to extracted values
        """

    @beartype
    @abstractmethod
    @require(lambda self, canonical_fields: isinstance(canonical_fields, dict), "Canonical fields must be dict")
    @require(
        lambda self, canonical_fields: all(field in self.CANONICAL_FIELDS for field in canonical_fields),
        "All field names must be canonical",
    )
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def map_from_canonical(self, canonical_fields: dict[str, Any]) -> dict[str, Any]:
        """
        Map canonical fields back to provider-specific format.

        Used for writeback/round-trip sync to preserve provider-specific structure.

        Args:
            canonical_fields: Dict of canonical field names to values

        Returns:
            Dict mapping provider-specific field names to values
        """

    @beartype
    @require(lambda self, field_name: isinstance(field_name, str), "Field name must be str")
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def is_canonical_field(self, field_name: str) -> bool:
        """
        Check if a field name is a canonical field.

        Args:
            field_name: Field name to check

        Returns:
            True if field is canonical, False otherwise
        """
        return field_name in self.CANONICAL_FIELDS
