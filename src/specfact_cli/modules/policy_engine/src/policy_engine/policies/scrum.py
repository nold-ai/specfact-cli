"""Scrum policy family (DoR/DoD)."""

from __future__ import annotations

from typing import Any

from beartype import beartype
from icontract import ensure

from ..config.policy_config import PolicyConfig
from ..models.policy_result import PolicyResult, normalize_policy_result


@beartype
@ensure(lambda result: isinstance(result, list), "Must return a list of policy findings")
def build_scrum_failures(config: PolicyConfig, items: list[dict[str, Any]]) -> list[PolicyResult]:
    """Evaluate Scrum DoR/DoD requirements against each backlog item."""
    findings: list[PolicyResult] = []

    for idx, item in enumerate(items):
        for field in config.scrum.dor_required_fields:
            if _is_missing(item, field):
                findings.append(
                    normalize_policy_result(
                        PolicyResult(
                            rule_id=f"scrum.dor.{field}",
                            severity="error",
                            evidence_pointer=f"items[{idx}].{field}",
                            recommended_action=f"Add required DoR field '{field}'.",
                            message=f"Missing required DoR field '{field}'.",
                        )
                    )
                )
        for field in config.scrum.dod_required_fields:
            if _is_missing(item, field):
                findings.append(
                    normalize_policy_result(
                        PolicyResult(
                            rule_id=f"scrum.dod.{field}",
                            severity="error",
                            evidence_pointer=f"items[{idx}].{field}",
                            recommended_action=f"Add required DoD field '{field}'.",
                            message=f"Missing required DoD field '{field}'.",
                        )
                    )
                )
    return findings


def _is_missing(item: dict[str, Any], field: str) -> bool:
    value = item.get(field)
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, list):
        return len(value) == 0
    return False
