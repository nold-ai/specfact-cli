"""Deterministic policy validation engine."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml
from beartype import beartype
from icontract import ensure

from ..config.policy_config import PolicyConfig
from ..models.policy_result import PolicyResult
from ..policies import build_kanban_failures, build_safe_failures, build_scrum_failures
from ..registry.policy_registry import PolicyRegistry


@beartype
@ensure(lambda result: isinstance(result, tuple), "Loader must return tuple")
def load_snapshot_items(repo_path: Path, snapshot_path: Path | None) -> tuple[list[dict[str, Any]], str | None]:
    """Load snapshot items from explicit input or known .specfact artifacts."""
    resolved_path, resolve_error = _resolve_snapshot_path(repo_path, snapshot_path)
    if resolve_error:
        return [], resolve_error
    assert resolved_path is not None

    payload, payload_error = _load_payload(resolved_path)
    if payload_error:
        return [], payload_error
    assert payload is not None

    items = _extract_items(payload)
    if not isinstance(items, list):
        return [], f"Invalid snapshot payload in {resolved_path}: 'items' must be a list or mapping"

    normalized_items: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict):
            normalized_items.append(_normalize_policy_item(item))
    if not normalized_items:
        return [], f"Snapshot payload in {resolved_path} does not contain any policy-evaluable items."
    return normalized_items, None


@beartype
def _resolve_snapshot_path(repo_path: Path, snapshot_path: Path | None) -> tuple[Path | None, str | None]:
    if snapshot_path is not None:
        resolved_snapshot = snapshot_path if snapshot_path.is_absolute() else repo_path / snapshot_path
        if not resolved_snapshot.exists():
            return None, f"Snapshot file not found: {resolved_snapshot}"
        return resolved_snapshot, None

    baseline_path = repo_path / ".specfact" / "backlog-baseline.json"
    if baseline_path.exists():
        return baseline_path, None

    plans_dir = repo_path / ".specfact" / "plans"
    if plans_dir.exists():
        candidates = [
            *plans_dir.glob("backlog-*.yaml"),
            *plans_dir.glob("backlog-*.yml"),
            *plans_dir.glob("backlog-*.json"),
        ]
        if candidates:
            latest = max(candidates, key=lambda path: path.stat().st_mtime)
            return latest, None

    return (
        None,
        "No policy input artifact found. Provide --snapshot or generate one via "
        "`specfact project snapshot` / `specfact backlog sync`.",
    )


@beartype
def _load_payload(snapshot_path: Path) -> tuple[Any | None, str | None]:
    if snapshot_path is None:
        return None, "Snapshot path is required for policy validation."
    try:
        raw = snapshot_path.read_text(encoding="utf-8")
        payload = yaml.safe_load(raw) if snapshot_path.suffix.lower() in {".yaml", ".yml"} else json.loads(raw)
    except Exception as exc:
        return None, f"Invalid snapshot payload in {snapshot_path}: {exc}"

    return payload, None


@beartype
def _extract_items(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload

    if not isinstance(payload, dict):
        return []

    if "items" in payload:
        return _coerce_items(payload.get("items"))

    backlog_graph = payload.get("backlog_graph")
    if isinstance(backlog_graph, dict) and "items" in backlog_graph:
        return _coerce_items(backlog_graph.get("items"))

    return []


@beartype
def _coerce_items(items: Any) -> list[Any]:
    if isinstance(items, list):
        return items
    if isinstance(items, dict):
        return [value for value in items.values() if isinstance(value, dict)]
    return []


@beartype
def _normalize_policy_item(item: dict[str, Any]) -> dict[str, Any]:
    """Map common imported artifact aliases into canonical policy field names."""
    normalized = dict(item)
    raw_data = normalized.get("raw_data")
    raw = raw_data if isinstance(raw_data, dict) else {}

    acceptance_criteria = _first_present(
        normalized,
        raw,
        [
            "acceptance_criteria",
            "acceptanceCriteria",
            "System.AcceptanceCriteria",
            "acceptance criteria",
        ],
    )
    if _is_missing_value(acceptance_criteria):
        acceptance_criteria = _extract_markdown_section(
            str(normalized.get("description") or ""), section_names=("acceptance criteria",)
        )
    if not _is_missing_value(acceptance_criteria):
        normalized["acceptance_criteria"] = acceptance_criteria

    business_value = _first_present(
        normalized,
        raw,
        [
            "business_value",
            "businessValue",
            "Microsoft.VSTS.Common.BusinessValue",
            "business value",
        ],
    )
    if not _is_missing_value(business_value):
        normalized["business_value"] = business_value

    definition_of_done = _first_present(
        normalized,
        raw,
        [
            "definition_of_done",
            "definitionOfDone",
            "System.DefinitionOfDone",
            "definition of done",
        ],
    )
    if _is_missing_value(definition_of_done):
        definition_of_done = _extract_markdown_section(
            str(normalized.get("description") or ""), section_names=("definition of done",)
        )
    if not _is_missing_value(definition_of_done):
        normalized["definition_of_done"] = definition_of_done

    return normalized


@beartype
def _first_present(primary: dict[str, Any], secondary: dict[str, Any], keys: list[str]) -> Any | None:
    for key in keys:
        if key in primary and not _is_missing_value(primary.get(key)):
            return primary.get(key)
        if key in secondary and not _is_missing_value(secondary.get(key)):
            return secondary.get(key)
    return None


@beartype
def _extract_markdown_section(description: str, section_names: tuple[str, ...]) -> str | None:
    if not description.strip():
        return None
    lines = description.splitlines()
    collecting = False
    buffer: list[str] = []
    normalized_names = {name.strip().lower() for name in section_names}
    heading_pattern = re.compile(r"^\s{0,3}#{1,6}\s+(?P<title>.+?)\s*$")
    for line in lines:
        match = heading_pattern.match(line)
        if match:
            heading_title = match.group("title").strip().lower()
            if collecting:
                break
            collecting = heading_title in normalized_names
            continue
        if collecting:
            buffer.append(line)
    content = "\n".join(buffer).strip()
    return content or None


@beartype
def _is_missing_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, list):
        return len(value) == 0
    return False


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
