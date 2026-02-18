"""
BundleMapping result model for spec-to-bundle assignment with confidence and explanation.
"""

from __future__ import annotations

from beartype import beartype
from icontract import ensure
from pydantic import BaseModel, Field


class BundleMapping(BaseModel):
    """
    Result of mapping a backlog item to an OpenSpec bundle.

    Attributes:
        primary_bundle_id: Best-match bundle id, or None if no mapping.
        confidence: Score in [0.0, 1.0].
        candidates: Alternative (bundle_id, score) pairs.
        explained_reasoning: Human-readable rationale.
    """

    primary_bundle_id: str | None = Field(
        default=None,
        description="Assigned bundle id, or None if no mapping",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score in [0.0, 1.0]",
    )
    candidates: list[tuple[str, float]] = Field(
        default_factory=list,
        description="Alternative (bundle_id, score) pairs",
    )
    explained_reasoning: str = Field(
        default="",
        description="Human-readable mapping rationale",
    )

    @beartype
    @ensure(
        lambda result: result is None or (isinstance(result, str) and len(result) >= 0),
        "Return type is None or non-negative length str",
    )
    def get_primary_or_none(self) -> str | None:
        """Return primary_bundle_id (for compatibility with callers expecting str | None)."""
        return self.primary_bundle_id
