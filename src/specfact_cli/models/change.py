"""
Change tracking data models.

This module defines tool-agnostic change tracking models to support delta spec
tracking (ADDED/MODIFIED/REMOVED) and change proposals. These models are used
by OpenSpec and potentially other tools (Linear, Jira, etc.) that support
similar change tracking capabilities.

All tool-specific metadata is stored in source_tracking, not in these models,
ensuring they remain adapter-agnostic.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from icontract import ensure, require
from pydantic import BaseModel, Field, model_validator

from specfact_cli.models.plan import Feature
from specfact_cli.models.source_tracking import SourceTracking


class ChangeType(str, Enum):
    """Change type for delta specs (tool-agnostic)."""

    ADDED = "added"
    MODIFIED = "modified"
    REMOVED = "removed"


class FeatureDelta(BaseModel):
    """Delta tracking for a feature change (tool-agnostic)."""

    feature_key: str = Field(..., description="Feature key (e.g., FEATURE-001)")
    change_type: ChangeType = Field(..., description="Type of change")
    original_feature: Feature | None = Field(None, description="Original feature (for MODIFIED/REMOVED)")
    proposed_feature: Feature | None = Field(None, description="Proposed feature (for ADDED/MODIFIED)")
    change_rationale: str | None = Field(None, description="Why this change is needed")
    change_date: str | None = Field(None, description="ISO timestamp of change proposal")
    validation_status: str | None = Field(None, description="Validation status: pending, passed, failed")
    validation_results: dict[str, Any] | None = Field(None, description="SpecFact validation results")
    source_tracking: SourceTracking | None = Field(
        None,
        description="Tool-specific metadata (e.g., OpenSpec delta path, Linear issue ID)",
    )

    @model_validator(mode="after")
    @require(
        lambda self: self.change_type == ChangeType.ADDED
        or (self.change_type in (ChangeType.MODIFIED, ChangeType.REMOVED) and self.original_feature is not None),
        "MODIFIED/REMOVED changes must have original_feature",
    )
    @require(
        lambda self: self.change_type == ChangeType.REMOVED
        or (self.change_type in (ChangeType.ADDED, ChangeType.MODIFIED) and self.proposed_feature is not None),
        "ADDED/MODIFIED changes must have proposed_feature",
    )
    @ensure(lambda result: isinstance(result, FeatureDelta), "Must return FeatureDelta")
    def validate_feature_delta(self) -> FeatureDelta:
        """
        Validate feature delta constraints after model initialization.

        Returns:
            Self (for Pydantic v2 model_validator)
        """
        return self


class ChangeProposal(BaseModel):
    """Change proposal (tool-agnostic, used by OpenSpec and potentially other tools)."""

    name: str = Field(..., description="Change identifier (e.g., 'add-user-feedback')")
    title: str = Field(..., description="Change title")
    description: str = Field(..., description="What: Description of the change")
    rationale: str = Field(..., description="Why: Rationale and business value")
    timeline: str | None = Field(None, description="When: Timeline and dependencies")
    owner: str | None = Field(None, description="Who: Owner and stakeholders")
    stakeholders: list[str] = Field(default_factory=list, description="List of stakeholders")
    dependencies: list[str] = Field(default_factory=list, description="Dependencies (other changes, features)")
    status: str = Field(default="proposed", description="Status: proposed, in-progress, applied, archived")
    created_at: str = Field(..., description="ISO timestamp of creation")
    applied_at: str | None = Field(None, description="ISO timestamp when applied")
    archived_at: str | None = Field(None, description="ISO timestamp when archived")
    source_tracking: SourceTracking | None = Field(
        None,
        description="Tool-specific metadata (e.g., OpenSpec change directory path, Linear issue ID)",
    )


class ChangeTracking(BaseModel):
    """Change tracking for a bundle (tool-agnostic capability)."""

    proposals: dict[str, ChangeProposal] = Field(
        default_factory=dict,
        description="Change proposals (name -> ChangeProposal)",
    )
    feature_deltas: dict[str, list[FeatureDelta]] = Field(
        default_factory=dict,
        description="Feature deltas per change (change_name -> [FeatureDelta])",
    )


class ChangeArchive(BaseModel):
    """Archive entry for completed changes (tool-agnostic)."""

    change_name: str = Field(..., description="Change identifier")
    applied_at: str = Field(..., description="ISO timestamp when applied")
    applied_by: str | None = Field(None, description="User who applied the change")
    pr_number: str | None = Field(None, description="PR number (if applicable)")
    commit_hash: str | None = Field(None, description="Git commit hash")
    feature_deltas: list[FeatureDelta] = Field(default_factory=list, description="Feature deltas that were applied")
    validation_results: dict[str, Any] | None = Field(None, description="SpecFact validation results")
    source_tracking: SourceTracking | None = Field(
        None,
        description="Tool-specific metadata (e.g., OpenSpec archive path, Linear issue URL)",
    )
