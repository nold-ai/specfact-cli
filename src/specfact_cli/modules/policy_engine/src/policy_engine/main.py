"""Typer app for policy-engine commands."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Annotated, TypedDict

import typer
from beartype import beartype
from icontract import require
from rich.console import Console

from .config import list_policy_templates, load_policy_config, load_policy_template
from .engine.suggester import build_suggestions
from .engine.validator import load_snapshot_items, render_markdown, validate_policies
from .models.policy_result import PolicyResult


policy_app = typer.Typer(name="policy", help="Policy validation and suggestion workflows.")
console = Console()
_TEMPLATE_CHOICES = tuple(list_policy_templates())
_ITEM_POINTER_PATTERN = re.compile(r"items\[(?P<index>\d+)\]")


class FailureGroup(TypedDict):
    item_index: int
    failure_count: int
    failures: list[dict[str, object]]


class SuggestionGroup(TypedDict):
    item_index: int
    suggestion_count: int
    suggestions: list[dict[str, object]]


def _resolve_template_selection(template_name: str | None) -> str:
    if template_name is not None:
        return template_name.strip().lower()
    selected = typer.prompt(
        "Select policy template (scrum/kanban/safe/mixed)",
        default="scrum",
    )
    return selected.strip().lower()


def _normalize_rule_filters(rule_filters: list[str] | None) -> list[str]:
    if not rule_filters:
        return []
    tokens: list[str] = []
    for raw in rule_filters:
        for token in raw.split(","):
            stripped = token.strip()
            if stripped:
                tokens.append(stripped)
    return tokens


def _filter_findings_by_rule(findings: list[PolicyResult], rule_filters: list[str]) -> list[PolicyResult]:
    if not rule_filters:
        return findings
    return [finding for finding in findings if any(rule in finding.rule_id for rule in rule_filters)]


def _limit_findings_by_item(findings: list[PolicyResult], limit: int | None) -> list[PolicyResult]:
    if limit is None:
        return findings
    item_indexes = sorted(
        {
            item_index
            for finding in findings
            if (item_index := _extract_item_index(finding.evidence_pointer)) is not None
        }
    )
    allowed_indexes = set(item_indexes[:limit])
    return [
        finding
        for finding in findings
        if (item_index := _extract_item_index(finding.evidence_pointer)) is not None and item_index in allowed_indexes
    ]


def _extract_item_index(pointer: str) -> int | None:
    match = _ITEM_POINTER_PATTERN.search(pointer)
    if not match:
        return None
    return int(match.group("index"))


def _group_failures_by_item(findings: list[PolicyResult]) -> list[FailureGroup]:
    grouped: dict[int, list[PolicyResult]] = {}
    for finding in findings:
        item_index = _extract_item_index(finding.evidence_pointer)
        if item_index is None:
            continue
        grouped.setdefault(item_index, []).append(finding)
    return [
        {
            "item_index": item_index,
            "failure_count": len(item_findings),
            "failures": [finding.model_dump(mode="json") for finding in item_findings],
        }
        for item_index, item_findings in sorted(grouped.items())
    ]


def _render_grouped_markdown(findings: list[PolicyResult]) -> str:
    groups = _group_failures_by_item(findings)
    lines = [
        "# Policy Validation Results",
        "",
        f"- Findings: {len(findings)}",
        "",
    ]
    if not groups:
        lines.append("No grouped item findings available.")
        return "\n".join(lines) + "\n"
    for group in groups:
        item_index = group["item_index"]
        item_failures = group["failures"]
        lines.append(f"## Item {item_index} ({group['failure_count']} findings)")
        lines.append("")
        lines.append("| rule_id | severity | evidence_pointer | recommended_action |")
        lines.append("|---|---|---|---|")
        for failure in item_failures:
            lines.append(
                f"| {failure['rule_id']} | {failure['severity']} | {failure['evidence_pointer']} | {failure['recommended_action']} |"
            )
        lines.append("")
    return "\n".join(lines)


def _group_suggestions_by_item(suggestions: list[dict[str, object]]) -> list[SuggestionGroup]:
    grouped: dict[int, list[dict[str, object]]] = {}
    for suggestion in suggestions:
        patch = suggestion.get("patch")
        if not isinstance(patch, dict):
            continue
        path = patch.get("path")
        if not isinstance(path, str):
            continue
        item_index = _extract_item_index(path)
        if item_index is None:
            continue
        grouped.setdefault(item_index, []).append(suggestion)
    return [
        {
            "item_index": item_index,
            "suggestion_count": len(item_suggestions),
            "suggestions": item_suggestions,
        }
        for item_index, item_suggestions in sorted(grouped.items())
    ]


@policy_app.command("init")
@beartype
@require(lambda repo: repo.exists(), "Repository path must exist")
def init_command(
    repo: Annotated[Path, typer.Option("--repo", help="Repository root path.")] = Path("."),
    template: Annotated[str | None, typer.Option("--template", help="Template: scrum, kanban, safe, mixed.")] = None,
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing .specfact/policy.yaml.")] = False,
) -> None:
    """Scaffold .specfact/policy.yaml from built-in templates."""
    selected = _resolve_template_selection(template)
    if selected not in _TEMPLATE_CHOICES:
        options = ", ".join(_TEMPLATE_CHOICES)
        console.print(f"[red]Unsupported template '{selected}'. Available: {options}[/red]")
        raise typer.Exit(2)

    template_content, template_error = load_policy_template(selected)
    if template_error:
        console.print(f"[red]{template_error}[/red]")
        raise typer.Exit(1)
    assert template_content is not None

    config_path = repo / ".specfact" / "policy.yaml"
    if config_path.exists() and not force:
        console.print(f"[red]Policy config already exists: {config_path}. Use --force to overwrite.[/red]")
        raise typer.Exit(1)

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(template_content, encoding="utf-8")
    console.print(f"Created policy config from '{selected}' template: {config_path}")


@policy_app.command("validate")
@beartype
@require(lambda repo: repo.exists(), "Repository path must exist")
def validate_command(
    repo: Annotated[Path, typer.Option("--repo", help="Repository root path.")] = Path("."),
    snapshot: Annotated[
        Path | None,
        typer.Option(
            "--snapshot",
            help="Snapshot path. If omitted, auto-discovers .specfact/backlog-baseline.json then latest .specfact/plans/backlog-*.",
        ),
    ] = None,
    output_format: Annotated[str, typer.Option("--format", help="Output format: json, markdown, or both.")] = "both",
    rule: Annotated[
        list[str] | None,
        typer.Option("--rule", help="Filter findings by rule id (repeatable or comma-separated)."),
    ] = None,
    limit: Annotated[
        int | None,
        typer.Option("--limit", min=1, help="Limit findings (or item groups with --group-by-item)."),
    ] = None,
    group_by_item: Annotated[bool, typer.Option("--group-by-item", help="Group output by backlog item index.")] = False,
) -> None:
    """Run deterministic policy validation and report hard failures."""
    config, config_error = load_policy_config(repo)
    if config_error:
        console.print(f"[red]{config_error}[/red]")
        raise typer.Exit(1)
    assert config is not None

    items, snapshot_error = load_snapshot_items(repo, snapshot)
    if snapshot_error:
        console.print(f"[red]{snapshot_error}[/red]")
        raise typer.Exit(1)

    findings = validate_policies(config, items)
    rule_filters = _normalize_rule_filters(rule)
    findings = _filter_findings_by_rule(findings, rule_filters)
    findings = (
        _limit_findings_by_item(findings, limit)
        if group_by_item
        else findings[:limit]
        if limit is not None
        else findings
    )
    payload: dict[str, object] = {
        "summary": {
            "total_findings": len(findings),
            "status": "failed" if findings else "passed",
            "deterministic": True,
            "network_required": False,
            "rule_filter_count": len(rule_filters),
            "limit": limit,
        },
    }
    if group_by_item:
        payload["groups"] = _group_failures_by_item(findings)
    else:
        payload["failures"] = [finding.model_dump(mode="json") for finding in findings]

    normalized_format = output_format.strip().lower()
    if normalized_format not in ("json", "markdown", "both"):
        console.print("[red]Invalid format. Use: json, markdown, or both.[/red]")
        raise typer.Exit(2)

    if normalized_format in ("markdown", "both"):
        console.print(_render_grouped_markdown(findings) if group_by_item else render_markdown(findings))
    if normalized_format in ("json", "both"):
        console.print(json.dumps(payload, indent=2, sort_keys=True))

    if findings:
        raise typer.Exit(1)


@policy_app.command("suggest")
@beartype
@require(lambda repo: repo.exists(), "Repository path must exist")
def suggest_command(
    repo: Annotated[Path, typer.Option("--repo", help="Repository root path.")] = Path("."),
    snapshot: Annotated[
        Path | None,
        typer.Option(
            "--snapshot",
            help="Snapshot path. If omitted, auto-discovers .specfact/backlog-baseline.json then latest .specfact/plans/backlog-*.",
        ),
    ] = None,
    rule: Annotated[
        list[str] | None,
        typer.Option("--rule", help="Filter suggestions by rule id (repeatable or comma-separated)."),
    ] = None,
    limit: Annotated[
        int | None,
        typer.Option("--limit", min=1, help="Limit suggestions (or item groups with --group-by-item)."),
    ] = None,
    group_by_item: Annotated[
        bool, typer.Option("--group-by-item", help="Group suggestions by backlog item index.")
    ] = False,
) -> None:
    """Generate confidence-scored patch-ready policy suggestions without writing files."""
    config, config_error = load_policy_config(repo)
    if config_error:
        console.print(f"[red]{config_error}[/red]")
        raise typer.Exit(1)
    assert config is not None

    items, snapshot_error = load_snapshot_items(repo, snapshot)
    if snapshot_error:
        console.print(f"[red]{snapshot_error}[/red]")
        raise typer.Exit(1)

    findings = validate_policies(config, items)
    rule_filters = _normalize_rule_filters(rule)
    findings = _filter_findings_by_rule(findings, rule_filters)
    findings = (
        _limit_findings_by_item(findings, limit)
        if group_by_item
        else findings[:limit]
        if limit is not None
        else findings
    )
    suggestions = build_suggestions(findings)
    payload: dict[str, object] = {
        "summary": {
            "suggestion_count": len(suggestions),
            "patch_ready": True,
            "auto_write": False,
            "rule_filter_count": len(rule_filters),
            "limit": limit,
        },
    }
    if group_by_item:
        payload["grouped_suggestions"] = _group_suggestions_by_item(suggestions)
    else:
        payload["suggestions"] = suggestions
    console.print("# Policy Suggestions")
    console.print(json.dumps(payload, indent=2, sort_keys=True))
    console.print("No changes were written. Re-run with explicit apply workflow when available.")


# Backward-compatible module package loader expects an `app` attribute.
app = policy_app
