"""
Deviation tracking models.

This module defines models for tracking deviations between plans,
protocols, and actual implementation following the CLI-First specification.
"""

from __future__ import annotations

from enum import Enum

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, Field


class DeviationSeverity(str, Enum):
    """Deviation severity level."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class DeviationType(str, Enum):
    """Type of deviation."""

    MISSING_FEATURE = "missing_feature"
    MISSING_STORY = "missing_story"
    MISSING_BUSINESS_CONTEXT = "missing_business_context"
    EXTRA_FEATURE = "extra_feature"
    EXTRA_STORY = "extra_story"
    EXTRA_IMPLEMENTATION = "extra_implementation"
    MISMATCH = "mismatch"
    ACCEPTANCE_DRIFT = "acceptance_drift"
    FSM_MISMATCH = "fsm_mismatch"
    RISK_OMISSION = "risk_omission"


class Deviation(BaseModel):
    """Deviation model."""

    type: DeviationType = Field(..., description="Deviation type")
    severity: DeviationSeverity = Field(..., description="Severity level")
    description: str = Field(..., description="Deviation description")
    location: str = Field(..., description="File/module location")
    fix_hint: str | None = Field(None, description="Fix suggestion")


class DeviationReport(BaseModel):
    """Deviation report model."""

    manual_plan: str = Field(..., description="Path to manual plan bundle")
    auto_plan: str = Field(..., description="Path to auto-generated plan bundle")
    deviations: list[Deviation] = Field(default_factory=list, description="All deviations")
    summary: dict[str, int] = Field(default_factory=dict, description="Deviation counts by type")

    @property
    def total_deviations(self) -> int:
        """Total number of deviations."""
        return len(self.deviations)

    @property
    def high_count(self) -> int:
        """Number of high severity deviations."""
        return sum(1 for d in self.deviations if d.severity == DeviationSeverity.HIGH)

    @property
    def medium_count(self) -> int:
        """Number of medium severity deviations."""
        return sum(1 for d in self.deviations if d.severity == DeviationSeverity.MEDIUM)

    @property
    def low_count(self) -> int:
        """Number of low severity deviations."""
        return sum(1 for d in self.deviations if d.severity == DeviationSeverity.LOW)


class ValidationReport(BaseModel):
    """Validation report model (for backward compatibility)."""

    deviations: list[Deviation] = Field(default_factory=list, description="All deviations")
    high_count: int = Field(default=0, description="Number of high severity deviations")
    medium_count: int = Field(default=0, description="Number of medium severity deviations")
    low_count: int = Field(default=0, description="Number of low severity deviations")
    passed: bool = Field(default=True, description="Whether validation passed")

    @beartype
    @require(lambda deviation: isinstance(deviation, Deviation), "Must be Deviation instance")
    @ensure(
        lambda self: self.high_count + self.medium_count + self.low_count == len(self.deviations),
        "Counts must match deviations",
    )
    @ensure(lambda self: self.passed == (self.high_count == 0), "Must fail if high severity deviations exist")
    def add_deviation(self, deviation: Deviation) -> None:
        """Add a deviation and update counts."""
        self.deviations.append(deviation)

        if deviation.severity == DeviationSeverity.HIGH:
            self.high_count += 1
            self.passed = False
        elif deviation.severity == DeviationSeverity.MEDIUM:
            self.medium_count += 1
        elif deviation.severity == DeviationSeverity.LOW:
            self.low_count += 1
