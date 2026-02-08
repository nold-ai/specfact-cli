"""Validation models used by module IO contracts."""

from __future__ import annotations

from typing import Literal

from beartype import beartype
from pydantic import BaseModel, Field


@beartype
class ValidationReport(BaseModel):
    """Structured validation report for module-level bundle validation."""

    status: Literal["passed", "failed", "warnings"] = Field(
        default="passed",
        description="Validation result status.",
    )
    violations: list[dict[str, str]] = Field(
        default_factory=list,
        description="Validation violations with severity/message/location keys.",
    )
    summary: dict[str, int] = Field(
        default_factory=lambda: {
            "total_checks": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
        },
        description="Validation summary counters.",
    )
