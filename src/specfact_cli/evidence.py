"""Core machine-readable evidence envelope contracts."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Literal

from beartype import beartype
from icontract import ensure
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, computed_field, field_serializer, field_validator


@beartype
class EvidenceResultSummary(BaseModel):
    """Pass, failure, and advisory totals for one evidence category."""

    model_config = ConfigDict(frozen=True, populate_by_name=True, serialize_by_alias=True)

    pass_count: int = Field(
        default=0, ge=0, validation_alias=AliasChoices("pass", "pass_count"), serialization_alias="pass"
    )
    fail_count: int = Field(
        default=0, ge=0, validation_alias=AliasChoices("fail", "fail_count"), serialization_alias="fail"
    )
    advisory_count: int = Field(
        default=0,
        ge=0,
        validation_alias=AliasChoices("advisory", "advisory_count"),
        serialization_alias="advisory",
    )


@beartype
class EvidenceEnvelope(BaseModel):
    """Core-only envelope; runtime emitters belong to the modules repository."""

    model_config = ConfigDict(frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    profile: str = Field(..., min_length=1)
    validation_results: Mapping[str, EvidenceResultSummary] = Field(default_factory=dict)

    @field_validator("validation_results", mode="after")
    @classmethod
    def _freeze_validation_results(
        cls, results: Mapping[str, EvidenceResultSummary]
    ) -> Mapping[str, EvidenceResultSummary]:
        """Copy result summaries into a read-only mapping for stable verdicts."""
        return MappingProxyType({name: summary.model_copy(deep=True) for name, summary in results.items()})

    @field_serializer("validation_results")
    def _serialize_validation_results(self, results: Mapping[str, EvidenceResultSummary]) -> dict[str, dict[str, int]]:
        """Emit immutable results using the standardized JSON summary keys."""
        return {name: summary.model_dump(by_alias=True) for name, summary in results.items()}

    @computed_field
    @property
    @ensure(lambda result: result in {"PASS", "PASS_WITH_ADVISORY", "FAIL"})
    def overall_verdict(self) -> Literal["PASS", "PASS_WITH_ADVISORY", "FAIL"]:
        """Derive the immutable CI verdict from validation result summaries."""
        summaries = self.validation_results.values()
        if any(summary.fail_count for summary in summaries):
            return "FAIL"
        if any(summary.advisory_count for summary in summaries):
            return "PASS_WITH_ADVISORY"
        return "PASS"

    @computed_field
    @property
    @ensure(lambda result: result in {0, 1})
    def ci_exit_code(self) -> int:
        """Return the CI exit code derived from the immutable verdict."""
        return 1 if self.overall_verdict == "FAIL" else 0
