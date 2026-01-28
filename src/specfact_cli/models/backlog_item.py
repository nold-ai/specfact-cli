"""
Backlog item domain model.

This module defines the unified BacklogItem model that represents backlog items
from any provider (GitHub, ADO, Jira, etc.) with lossless data preservation
and refinement state tracking.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, Field

from specfact_cli.models.source_tracking import SourceTracking


class BacklogItem(BaseModel):
    """
    Unified domain model for backlog items from any provider.

    This model provides:
    - Normalized fields (title, body_markdown, state) for cross-provider compatibility
    - Provider-specific data preservation via provider_fields
    - Refinement state tracking (template detection, AI refinement)
    - Lossless round-trip preservation
    """

    # Identity fields
    id: str = Field(..., description="Backlog item identifier (provider-specific)")
    provider: str = Field(..., description="Provider name (github, ado, jira, linear, etc.)")
    url: str = Field(..., description="Backlog item URL (API or provider URL)")
    canonical_url: str | None = Field(
        default=None,
        description="User-friendly URL for opening in browser (e.g. ADO: org/project-name/_workitems/edit/id)",
    )

    # Content fields
    title: str = Field(..., description="Backlog item title")
    body_markdown: str = Field(default="", description="Backlog item body in Markdown format")
    state: str = Field(..., description="Backlog item state (open, closed, etc.)")
    acceptance_criteria: str | None = Field(
        default=None, description="Acceptance criteria for the item (separate from body_markdown, all frameworks)"
    )

    # Metadata fields
    assignees: list[str] = Field(default_factory=list, description="List of assignee usernames")
    tags: list[str] = Field(default_factory=list, description="List of tags/labels")
    iteration: str | None = Field(default=None, description="Iteration/sprint identifier")
    sprint: str | None = Field(
        default=None, description="Sprint identifier (extracted from iteration path or milestone)"
    )
    release: str | None = Field(
        default=None, description="Release identifier (extracted from iteration path or milestone)"
    )
    area: str | None = Field(default=None, description="Area path/component")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Last update timestamp")

    # Agile framework fields (Kanban/Scrum/SAFe)
    story_points: int | None = Field(
        default=None,
        description="Story points estimate (0-100 range, Scrum/SAFe). Stories > 13 points may need splitting.",
    )
    business_value: int | None = Field(default=None, description="Business value estimate (0-100 range, Scrum/SAFe)")
    priority: int | None = Field(default=None, description="Priority level (1-4 range, 1=highest, all frameworks)")
    value_points: int | None = Field(
        default=None,
        description="Value points (SAFe-specific, calculated from business_value / story_points). Used for WSJF prioritization.",
    )
    work_item_type: str | None = Field(
        default=None,
        description="Work item type (Epic, Feature, User Story, Task, Bug, etc., framework-aware). Supports Kanban, Scrum, SAFe hierarchies.",
    )

    # Tracking fields
    source_tracking: SourceTracking | None = Field(default=None, description="Source tracking metadata")
    provider_fields: dict[str, Any] = Field(
        default_factory=dict, description="Provider-specific fields preserved for lossless round-trip"
    )

    # Refinement state fields
    detected_template: str | None = Field(default=None, description="Detected template ID")
    template_confidence: float | None = Field(default=None, description="Template detection confidence (0.0-1.0)")
    template_missing_fields: list[str] = Field(
        default_factory=list, description="List of missing required template fields"
    )
    refined_body: str | None = Field(default=None, description="AI-refined body content")
    refinement_applied: bool = Field(default=False, description="Whether refinement has been applied to remote")
    refinement_timestamp: datetime | None = Field(default=None, description="Timestamp when refinement was applied")

    @beartype
    @property
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def needs_refinement(self) -> bool:
        """
        Check if backlog item needs refinement.

        Returns:
            True if item needs refinement (low confidence or no template match), False otherwise
        """
        if self.detected_template is None:
            return True
        if self.template_confidence is None:
            return True
        return self.template_confidence < 0.6

    @beartype
    @require(
        lambda self: isinstance(self.refined_body, str) and len(self.refined_body) > 0, "Refined body must be non-empty"
    )
    @ensure(lambda result: result is None, "Must return None")
    def apply_refinement(self) -> None:
        """
        Apply refined body to the item and mark as applied.

        This updates body_markdown with refined_body and sets refinement_applied=True.
        """
        if self.refined_body:
            self.body_markdown = self.refined_body
            self.refinement_applied = True
            self.refinement_timestamp = datetime.now(UTC)
