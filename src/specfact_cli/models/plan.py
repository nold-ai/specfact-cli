"""
Plan bundle data models.

This module defines Pydantic models for development plans, features,
and stories following the CLI-First specification.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


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


class Metadata(BaseModel):
    """Plan bundle metadata."""

    stage: str = Field(default="draft", description="Plan stage (draft, review, approved, released)")
    promoted_at: str | None = Field(None, description="ISO timestamp of last promotion")
    promoted_by: str | None = Field(None, description="User who performed last promotion")


class PlanBundle(BaseModel):
    """Complete plan bundle model."""

    version: str = Field(default="1.0", description="Plan bundle version")
    idea: Idea | None = Field(None, description="Initial idea")
    business: Business | None = Field(None, description="Business context")
    product: Product = Field(..., description="Product definition")
    features: list[Feature] = Field(default_factory=list, description="Product features")
    metadata: Metadata | None = Field(None, description="Plan bundle metadata")
