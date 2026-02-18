"""SAFe policy family (PI readiness hooks)."""

from __future__ import annotations

from typing import Any

from beartype import beartype
from icontract import ensure

from ..config.policy_config import PolicyConfig
from ..models.policy_result import PolicyResult, normalize_policy_result


@beartype
@ensure(lambda result: isinstance(result, list), "Must return a list of policy findings")
def build_safe_failures(config: PolicyConfig, items: list[dict[str, Any]]) -> list[PolicyResult]:
    """Evaluate SAFe PI readiness required fields."""
    findings: list[PolicyResult] = []
    if not config.safe.pi_readiness_required_fields:
        return findings

    for idx, item in enumerate(items):
        for field in config.safe.pi_readiness_required_fields:
            if _is_missing(item, field):
                findings.append(
                    normalize_policy_result(
                        PolicyResult(
                            rule_id=f"safe.pi_readiness.{field}",
                            severity="error",
                            evidence_pointer=f"items[{idx}].{field}",
                            recommended_action=f"Add PI readiness field '{field}'.",
                            message=f"Missing required PI readiness field '{field}'.",
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
