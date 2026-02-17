"""Result model for policy validation findings."""

from __future__ import annotations

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, Field


@beartype
class PolicyResult(BaseModel):
    """Single policy finding."""

    rule_id: str = Field(..., description="Stable policy rule identifier.")
    severity: str = Field(..., description="Finding severity (for example: error, warning).")
    evidence_pointer: str = Field(..., description="Pointer to the field/path that violated the rule.")
    recommended_action: str = Field(..., description="Suggested remediating action.")
    message: str = Field(..., description="Human-readable failure message.")


@beartype
@require(lambda finding: finding.rule_id.strip() != "", "rule_id must not be empty")
@require(lambda finding: finding.severity.strip() != "", "severity must not be empty")
@require(lambda finding: finding.evidence_pointer.strip() != "", "evidence_pointer must not be empty")
@require(lambda finding: finding.recommended_action.strip() != "", "recommended_action must not be empty")
@ensure(lambda result: isinstance(result, PolicyResult), "Must return PolicyResult")
def normalize_policy_result(finding: PolicyResult) -> PolicyResult:
    """Normalize fields used by JSON/Markdown rendering."""
    return PolicyResult(
        rule_id=finding.rule_id.strip(),
        severity=finding.severity.strip().lower(),
        evidence_pointer=finding.evidence_pointer.strip(),
        recommended_action=finding.recommended_action.strip(),
        message=finding.message.strip(),
    )
