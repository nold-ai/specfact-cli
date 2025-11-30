"""
Code quality tracking models.

This module defines models for tracking contract coverage and code quality
metrics (beartype, icontract, crosshair).
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class CodeQuality(BaseModel):
    """Code quality metrics for a file."""

    beartype: bool = Field(default=False, description="Has beartype type checking")
    icontract: bool = Field(default=False, description="Has icontract decorators")
    crosshair: bool = Field(default=False, description="Has CrossHair property tests")
    coverage: float = Field(default=0.0, ge=0.0, le=1.0, description="Test coverage (0.0-1.0)")
    last_checked: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO timestamp of last check",
    )


class QualityTracking(BaseModel):
    """Quality tracking for a project bundle."""

    code_quality: dict[str, CodeQuality] = Field(default_factory=dict, description="File path → CodeQuality mapping")
