"""
SDD (Spec-Driven Development) manifest data models.

This module defines Pydantic models for SDD manifests that capture
WHY (intent, constraints), WHAT (capabilities, acceptance), and HOW
(high-level architecture, invariants, contracts) with coverage thresholds
and enforcement budgets.
"""

from __future__ import annotations

from datetime import UTC, datetime

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, Field


class SDDWhy(BaseModel):
    """WHY section: Intent and constraints."""

    intent: str = Field(..., description="Primary intent/goal")
    constraints: list[str] = Field(default_factory=list, description="Business/technical constraints")
    target_users: str | None = Field(None, description="Target user personas")
    value_hypothesis: str | None = Field(None, description="Value proposition")


class SDDWhat(BaseModel):
    """WHAT section: Capabilities and acceptance."""

    capabilities: list[str] = Field(..., description="Core capabilities")
    acceptance_criteria: list[str] = Field(default_factory=list, description="High-level acceptance criteria")
    out_of_scope: list[str] = Field(default_factory=list, description="Explicitly out of scope")


class OpenAPIContractReference(BaseModel):
    """OpenAPI contract reference in SDD manifest."""

    feature_key: str = Field(..., description="Feature key (e.g., FEATURE-001)")
    contract_file: str = Field(
        ..., description="Contract file path relative to bundle (e.g., contracts/FEATURE-001.openapi.yaml)"
    )
    endpoints_count: int = Field(0, description="Number of API endpoints in contract")
    status: str = Field("draft", description="Contract status (draft, validated, tested, deployed)")


class SDDHow(BaseModel):
    """HOW section: High-level architecture, invariants, contracts."""

    architecture: str | None = Field(None, description="High-level architecture description")
    invariants: list[str] = Field(default_factory=list, description="System invariants")
    contracts: list[str] = Field(default_factory=list, description="Contract requirements (legacy text descriptions)")
    openapi_contracts: list[OpenAPIContractReference] = Field(
        default_factory=list, description="OpenAPI contract references linked to features"
    )
    module_boundaries: list[str] = Field(default_factory=list, description="Module/component boundaries")


class SDDCoverageThresholds(BaseModel):
    """Coverage thresholds for SDD validation."""

    contracts_per_story: float = Field(default=1.0, ge=0.0, description="Minimum contracts per story")
    invariants_per_feature: float = Field(default=1.0, ge=0.0, description="Minimum invariants per feature")
    architecture_facets: int = Field(
        default=3, ge=0, description="Minimum architecture facets (modules, boundaries, etc.)"
    )
    openapi_coverage_percent: float = Field(
        default=80.0, ge=0.0, le=100.0, description="Minimum percentage of features with OpenAPI contracts (0-100)"
    )


class SDDEnforcementBudget(BaseModel):
    """Enforcement budget for SDD validation."""

    shadow_budget_seconds: int = Field(300, ge=0, description="Shadow mode budget (seconds)")
    warn_budget_seconds: int = Field(180, ge=0, description="Warn mode budget (seconds)")
    block_budget_seconds: int = Field(90, ge=0, description="Block mode budget (seconds)")


class SDDManifest(BaseModel):
    """SDD manifest with WHY/WHAT/HOW, hashes, and coverage thresholds."""

    version: str = Field("1.0.0", description="SDD manifest schema version")
    plan_bundle_id: str = Field(..., description="Linked plan bundle ID (content hash)")
    plan_bundle_hash: str = Field(..., description="Plan bundle content hash")
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat(), description="Creation timestamp")
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat(), description="Last update timestamp")

    why: SDDWhy = Field(..., description="WHY section: Intent and constraints")
    what: SDDWhat = Field(..., description="WHAT section: Capabilities and acceptance")
    how: SDDHow = Field(..., description="HOW section: Architecture, invariants, contracts")

    coverage_thresholds: SDDCoverageThresholds = Field(
        default_factory=lambda: SDDCoverageThresholds(
            contracts_per_story=1.0,
            invariants_per_feature=1.0,
            architecture_facets=3,
            openapi_coverage_percent=80.0,
        ),
        description="Coverage thresholds for validation",
    )
    enforcement_budget: SDDEnforcementBudget = Field(
        default_factory=lambda: SDDEnforcementBudget(
            shadow_budget_seconds=300,
            warn_budget_seconds=180,
            block_budget_seconds=90,
        ),
        description="Enforcement budget configuration",
    )

    frozen_sections: list[str] = Field(
        default_factory=list, description="Frozen section IDs (cannot be edited without hash bump)"
    )
    promotion_status: str = Field("draft", description="Promotion status (draft, review, approved, released)")

    provenance: dict[str, str] = Field(default_factory=dict, description="Provenance metadata (source, author, etc.)")

    @beartype
    @require(
        lambda self: self.promotion_status in ("draft", "review", "approved", "released"), "Invalid promotion status"
    )
    @ensure(lambda self: len(self.plan_bundle_hash) > 0, "Plan bundle hash must not be empty")
    @ensure(lambda self: len(self.plan_bundle_id) > 0, "Plan bundle ID must not be empty")
    def validate_structure(self) -> bool:
        """
        Validate SDD manifest structure (custom validation beyond Pydantic).

        Returns:
            True if valid, raises ValidationError otherwise
        """
        return True

    @beartype
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(UTC).isoformat()
