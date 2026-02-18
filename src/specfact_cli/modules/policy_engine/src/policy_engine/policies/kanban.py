"""Kanban policy family (entry/exit per column)."""

from __future__ import annotations

from typing import Any

from beartype import beartype
from icontract import ensure

from ..config.policy_config import PolicyConfig
from ..models.policy_result import PolicyResult, normalize_policy_result


@beartype
@ensure(lambda result: isinstance(result, list), "Must return a list of policy findings")
def build_kanban_failures(config: PolicyConfig, items: list[dict[str, Any]]) -> list[PolicyResult]:
    """Evaluate Kanban entry/exit rules for each item column."""
    findings: list[PolicyResult] = []
    column_rules = config.kanban.columns
    if not column_rules:
        return findings

    for idx, item in enumerate(items):
        column = str(item.get("column", "")).strip()
        if not column or column not in column_rules:
            continue
        rules = column_rules[column]
        for field in rules.entry_required_fields:
            if _is_missing(item, field):
                findings.append(
                    normalize_policy_result(
                        PolicyResult(
                            rule_id=f"kanban.entry.{column}.{field}",
                            severity="error",
                            evidence_pointer=f"items[{idx}].{field}",
                            recommended_action=f"Add required entry field '{field}' before column '{column}'.",
                            message=f"Missing required entry field '{field}' for column '{column}'.",
                        )
                    )
                )
        for field in rules.exit_required_fields:
            if _is_missing(item, field):
                findings.append(
                    normalize_policy_result(
                        PolicyResult(
                            rule_id=f"kanban.exit.{column}.{field}",
                            severity="error",
                            evidence_pointer=f"items[{idx}].{field}",
                            recommended_action=f"Add required exit field '{field}' before leaving column '{column}'.",
                            message=f"Missing required exit field '{field}' for column '{column}'.",
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
