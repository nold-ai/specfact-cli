"""Provider-agnostic backlog dependency graph models."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ItemType(StrEnum):
    """Normalized backlog item types."""

    EPIC = "epic"
    FEATURE = "feature"
    STORY = "story"
    TASK = "task"
    BUG = "bug"
    SUB_TASK = "sub_task"
    CUSTOM = "custom"


class DependencyType(StrEnum):
    """Normalized dependency relationship types."""

    PARENT_CHILD = "parent_child"
    BLOCKS = "blocks"
    RELATES_TO = "relates_to"
    DUPLICATES = "duplicates"
    CLONED_FROM = "cloned_from"
    IMPLEMENTS = "implements"
    CUSTOM = "custom"


class BacklogItem(BaseModel):
    """Unified backlog item node for provider-agnostic graph analysis."""

    id: str = Field(..., description="Provider-specific unique item id")
    key: str | None = Field(default=None, description="Display key, e.g. ABC-123")
    title: str = Field(..., description="Backlog item title")
    type: ItemType = Field(..., description="Canonical normalized item type")
    status: str = Field(default="unknown", description="Provider status value")
    description: str | None = Field(default=None, description="Backlog item body/description")
    priority: str | None = Field(default=None, description="Provider priority value")
    parent_id: str | None = Field(default=None, description="Parent item id when provided")
    raw_data: dict[str, Any] = Field(default_factory=dict, description="Raw provider payload for lossless round-trip")
    inferred_type: ItemType | None = Field(default=None, description="Type inferred from template/rules")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Inference confidence score")

    def effective_type(self) -> ItemType:
        """Return inferred type only when confidence is high enough."""
        if self.inferred_type is not None and self.confidence >= 0.5:
            return self.inferred_type
        return self.type


class Dependency(BaseModel):
    """Directed edge between backlog items."""

    source_id: str = Field(..., description="Source item id")
    target_id: str = Field(..., description="Target item id")
    type: DependencyType = Field(..., description="Normalized dependency type")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional provider relationship fields")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Relationship confidence score")


class BacklogGraph(BaseModel):
    """Provider-agnostic dependency graph for backlog analytics."""

    items: dict[str, BacklogItem] = Field(default_factory=dict, description="Graph nodes keyed by item id")
    dependencies: list[Dependency] = Field(default_factory=list, description="Graph edges")
    provider: str = Field(..., description="Provider name")
    project_key: str = Field(..., description="Project/repo identifier")
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Graph fetch timestamp")
    transitive_closure: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Computed transitive dependencies by source id",
    )
    cycles_detected: list[list[str]] = Field(default_factory=list, description="Detected cycles")
    orphans: list[str] = Field(default_factory=list, description="Orphan item ids")

    def to_json(self) -> str:
        """Serialize graph to JSON."""
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, payload: str) -> BacklogGraph:
        """Deserialize graph from JSON payload."""
        return cls.model_validate_json(payload)
