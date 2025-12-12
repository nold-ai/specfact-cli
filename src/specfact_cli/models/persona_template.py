"""
Persona template models for structured Markdown export/import.

This module defines Pydantic models for persona template schemas that specify
required sections, optional sections, validation rules, and section ordering
for persona-specific Markdown artifacts.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, Field


class SectionType(str, Enum):
    """Section type classification."""

    REQUIRED = "required"  # Must be present in export/import
    OPTIONAL = "optional"  # May be present
    CONDITIONAL = "conditional"  # Required if certain conditions met


class SectionValidation(BaseModel):
    """Validation rules for a section."""

    min_items: int | None = Field(None, description="Minimum number of items (for lists)")
    max_items: int | None = Field(None, description="Maximum number of items (for lists)")
    pattern: str | None = Field(None, description="Regex pattern for content validation")
    required_fields: list[str] = Field(default_factory=list, description="Required sub-fields")
    format: str | None = Field(None, description="Content format (e.g., 'checklist', 'gwt', 'markdown')")


class TemplateSection(BaseModel):
    """Template section definition."""

    name: str = Field(..., description="Section name (e.g., 'idea', 'features')")
    heading: str = Field(..., description="Markdown heading (e.g., '## Idea & Business Context')")
    type: SectionType = Field(SectionType.REQUIRED, description="Section type")
    description: str = Field(..., description="Section description/guidance")
    order: int = Field(..., description="Display order (lower = earlier)")
    validation: SectionValidation | None = Field(None, description="Validation rules")
    placeholder: str | None = Field(None, description="Placeholder text for empty sections")
    condition: str | None = Field(None, description="Condition for conditional sections (e.g., 'if features exist')")


class PersonaTemplate(BaseModel):
    """Persona template schema definition."""

    persona_name: str = Field(..., description="Persona name (e.g., 'product-owner')")
    version: str = Field("1.0.0", description="Template version (SemVer)")
    description: str = Field(..., description="Template description")
    sections: list[TemplateSection] = Field(..., description="Template sections in order")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @beartype
    @require(lambda self: len(self.sections) > 0, "Template must have at least one section")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def get_required_sections(self) -> list[str]:
        """Get list of required section names."""
        return [s.name for s in self.sections if s.type == SectionType.REQUIRED]

    @beartype
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def get_section_order(self) -> list[str]:
        """Get section names in display order."""
        sorted_sections = sorted(self.sections, key=lambda s: s.order)
        return [s.name for s in sorted_sections]

    @beartype
    @require(lambda section_name: isinstance(section_name, str), "Section name must be str")
    @ensure(lambda result: result is None or isinstance(result, TemplateSection), "Must return TemplateSection or None")
    def get_section(self, section_name: str) -> TemplateSection | None:
        """Get section definition by name."""
        return next((s for s in self.sections if s.name == section_name), None)

    @beartype
    @require(lambda section_name: isinstance(section_name, str), "Section name must be str")
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def is_required(self, section_name: str) -> bool:
        """Check if section is required."""
        section = self.get_section(section_name)
        return section is not None and section.type == SectionType.REQUIRED
