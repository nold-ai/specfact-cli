"""Suggestion engine for policy findings."""

from __future__ import annotations

from beartype import beartype
from icontract import ensure

from ..models.policy_result import PolicyResult


@beartype
@ensure(lambda result: isinstance(result, list), "Suggestions must be returned as list")
def build_suggestions(findings: list[PolicyResult]) -> list[dict[str, object]]:
    """Create confidence-scored, patch-ready suggestions from policy failures."""
    suggestions: list[dict[str, object]] = []
    for finding in findings:
        suggestions.append(
            {
                "rule_id": finding.rule_id,
                "confidence": _score_confidence(finding),
                "reason": finding.message,
                "patch": {
                    "op": "add",
                    "path": finding.evidence_pointer,
                    "value": "TODO",
                },
            }
        )
    return suggestions


def _score_confidence(finding: PolicyResult) -> float:
    if finding.severity == "error":
        return 0.9
    return 0.75
