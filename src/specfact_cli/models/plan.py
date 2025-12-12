"""
Plan bundle data models.

This module defines Pydantic models for development plans, features,
and stories following the CLI-First specification.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from specfact_cli.models.source_tracking import SourceTracking


class Story(BaseModel):
    """User story model following Scrum/Agile practices."""

    key: str = Field(..., description="Story key (e.g., STORY-001)")
    title: str = Field(..., description="Story title (user-facing value statement)")
    acceptance: list[str] = Field(default_factory=list, description="Acceptance criteria")
    tags: list[str] = Field(default_factory=list, description="Story tags")
    story_points: int | None = Field(None, ge=0, le=100, description="Story points (complexity: 1,2,3,5,8,13,21...)")
    value_points: int | None = Field(
        None, ge=0, le=100, description="Value points (business value: 1,2,3,5,8,13,21...)"
    )
    tasks: list[str] = Field(default_factory=list, description="Implementation tasks (methods, functions)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")
    draft: bool = Field(default=False, description="Whether this is a draft story")
    scenarios: dict[str, list[str]] | None = Field(
        None,
        description="Scenarios extracted from control flow: primary, alternate, exception, recovery (Given/When/Then format)",
    )
    contracts: dict[str, Any] | None = Field(
        None,
        description="API contracts extracted from function signatures: parameters, return_type, preconditions, postconditions, error_contracts",
    )
    source_functions: list[str] = Field(
        default_factory=list,
        description="Source function mappings (format: 'file.py::func')",
    )
    test_functions: list[str] = Field(
        default_factory=list,
        description="Test function mappings (format: 'test_file.py::test_func')",
    )
    # NEW: Prioritization & Planning (Agile/Scrum alignment)
    priority: str | None = Field(
        default=None,
        description="Priority level (P0=Critical, P1=High, P2=Medium, P3=Low) or MoSCoW (Must/Should/Could/Won't)",
    )
    rank: int | None = Field(default=None, description="Backlog rank (1 = highest priority, lower = lower priority)")
    due_date: str | None = Field(
        default=None, description="Target completion date (ISO 8601 format, e.g., '2025-01-15')"
    )
    target_sprint: str | None = Field(default=None, description="Target sprint identifier (e.g., 'Sprint 2025-01')")
    target_release: str | None = Field(default=None, description="Target release identifier (e.g., 'v2.1.0')")
    # NEW: Dependencies
    depends_on_stories: list[str] = Field(
        default_factory=list,
        description="Story keys this story depends on (e.g., ['STORY-001', 'STORY-002'])",
    )
    blocks_stories: list[str] = Field(
        default_factory=list,
        description="Story keys this story blocks (reverse of depends_on)",
    )
    # NEW: Business Value
    business_value_description: str | None = Field(
        default=None, description="Clear statement of business value and user impact"
    )
    business_metrics: list[str] = Field(
        default_factory=list,
        description="Measurable business outcomes (e.g., 'Increase conversion by 15%')",
    )
    # NEW: Definition of Ready
    definition_of_ready: dict[str, bool] = Field(
        default_factory=dict,
        description="DoR checklist status: {'story_points': True, 'value_points': True, 'priority': True, ...}",
    )


class Feature(BaseModel):
    """Feature model."""

    key: str = Field(..., description="Feature key (e.g., FEATURE-001)")
    title: str = Field(..., description="Feature title")
    outcomes: list[str] = Field(default_factory=list, description="Expected outcomes")
    acceptance: list[str] = Field(default_factory=list, description="Acceptance criteria")
    constraints: list[str] = Field(default_factory=list, description="Constraints")
    stories: list[Story] = Field(default_factory=list, description="User stories")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")
    draft: bool = Field(default=False, description="Whether this is a draft feature")
    source_tracking: SourceTracking | None = Field(
        default=None, description="Source tracking information linking specs to code/tests"
    )
    contract: str | None = Field(
        default=None, description="Path to OpenAPI contract (e.g., 'contracts/auth-api.openapi.yaml')"
    )
    protocol: str | None = Field(default=None, description="Path to FSM protocol (e.g., 'protocols/auth-fsm.yaml')")
    # NEW: Prioritization (Agile/Scrum alignment)
    priority: str | None = Field(
        default=None, description="Feature priority (P0-P3 or MoSCoW: Must/Should/Could/Won't)"
    )
    rank: int | None = Field(default=None, description="Feature rank in backlog (1 = highest priority)")
    business_value_score: int | None = Field(default=None, ge=0, le=100, description="Business value score (0-100)")
    # NEW: Dependencies
    depends_on_features: list[str] = Field(default_factory=list, description="Feature keys this feature depends on")
    blocks_features: list[str] = Field(default_factory=list, description="Feature keys this feature blocks")
    # NEW: Business Context
    business_value_description: str | None = Field(
        default=None, description="Clear business value proposition for this feature"
    )
    target_users: list[str] = Field(
        default_factory=list, description="Target user personas (e.g., ['end-user', 'admin'])"
    )
    success_metrics: list[str] = Field(
        default_factory=list, description="Success metrics (e.g., 'Reduce support tickets by 30%')"
    )
    # NEW: Planning
    target_release: str | None = Field(default=None, description="Target release identifier (e.g., 'v2.1.0')")
    estimated_story_points: int | None = Field(
        default=None, description="Total estimated story points (sum of all stories, computed automatically)"
    )


class Release(BaseModel):
    """Release model."""

    name: str = Field(..., description="Release name")
    objectives: list[str] = Field(default_factory=list, description="Release objectives")
    scope: list[str] = Field(default_factory=list, description="Features in scope")
    risks: list[str] = Field(default_factory=list, description="Release risks")


class Product(BaseModel):
    """Product definition model."""

    themes: list[str] = Field(default_factory=list, description="Product themes")
    releases: list[Release] = Field(default_factory=list, description="Product releases")


class Business(BaseModel):
    """Business context model."""

    segments: list[str] = Field(default_factory=list, description="Market segments")
    problems: list[str] = Field(default_factory=list, description="Problems being solved")
    solutions: list[str] = Field(default_factory=list, description="Proposed solutions")
    differentiation: list[str] = Field(default_factory=list, description="Differentiation points")
    risks: list[str] = Field(default_factory=list, description="Business risks")


class Idea(BaseModel):
    """Initial idea model."""

    title: str = Field(..., description="Idea title")
    narrative: str = Field(..., description="Idea narrative")
    target_users: list[str] = Field(default_factory=list, description="Target user personas")
    value_hypothesis: str = Field(default="", description="Value hypothesis")
    constraints: list[str] = Field(default_factory=list, description="Idea constraints")
    metrics: dict[str, Any] | None = Field(None, description="Success metrics")


class PlanSummary(BaseModel):
    """Summary metadata for fast plan bundle access without full parsing."""

    features_count: int = Field(default=0, description="Number of features in the plan")
    stories_count: int = Field(default=0, description="Total number of stories across all features")
    themes_count: int = Field(default=0, description="Number of product themes")
    releases_count: int = Field(default=0, description="Number of releases")
    content_hash: str | None = Field(None, description="SHA256 hash of plan content for integrity verification")
    computed_at: str | None = Field(None, description="ISO timestamp when summary was computed")


class Metadata(BaseModel):
    """Plan bundle metadata."""

    stage: str = Field(default="draft", description="Plan stage (draft, review, approved, released)")
    promoted_at: str | None = Field(None, description="ISO timestamp of last promotion")
    promoted_by: str | None = Field(None, description="User who performed last promotion")
    analysis_scope: str | None = Field(
        None, description="Analysis scope: 'full' for entire repository, 'partial' for subdirectory analysis"
    )
    entry_point: str | None = Field(None, description="Entry point path for partial analysis (relative to repo root)")
    external_dependencies: list[str] = Field(
        default_factory=list, description="List of external modules/packages imported from outside entry point"
    )
    summary: PlanSummary | None = Field(None, description="Summary metadata for fast access without full parsing")


class Clarification(BaseModel):
    """Single clarification Q&A."""

    id: str = Field(..., description="Unique question ID (e.g., Q001)")
    category: str = Field(..., description="Taxonomy category (Functional Scope, Data Model, etc.)")
    question: str = Field(..., description="Clarification question")
    answer: str = Field(..., description="User-provided answer")
    integrated_into: list[str] = Field(
        default_factory=list, description="Plan sections updated (e.g., 'features.FEATURE-001.acceptance')"
    )
    timestamp: str = Field(..., description="ISO timestamp of answer")


class ClarificationSession(BaseModel):
    """Session of clarifications."""

    date: str = Field(..., description="Session date (YYYY-MM-DD)")
    questions: list[Clarification] = Field(default_factory=list, description="Questions asked in this session")


class Clarifications(BaseModel):
    """Plan bundle clarifications."""

    sessions: list[ClarificationSession] = Field(default_factory=list, description="Clarification sessions")


class PlanBundle(BaseModel):
    """Complete plan bundle model."""

    version: str = Field(default="1.0", description="Plan bundle version")
    idea: Idea | None = Field(None, description="Initial idea")
    business: Business | None = Field(None, description="Business context")
    product: Product = Field(..., description="Product definition")
    features: list[Feature] = Field(default_factory=list, description="Product features")
    metadata: Metadata | None = Field(None, description="Plan bundle metadata")
    clarifications: Clarifications | None = Field(None, description="Plan clarifications (Q&A sessions)")

    def compute_summary(self, include_hash: bool = False) -> PlanSummary:
        """
        Compute summary metadata for fast access without full parsing.

        Args:
            include_hash: Whether to compute content hash (slower but enables integrity checks)

        Returns:
            PlanSummary with counts and optional hash
        """
        import hashlib
        import json
        from datetime import datetime

        features_count = len(self.features)
        stories_count = sum(len(f.stories) for f in self.features)
        themes_count = len(self.product.themes) if self.product.themes else 0
        releases_count = len(self.product.releases) if self.product.releases else 0

        content_hash = None
        if include_hash:
            # Compute hash of plan content (excluding summary itself to avoid circular dependency)
            # NOTE: Also exclude clarifications - they are review metadata, not plan content
            # This ensures hash stability across review sessions (clarifications change but plan doesn't)
            plan_dict = self.model_dump(exclude={"metadata": {"summary"}})
            # Remove clarifications from dict (they are review metadata, not plan content)
            if "clarifications" in plan_dict:
                del plan_dict["clarifications"]
            # IMPORTANT: Sort features by key to ensure deterministic hash regardless of list order
            # Features are stored as list, so we need to sort by feature.key
            if "features" in plan_dict and isinstance(plan_dict["features"], list):
                plan_dict["features"] = sorted(
                    plan_dict["features"],
                    key=lambda f: f.get("key", "") if isinstance(f, dict) else getattr(f, "key", ""),
                )
            plan_json = json.dumps(plan_dict, sort_keys=True, default=str)
            content_hash = hashlib.sha256(plan_json.encode("utf-8")).hexdigest()

        return PlanSummary(
            features_count=features_count,
            stories_count=stories_count,
            themes_count=themes_count,
            releases_count=releases_count,
            content_hash=content_hash,
            computed_at=datetime.now().isoformat(),
        )

    def update_summary(self, include_hash: bool = False) -> None:
        """
        Update the summary metadata in this plan bundle.

        Args:
            include_hash: Whether to compute content hash (slower but enables integrity checks)
        """
        if self.metadata is None:
            # Create Metadata with default values
            # All fields have defaults, but type checker needs explicit None for optional fields
            self.metadata = Metadata(
                stage="draft",
                promoted_at=None,
                promoted_by=None,
                analysis_scope=None,
                entry_point=None,
                external_dependencies=[],
                summary=None,
            )
        self.metadata.summary = self.compute_summary(include_hash=include_hash)
