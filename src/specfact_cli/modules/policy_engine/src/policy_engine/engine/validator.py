"""Deterministic policy validation engine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure

from policy_engine.config.policy_config import PolicyConfig
from policy_engine.models.policy_result import PolicyResult
from policy_engine.policies import build_kanban_failures, build_safe_failures, build_scrum_failures
from policy_engine.registry.policy_registry import PolicyRegistry


@beartype
@ensure(lambda result: isinstance(result, tuple), "Loader must return tuple")
def load_snapshot_items(snapshot_path: Path | None) -> tuple[list[dict[str, Any]], str | None]:
    """Load snapshot items from JSON file."""
    if snapshot_path is None:
        return [], "Snapshot path is required for policy validation."
    if not snapshot_path.exists():
        return [], f"Snapshot file not found: {snapshot_path}"
    try:
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [], f"Invalid snapshot JSON in {snapshot_path}: {exc}"

    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        items = payload.get("items", [])
    else:
        return [], f"Invalid snapshot payload in {snapshot_path}: expected object or list"

    if not isinstance(items, list):
        return [], f"Invalid snapshot payload in {snapshot_path}: 'items' must be a list"

    normalized_items: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict):
            normalized_items.append(item)
    if not normalized_items:
        return [], f"Snapshot payload in {snapshot_path} does not contain any policy-evaluable items."
    return normalized_items, None


@beartype
@ensure(lambda result: isinstance(result, list), "Validation must return a list")
def validate_policies(
    config: PolicyConfig,
    items: list[dict[str, Any]],
    registry: PolicyRegistry | None = None,
) -> list[PolicyResult]:
    """Run deterministic policy validation across configured families."""
    findings: list[PolicyResult] = []
    findings.extend(build_scrum_failures(config, items))
    findings.extend(build_kanban_failures(config, items))
    findings.extend(build_safe_failures(config, items))

    if registry is not None:
        for evaluator in registry.get_all():
            findings.extend(evaluator(config, items))
    return findings


@beartype
def render_markdown(findings: list[PolicyResult]) -> str:
    """Render human-readable markdown output."""
    lines = [
        "# Policy Validation Results",
        "",
        f"- Findings: {len(findings)}",
        "",
    ]
    if not findings:
        lines.append("No policy failures found.")
        return "\n".join(lines) + "\n"

    lines.append("| rule_id | severity | evidence_pointer | recommended_action |")
    lines.append("|---|---|---|---|")
    for finding in findings:
        lines.append(
            f"| {finding.rule_id} | {finding.severity} | {finding.evidence_pointer} | {finding.recommended_action} |"
        )
    lines.append("")
    return "\n".join(lines)
