"""
Backlog refinement commands.

This module provides the `specfact backlog refine` command for AI-assisted
backlog refinement with template detection and matching.

SpecFact CLI Architecture:
- SpecFact CLI generates prompts/instructions for IDE AI copilots
- IDE AI copilots execute those instructions using their native LLM
- IDE AI copilots feed results back to SpecFact CLI
- SpecFact CLI validates and processes the results
"""

from __future__ import annotations

import contextlib
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import typer
import yaml
from beartype import beartype
from icontract import ensure, require
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Confirm
from rich.table import Table

from specfact_cli.adapters.registry import AdapterRegistry
from specfact_cli.backlog.adapters.base import BacklogAdapter
from specfact_cli.backlog.ai_refiner import BacklogAIRefiner
from specfact_cli.backlog.filters import BacklogFilters
from specfact_cli.backlog.template_detector import TemplateDetector
from specfact_cli.models.backlog_item import BacklogItem
from specfact_cli.models.dor_config import DefinitionOfReady
from specfact_cli.models.plan import Product
from specfact_cli.models.project import BundleManifest, ProjectBundle
from specfact_cli.models.validation import ValidationReport
from specfact_cli.runtime import debug_log_operation, is_debug_mode
from specfact_cli.templates.registry import BacklogTemplate, TemplateRegistry


app = typer.Typer(
    name="backlog",
    help="Backlog refinement and template management",
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


@beartype
@require(lambda source: source.exists(), "Source path must exist")
@ensure(lambda result: isinstance(result, ProjectBundle), "Must return ProjectBundle")
def import_to_bundle(source: Path, config: dict[str, Any]) -> ProjectBundle:
    """Convert external source artifacts into a ProjectBundle."""
    if source.is_dir() and (source / "bundle.manifest.yaml").exists():
        return ProjectBundle.load_from_directory(source)
    bundle_name = config.get("bundle_name", source.stem if source.suffix else source.name)
    return ProjectBundle(
        manifest=BundleManifest(schema_metadata=None, project_metadata=None),
        bundle_name=str(bundle_name),
        product=Product(),
    )


@beartype
@require(lambda target: target is not None, "Target path must be provided")
@ensure(lambda target: target.exists(), "Target must exist after export")
def export_from_bundle(bundle: ProjectBundle, target: Path, config: dict[str, Any]) -> None:
    """Export a ProjectBundle to target path."""
    if target.suffix:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(bundle.model_dump_json(indent=2), encoding="utf-8")
        return
    target.mkdir(parents=True, exist_ok=True)
    bundle.save_to_directory(target)


@beartype
@require(lambda external_source: len(external_source.strip()) > 0, "External source must be non-empty")
@ensure(lambda result: isinstance(result, ProjectBundle), "Must return ProjectBundle")
def sync_with_bundle(bundle: ProjectBundle, external_source: str, config: dict[str, Any]) -> ProjectBundle:
    """Synchronize an existing bundle with an external source."""
    source_path = Path(external_source)
    if source_path.exists() and source_path.is_dir() and (source_path / "bundle.manifest.yaml").exists():
        return ProjectBundle.load_from_directory(source_path)
    return bundle


@beartype
@ensure(lambda result: isinstance(result, ValidationReport), "Must return ValidationReport")
def validate_bundle(bundle: ProjectBundle, rules: dict[str, Any]) -> ValidationReport:
    """Validate bundle for module-specific constraints."""
    total_checks = max(len(rules), 1)
    report = ValidationReport(
        status="passed",
        violations=[],
        summary={"total_checks": total_checks, "passed": total_checks, "failed": 0, "warnings": 0},
    )
    if not bundle.bundle_name:
        report.status = "failed"
        report.violations.append(
            {
                "severity": "error",
                "message": "Bundle name is required",
                "location": "ProjectBundle.bundle_name",
            }
        )
        report.summary["failed"] += 1
        report.summary["passed"] = max(report.summary["passed"] - 1, 0)
    return report


def _apply_filters(
    items: list[BacklogItem],
    labels: list[str] | None = None,
    state: str | None = None,
    assignee: str | None = None,
    iteration: str | None = None,
    sprint: str | None = None,
    release: str | None = None,
) -> list[BacklogItem]:
    """
    Apply post-fetch filters to backlog items.

    Args:
        items: List of BacklogItem instances to filter
        labels: Filter by labels/tags (any label must match)
        state: Filter by state (exact match)
        assignee: Filter by assignee (exact match)
        iteration: Filter by iteration path (exact match)
        sprint: Filter by sprint (exact match)
        release: Filter by release (exact match)

    Returns:
        Filtered list of BacklogItem instances
    """
    filtered = items

    # Filter by labels/tags (any label must match)
    if labels:
        filtered = [
            item for item in filtered if any(label.lower() in [tag.lower() for tag in item.tags] for label in labels)
        ]

    # Filter by state (case-insensitive)
    if state:
        normalized_state = BacklogFilters.normalize_filter_value(state)
        filtered = [item for item in filtered if BacklogFilters.normalize_filter_value(item.state) == normalized_state]

    # Filter by assignee (case-insensitive)
    # Matches against any identifier in assignees list (displayName, uniqueName, or mail for ADO)
    if assignee:
        normalized_assignee = BacklogFilters.normalize_filter_value(assignee)
        filtered = [
            item
            for item in filtered
            if item.assignees  # Only check items with assignees
            and any(
                BacklogFilters.normalize_filter_value(a) == normalized_assignee
                for a in item.assignees
                if a  # Skip None or empty strings
            )
        ]

    # Filter by iteration (case-insensitive)
    if iteration:
        normalized_iteration = BacklogFilters.normalize_filter_value(iteration)
        filtered = [
            item
            for item in filtered
            if item.iteration and BacklogFilters.normalize_filter_value(item.iteration) == normalized_iteration
        ]

    # Filter by sprint (case-insensitive)
    if sprint:
        normalized_sprint = BacklogFilters.normalize_filter_value(sprint)
        filtered = [
            item
            for item in filtered
            if item.sprint and BacklogFilters.normalize_filter_value(item.sprint) == normalized_sprint
        ]

    # Filter by release (case-insensitive)
    if release:
        normalized_release = BacklogFilters.normalize_filter_value(release)
        filtered = [
            item
            for item in filtered
            if item.release and BacklogFilters.normalize_filter_value(item.release) == normalized_release
        ]

    return filtered


def _parse_standup_from_body(body: str) -> tuple[str | None, str | None, str | None]:
    """Extract yesterday/today/blockers lines from body (standup format)."""
    yesterday: str | None = None
    today: str | None = None
    blockers: str | None = None
    if not body:
        return yesterday, today, blockers
    for line in body.splitlines():
        line_stripped = line.strip()
        if re.match(r"^\*\*[Yy]esterday(?:\*\*|:)\s*\*\*\s*", line_stripped):
            yesterday = re.sub(r"^\*\*[Yy]esterday(?:\*\*|:)\s*\*\*\s*", "", line_stripped).strip()
        elif re.match(r"^\*\*[Tt]oday(?:\*\*|:)\s*\*\*\s*", line_stripped):
            today = re.sub(r"^\*\*[Tt]oday(?:\*\*|:)\s*\*\*\s*", "", line_stripped).strip()
        elif re.match(r"^\*\*[Bb]lockers?(?:\*\*|:)\s*\*\*\s*", line_stripped):
            blockers = re.sub(r"^\*\*[Bb]lockers?(?:\*\*|:)\s*\*\*\s*", "", line_stripped).strip()
    return yesterday, today, blockers


def _load_standup_config() -> dict[str, Any]:
    """Load standup config from env and optional .specfact/standup.yaml. Env overrides file."""
    config: dict[str, Any] = {}
    config_dir = os.environ.get("SPECFACT_CONFIG_DIR")
    search_paths: list[Path] = []
    if config_dir:
        search_paths.append(Path(config_dir))
    search_paths.append(Path.cwd() / ".specfact")
    for base in search_paths:
        path = base / "standup.yaml"
        if path.is_file():
            try:
                with open(path, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                config = dict(data.get("standup", data))
            except Exception as exc:
                debug_log_operation("config_load", str(path), "error", error=repr(exc))
            break
    if os.environ.get("SPECFACT_STANDUP_STATE"):
        config["default_state"] = os.environ["SPECFACT_STANDUP_STATE"]
    if os.environ.get("SPECFACT_STANDUP_LIMIT"):
        with contextlib.suppress(ValueError):
            config["limit"] = int(os.environ["SPECFACT_STANDUP_LIMIT"])
    if os.environ.get("SPECFACT_STANDUP_ASSIGNEE"):
        config["default_assignee"] = os.environ["SPECFACT_STANDUP_ASSIGNEE"]
    return config


def _load_backlog_config() -> dict[str, Any]:
    """Load project backlog context from .specfact/backlog.yaml (no secrets).
    Same search path as standup: SPECFACT_CONFIG_DIR then .specfact in cwd.
    When file has top-level 'backlog' key, that nested structure is returned.
    """
    config: dict[str, Any] = {}
    config_dir = os.environ.get("SPECFACT_CONFIG_DIR")
    search_paths: list[Path] = []
    if config_dir:
        search_paths.append(Path(config_dir))
    search_paths.append(Path.cwd() / ".specfact")
    for base in search_paths:
        path = base / "backlog.yaml"
        if path.is_file():
            try:
                with open(path, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                if isinstance(data, dict) and "backlog" in data:
                    nested = data["backlog"]
                    config = dict(nested) if isinstance(nested, dict) else {}
                else:
                    config = dict(data) if isinstance(data, dict) else {}
            except Exception as exc:
                debug_log_operation("config_load", str(path), "error", error=repr(exc))
            break
    return config


@beartype
def _resolve_standup_options(
    cli_state: str | None,
    cli_limit: int | None,
    cli_assignee: str | None,
    config: dict[str, Any] | None,
) -> tuple[str, int, str | None]:
    """
    Resolve effective state, limit, assignee from CLI options and config.
    CLI options override config; config overrides built-in defaults.
    Returns (state, limit, assignee).
    """
    cfg = config or _load_standup_config()
    default_state = str(cfg.get("default_state", "open"))
    default_limit = int(cfg.get("limit", 20)) if cfg.get("limit") is not None else 20
    default_assignee = cfg.get("default_assignee")
    if default_assignee is not None:
        default_assignee = str(default_assignee)
    state = cli_state if cli_state is not None else default_state
    limit = cli_limit if cli_limit is not None else default_limit
    assignee = cli_assignee if cli_assignee is not None else default_assignee
    return (state, limit, assignee)


@beartype
def _resolve_post_fetch_assignee_filter(adapter: str, assignee: str | None) -> str | None:
    """
    Resolve assignee value for local post-fetch filtering.

    For GitHub, `me`/`@me` should be handled by adapter-side query semantics and
    not re-filtered locally as a literal username.
    """
    if not assignee:
        return assignee
    if adapter.lower() == "github":
        normalized = BacklogFilters.normalize_filter_value(assignee.lstrip("@"))
        if normalized == "me":
            return None
    return assignee


@beartype
def _split_assigned_unassigned(items: list[BacklogItem]) -> tuple[list[BacklogItem], list[BacklogItem]]:
    """Split items into assigned and unassigned (assignees empty or None)."""
    assigned: list[BacklogItem] = []
    unassigned: list[BacklogItem] = []
    for item in items:
        if item.assignees:
            assigned.append(item)
        else:
            unassigned.append(item)
    return (assigned, unassigned)


def _format_sprint_end_header(end_date: date) -> str:
    """Format sprint end date as 'Sprint ends: YYYY-MM-DD (N days)'."""
    today = date.today()
    delta = (end_date - today).days
    return f"Sprint ends: {end_date.isoformat()} ({delta} days)"


@beartype
def _sort_standup_rows_blockers_first(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort standup rows so items with non-empty blockers appear first."""
    with_blockers = [r for r in rows if (r.get("blockers") or "").strip()]
    without = [r for r in rows if not (r.get("blockers") or "").strip()]
    return with_blockers + without


@beartype
def _build_standup_rows(
    items: list[BacklogItem],
    include_priority: bool = False,
) -> list[dict[str, Any]]:
    """
    Build standup view rows from backlog items (id, title, status, last_updated, optional yesterday/today/blockers).
    When include_priority is True and item has priority/business_value, add to row.
    """
    rows: list[dict[str, Any]] = []
    for item in items:
        yesterday, today, blockers = _parse_standup_from_body(item.body_markdown or "")
        row: dict[str, Any] = {
            "id": item.id,
            "title": item.title,
            "status": item.state,
            "assignees": ", ".join(item.assignees) if item.assignees else "—",
            "last_updated": item.updated_at,
            "yesterday": yesterday or "",
            "today": today or "",
            "blockers": blockers or "",
        }
        if include_priority and item.priority is not None:
            row["priority"] = item.priority
        elif include_priority and item.business_value is not None:
            row["priority"] = item.business_value
        rows.append(row)
    return rows


@beartype
def _format_standup_comment(yesterday: str, today: str, blockers: str) -> str:
    """Format standup text as a comment (Yesterday / Today / Blockers) with date prefix."""
    prefix = f"Standup {date.today().isoformat()}"
    parts = [prefix, ""]
    if yesterday:
        parts.append(f"**Yesterday:** {yesterday}")
    if today:
        parts.append(f"**Today:** {today}")
    if blockers:
        parts.append(f"**Blockers:** {blockers}")
    return "\n".join(parts).strip()


@beartype
def _post_standup_comment_supported(adapter: BacklogAdapter, item: BacklogItem) -> bool:
    """Return True if the adapter supports adding comments (e.g. for standup post)."""
    return adapter.supports_add_comment()


@beartype
def _post_standup_to_item(adapter: BacklogAdapter, item: BacklogItem, body: str) -> bool:
    """Post standup comment to the linked issue via adapter. Returns True on success."""
    return adapter.add_comment(item, body)


@beartype
@ensure(
    lambda result: result is None or (isinstance(result, (int, float)) and result >= 0),
    "Value score is non-negative when present",
)
def _compute_value_score(item: BacklogItem) -> float | None:
    """
    Compute value score for next-best suggestion: business_value / max(1, story_points * priority).

    Returns None when any of story_points, business_value, or priority is missing.
    """
    if item.story_points is None or item.business_value is None or item.priority is None:
        return None
    denom = max(1, (item.story_points or 0) * (item.priority or 1))
    return item.business_value / denom


@beartype
def _format_daily_item_detail(
    item: BacklogItem,
    comments: list[str],
    *,
    show_all_provided_comments: bool = False,
    total_comments: int | None = None,
) -> str:
    """
    Format a single backlog item for interactive detail view (refine-like).

    Includes ID, title, status, assignees, last updated, description, acceptance criteria,
    standup fields (yesterday/today/blockers), and comments when provided.
    """
    parts: list[str] = []
    parts.append(f"## {item.id} - {item.title}")
    parts.append(f"- **Status:** {item.state}")
    assignee_str = ", ".join(item.assignees) if item.assignees else "—"
    parts.append(f"- **Assignees:** {assignee_str}")
    updated = (
        item.updated_at.strftime("%Y-%m-%d %H:%M") if hasattr(item.updated_at, "strftime") else str(item.updated_at)
    )
    parts.append(f"- **Last updated:** {updated}")
    if item.body_markdown:
        parts.append("\n**Description:**")
        parts.append(item.body_markdown.strip())
    if item.acceptance_criteria:
        parts.append("\n**Acceptance criteria:**")
        parts.append(item.acceptance_criteria.strip())
    yesterday, today, blockers = _parse_standup_from_body(item.body_markdown or "")
    if yesterday or today or blockers:
        parts.append("\n**Standup:**")
        if yesterday:
            parts.append(f"- Yesterday: {yesterday}")
        if today:
            parts.append(f"- Today: {today}")
        if blockers:
            parts.append(f"- Blockers: {blockers}")
    if item.story_points is not None:
        parts.append(f"\n- **Story points:** {item.story_points}")
    if item.business_value is not None:
        parts.append(f"- **Business value:** {item.business_value}")
    if item.priority is not None:
        parts.append(f"- **Priority:** {item.priority}")
    _ = (comments, show_all_provided_comments, total_comments)
    return "\n".join(parts)


@beartype
def _apply_comment_window(
    comments: list[str],
    *,
    first_comments: int | None = None,
    last_comments: int | None = None,
) -> list[str]:
    """Apply optional first/last comment window; default returns all comments."""
    if first_comments is not None and last_comments is not None:
        msg = "Use only one of --first-comments or --last-comments."
        raise ValueError(msg)
    if first_comments is not None:
        return comments[: max(first_comments, 0)]
    if last_comments is not None:
        return comments[-last_comments:] if last_comments > 0 else []
    return comments


@beartype
def _apply_issue_window(
    items: list[BacklogItem],
    *,
    first_issues: int | None = None,
    last_issues: int | None = None,
) -> list[BacklogItem]:
    """Apply optional first/last issue window to already-filtered items."""
    if first_issues is not None and last_issues is not None:
        msg = "Use only one of --first-issues or --last-issues."
        raise ValueError(msg)
    if first_issues is not None or last_issues is not None:

        def _issue_number(item: BacklogItem) -> int:
            if item.id.isdigit():
                return int(item.id)
            issue_match = re.search(r"/issues/(\d+)", item.url or "")
            if issue_match:
                return int(issue_match.group(1))
            ado_match = re.search(r"/(?:_workitems/edit|workitems)/(\d+)", item.url or "", re.IGNORECASE)
            if ado_match:
                return int(ado_match.group(1))
            return sys.maxsize

        sorted_items = sorted(items, key=_issue_number)
        if first_issues is not None:
            return sorted_items[: max(first_issues, 0)]
        if last_issues is not None:
            return sorted_items[-last_issues:] if last_issues > 0 else []
    return items


@beartype
def _apply_issue_id_filter(items: list[BacklogItem], issue_id: str | None) -> list[BacklogItem]:
    """Apply optional exact issue/work-item ID filter."""
    if issue_id is None:
        return items
    return [i for i in items if str(i.id) == str(issue_id)]


@beartype
def _resolve_refine_preview_comment_window(
    *,
    first_comments: int | None,
    last_comments: int | None,
) -> tuple[int | None, int | None]:
    """Resolve comment window for refine preview output."""
    if first_comments is not None:
        return first_comments, None
    if last_comments is not None:
        return None, last_comments
    # Keep preview concise by default while still showing current discussion.
    return None, 2


@beartype
def _resolve_refine_export_comment_window(
    *,
    first_comments: int | None,
    last_comments: int | None,
) -> tuple[int | None, int | None]:
    """Resolve comment window for refine export output (always full history)."""
    _ = (first_comments, last_comments)
    return None, None


@beartype
def _resolve_daily_issue_window(
    items: list[BacklogItem],
    *,
    first_issues: int | None,
    last_issues: int | None,
) -> list[BacklogItem]:
    """Resolve and apply daily issue-window options with refine-aligned semantics."""
    if first_issues is not None and last_issues is not None:
        msg = "Use only one of --first-issues or --last-issues"
        raise ValueError(msg)
    return _apply_issue_window(items, first_issues=first_issues, last_issues=last_issues)


@beartype
def _resolve_daily_fetch_limit(
    effective_limit: int,
    *,
    first_issues: int | None,
    last_issues: int | None,
) -> int | None:
    """Resolve pre-fetch limit for daily command."""
    if first_issues is not None or last_issues is not None:
        return None
    return effective_limit


@beartype
def _resolve_daily_display_limit(
    effective_limit: int,
    *,
    first_issues: int | None,
    last_issues: int | None,
) -> int | None:
    """Resolve post-window display limit for daily command."""
    if first_issues is not None or last_issues is not None:
        return None
    return effective_limit


@beartype
def _resolve_daily_mode_state(
    *,
    mode: str,
    cli_state: str | None,
    effective_state: str | None,
) -> str | None:
    """Resolve daily state behavior per mode while preserving explicit CLI state."""
    if cli_state is not None:
        return effective_state
    if mode == "kanban":
        return None
    return effective_state


@beartype
def _has_policy_failure(row: dict[str, Any]) -> bool:
    """Return True when row indicates a policy failure signal."""
    policy_status = str(row.get("policy_status", "")).strip().lower()
    if policy_status in {"failed", "fail", "violation", "violated"}:
        return True
    failures = row.get("policy_failures")
    if isinstance(failures, list):
        return len(failures) > 0
    return bool(failures)


@beartype
def _has_aging_or_stalled_signal(row: dict[str, Any]) -> bool:
    """Return True when row indicates aging/stalled work."""
    stalled = row.get("stalled")
    if isinstance(stalled, bool):
        if stalled:
            return True
    elif str(stalled).strip().lower() in {"true", "yes", "1"}:
        return True
    days_stalled = row.get("days_stalled")
    if isinstance(days_stalled, (int, float)):
        return days_stalled > 0
    aging_days = row.get("aging_days")
    if isinstance(aging_days, (int, float)):
        return aging_days > 0
    return False


@beartype
def _exception_priority(row: dict[str, Any]) -> int:
    """Return exception priority rank: blockers, policy, aging, normal."""
    if str(row.get("blockers", "")).strip():
        return 0
    if _has_policy_failure(row):
        return 1
    if _has_aging_or_stalled_signal(row):
        return 2
    return 3


@beartype
def _split_exception_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split standup rows into exceptions-first and normal rows with stable ordering."""
    exceptions = sorted((row for row in rows if _exception_priority(row) < 3), key=_exception_priority)
    normal = [row for row in rows if _exception_priority(row) == 3]
    return exceptions, normal


@beartype
def _build_daily_patch_proposal(items: list[BacklogItem], *, mode: str) -> str:
    """Build a non-destructive patch proposal preview for standup notes."""
    lines: list[str] = []
    lines.append("# Patch Proposal")
    lines.append("")
    lines.append(f"- Mode: {mode}")
    lines.append(f"- Items in scope: {len(items)}")
    lines.append("- Action: Propose standup note/field updates only (no silent writes).")
    lines.append("")
    lines.append("## Candidate Items")
    for item in items[:10]:
        lines.append(f"- {item.id}: {item.title}")
    if len(items) > 10:
        lines.append(f"- ... and {len(items) - 10} more")
    return "\n".join(lines)


@beartype
def _is_patch_mode_available() -> bool:
    """Detect whether patch command group is available in current installation."""
    try:
        result = subprocess.run(
            ["specfact", "patch", "--help"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


@beartype
def _build_comment_fetch_progress_description(index: int, total: int, item_id: str) -> str:
    """Build progress text while fetching per-item comments."""
    return f"[cyan]Fetching issue {index}/{total} comments (ID: {item_id})...[/cyan]"


@beartype
def _build_refine_preview_comment_panels(comments: list[str]) -> list[Panel]:
    """Render refine preview comments as scoped panel blocks."""
    total = len(comments)
    panels: list[Panel] = []
    for index, comment in enumerate(comments, 1):
        body = comment.strip() if comment.strip() else "[dim](empty comment)[/dim]"
        panels.append(Panel(body, title=f"Comment {index}/{total}", border_style="cyan"))
    return panels


@beartype
def _build_refine_preview_comment_empty_panel() -> Panel:
    """Render explicit empty-state panel when no comments are found."""
    return Panel("[dim](no comments found)[/dim]", title="Comments", border_style="dim")


@beartype
def _build_daily_interactive_comment_panels(
    comments: list[str],
    *,
    show_all_provided_comments: bool,
    total_comments: int,
) -> list[Panel]:
    """Render daily interactive comments with refine-like scoped panels."""
    if not comments:
        return [_build_refine_preview_comment_empty_panel()]

    if show_all_provided_comments:
        panels = _build_refine_preview_comment_panels(comments)
        omitted_count = max(total_comments - len(comments), 0)
        if omitted_count > 0:
            panels.append(
                Panel(
                    f"[dim]{omitted_count} additional comment(s) omitted by comment window.[/dim]\n"
                    "[dim]Hint: increase --first-comments/--last-comments or use export options for full history.[/dim]",
                    title="Comment Window",
                    border_style="dim",
                )
            )
        return panels

    latest = comments[-1].strip() if comments[-1].strip() else "[dim](empty comment)[/dim]"
    panels: list[Panel] = [Panel(latest, title="Latest Comment", border_style="cyan")]
    hidden_count = max(total_comments - 1, 0)
    if hidden_count > 0:
        panels.append(
            Panel(
                f"[dim]{hidden_count} older comment(s) hidden in interactive view.[/dim]\n"
                "[dim]Hint: use `specfact backlog refine --export-to-tmp` or "
                "`specfact backlog daily --copilot-export <path> --comments` for full history.[/dim]",
                title="Comments Hint",
                border_style="dim",
            )
        )
    return panels


@beartype
def _build_daily_navigation_choices(*, can_post_comment: bool) -> list[str]:
    """Build interactive daily navigation choices."""
    choices = ["Next story", "Previous story"]
    if can_post_comment:
        choices.append("Post standup update")
    choices.extend(["Back to list", "Exit"])
    return choices


@beartype
def _build_interactive_post_body(yesterday: str | None, today: str | None, blockers: str | None) -> str | None:
    """Build standup comment body from interactive inputs."""
    y = (yesterday or "").strip()
    t = (today or "").strip()
    b = (blockers or "").strip()
    if not y and not t and not b:
        return None
    return _format_standup_comment(y, t, b)


def _collect_comment_annotations(
    adapter: str,
    items: list[BacklogItem],
    *,
    repo_owner: str | None,
    repo_name: str | None,
    github_token: str | None,
    ado_org: str | None,
    ado_project: str | None,
    ado_token: str | None,
    first_comments: int | None = None,
    last_comments: int | None = None,
    progress_callback: Callable[[int, int, BacklogItem], None] | None = None,
) -> dict[str, list[str]]:
    """
    Collect comment annotations for backlog items when the adapter supports get_comments().

    Returns a mapping of item ID -> list of comment strings. Returns empty dict if not supported.
    """
    comments_by_item_id: dict[str, list[str]] = {}
    try:
        adapter_kwargs = _build_adapter_kwargs(
            adapter,
            repo_owner=repo_owner,
            repo_name=repo_name,
            github_token=github_token,
            ado_org=ado_org,
            ado_project=ado_project,
            ado_token=ado_token,
        )
        registry = AdapterRegistry()
        adapter_instance = registry.get_adapter(adapter, **adapter_kwargs)
        if not isinstance(adapter_instance, BacklogAdapter):
            return comments_by_item_id
        get_comments_fn = getattr(adapter_instance, "get_comments", None)
        if not callable(get_comments_fn):
            return comments_by_item_id
        total_items = len(items)
        for index, item in enumerate(items, 1):
            if progress_callback is not None:
                progress_callback(index, total_items, item)
            with contextlib.suppress(Exception):
                raw = get_comments_fn(item)
                comments = list(raw) if isinstance(raw, list) else []
                comments_by_item_id[item.id] = _apply_comment_window(
                    comments,
                    first_comments=first_comments,
                    last_comments=last_comments,
                )
    except Exception:
        return comments_by_item_id
    return comments_by_item_id


@beartype
def _build_copilot_export_content(
    items: list[BacklogItem],
    include_value_score: bool = False,
    include_comments: bool = False,
    comments_by_item_id: dict[str, list[str]] | None = None,
) -> str:
    """
    Build Markdown content for Copilot export: one section per item.

    Per item: ID, title, status, assignees, last updated, progress summary (standup fields),
    blockers, optional value score, and optionally description/comments when enabled.
    """
    lines: list[str] = []
    lines.append("# Daily standup – Copilot export")
    lines.append("")
    comments_map = comments_by_item_id or {}
    for item in items:
        lines.append(f"## {item.id} - {item.title}")
        lines.append("")
        lines.append(f"- **Status:** {item.state}")
        assignee_str = ", ".join(item.assignees) if item.assignees else "—"
        lines.append(f"- **Assignees:** {assignee_str}")
        updated = (
            item.updated_at.strftime("%Y-%m-%d %H:%M") if hasattr(item.updated_at, "strftime") else str(item.updated_at)
        )
        lines.append(f"- **Last updated:** {updated}")
        if include_comments:
            body = (item.body_markdown or "").strip()
            if body:
                snippet = body[:_SUMMARIZE_BODY_TRUNCATE]
                if len(body) > _SUMMARIZE_BODY_TRUNCATE:
                    snippet += "\n..."
                lines.append("- **Description:**")
                for line in snippet.splitlines():
                    lines.append(f"  {line}" if line else "  ")
        yesterday, today, blockers = _parse_standup_from_body(item.body_markdown or "")
        if yesterday or today:
            lines.append(f"- **Progress:** Yesterday: {yesterday or '—'}; Today: {today or '—'}")
        if blockers:
            lines.append(f"- **Blockers:** {blockers}")
        if include_comments:
            item_comments = comments_map.get(item.id, [])
            if item_comments:
                lines.append("- **Comments (annotations):**")
                for c in item_comments:
                    lines.append(f"  - {c}")
        if item.story_points is not None:
            lines.append(f"- **Story points:** {item.story_points}")
        if item.priority is not None:
            lines.append(f"- **Priority:** {item.priority}")
        if include_value_score:
            score = _compute_value_score(item)
            if score is not None:
                lines.append(f"- **Value score:** {score:.2f}")
        lines.append("")
    return "\n".join(lines).strip()


_SUMMARIZE_BODY_TRUNCATE = 1200


@beartype
def _build_summarize_prompt_content(
    items: list[BacklogItem],
    filter_context: dict[str, Any],
    include_value_score: bool = False,
    comments_by_item_id: dict[str, list[str]] | None = None,
    include_comments: bool = False,
) -> str:
    """
    Build prompt content for standup summary: instruction + filter context + per-item data.

    When include_comments is True, includes body (description) and annotations (comments) per item
    so an LLM can produce a meaningful summary. When False, only metadata (id, title, status,
    assignees, last updated) is included to avoid leaking sensitive or large context.
    For use with slash command (e.g. specfact.daily) or copy-paste to Copilot.
    """
    lines: list[str] = []
    lines.append("--- BEGIN STANDUP PROMPT ---")
    lines.append("Generate a concise daily standup summary from the following data.")
    if include_comments:
        lines.append(
            "Include: current focus, blockers, and pending items. Use each item's description and comments for context. Keep it short and actionable."
        )
    else:
        lines.append("Include: current focus and pending items from the metadata below. Keep it short and actionable.")
    lines.append("")
    lines.append("## Filter context")
    lines.append(f"- Adapter: {filter_context.get('adapter', '—')}")
    lines.append(f"- State: {filter_context.get('state', '—')}")
    lines.append(f"- Sprint: {filter_context.get('sprint', '—')}")
    lines.append(f"- Assignee: {filter_context.get('assignee', '—')}")
    lines.append(f"- Limit: {filter_context.get('limit', '—')}")
    lines.append("")
    data_header = "Standup data (with description and comments)" if include_comments else "Standup data (metadata only)"
    lines.append(f"## {data_header}")
    lines.append("")
    comments_map = comments_by_item_id or {}
    for item in items:
        lines.append(f"## {item.id} - {item.title}")
        lines.append("")
        lines.append(f"- **Status:** {item.state}")
        assignee_str = ", ".join(item.assignees) if item.assignees else "—"
        lines.append(f"- **Assignees:** {assignee_str}")
        updated = (
            item.updated_at.strftime("%Y-%m-%d %H:%M") if hasattr(item.updated_at, "strftime") else str(item.updated_at)
        )
        lines.append(f"- **Last updated:** {updated}")
        if include_comments:
            body = (item.body_markdown or "").strip()
            if body:
                snippet = body[:_SUMMARIZE_BODY_TRUNCATE]
                if len(body) > _SUMMARIZE_BODY_TRUNCATE:
                    snippet += "\n..."
                lines.append("- **Description:**")
                lines.append(snippet)
                lines.append("")
            yesterday, today, blockers = _parse_standup_from_body(item.body_markdown or "")
            if yesterday or today:
                lines.append(f"- **Progress:** Yesterday: {yesterday or '—'}; Today: {today or '—'}")
            if blockers:
                lines.append(f"- **Blockers:** {blockers}")
            item_comments = comments_map.get(item.id, [])
            if item_comments:
                lines.append("- **Comments (annotations):**")
                for c in item_comments:
                    lines.append(f"  - {c}")
        if item.story_points is not None:
            lines.append(f"- **Story points:** {item.story_points}")
        if item.priority is not None:
            lines.append(f"- **Priority:** {item.priority}")
        if include_value_score:
            score = _compute_value_score(item)
            if score is not None:
                lines.append(f"- **Value score:** {score:.2f}")
        lines.append("")
    lines.append("--- END STANDUP PROMPT ---")
    return "\n".join(lines).strip()


@beartype
def _build_refine_export_content(
    adapter: str,
    items: list[BacklogItem],
    comments_by_item_id: dict[str, list[str]] | None = None,
    template_guidance_by_item_id: dict[str, dict[str, Any]] | None = None,
) -> str:
    """Build markdown export content for `backlog refine --export-to-tmp`."""
    export_content = "# SpecFact Backlog Refinement Export\n\n"
    export_content += f"**Export Date**: {datetime.now().isoformat()}\n"
    export_content += f"**Adapter**: {adapter}\n"
    export_content += f"**Items**: {len(items)}\n\n"
    export_content += "## Copilot Instructions\n\n"
    export_content += (
        "Use each `## Item N:` section below as refinement input. Preserve scope/intent and return improved markdown "
        "per item.\n\n"
    )
    export_content += (
        "For import readiness: the refined artifact (`--import-from-tmp`) must not include this instruction block; "
        "it should contain only the `## Item N:` sections and refined fields.\n\n"
    )
    export_content += "**Refinement Rules (same as interactive mode):**\n"
    export_content += "1. Preserve all original requirements, scope, and technical details\n"
    export_content += "2. Do NOT add new features or change the scope\n"
    export_content += "3. Transform content to match the target template structure\n"
    export_content += "4. If required information is missing, use a Markdown checkbox: `- [ ] describe what's needed`\n"
    export_content += (
        "5. If information is conflicting or ambiguous, add a `[NOTES]` section at the end explaining ambiguity\n"
    )
    export_content += "6. Use markdown headings for sections (`## Section Name`)\n"
    export_content += "7. Include story points, business value, priority, and work item type when available\n"
    export_content += "8. For high-complexity stories, suggest splitting when appropriate\n"
    export_content += "9. Follow provider-aware formatting guidance listed per item\n\n"
    export_content += "---\n\n"
    comments_map = comments_by_item_id or {}
    template_map = template_guidance_by_item_id or {}

    for idx, item in enumerate(items, 1):
        export_content += f"## Item {idx}: {item.title}\n\n"
        export_content += f"**ID**: {item.id}\n"
        export_content += f"**URL**: {item.url}\n"
        if item.canonical_url:
            export_content += f"**Canonical URL**: {item.canonical_url}\n"
        export_content += f"**State**: {item.state}\n"
        export_content += f"**Provider**: {item.provider}\n"
        item_template = template_map.get(item.id, {})
        if item_template:
            export_content += f"\n**Target Template**: {item_template.get('name', 'N/A')}\n"
            export_content += f"**Template ID**: {item_template.get('template_id', 'N/A')}\n"
            template_desc = str(item_template.get("description", "")).strip()
            if template_desc:
                export_content += f"**Template Description**: {template_desc}\n"
            required_sections = item_template.get("required_sections", [])
            export_content += "\n**Required Sections**:\n"
            if isinstance(required_sections, list) and required_sections:
                for section in required_sections:
                    export_content += f"- {section}\n"
            else:
                export_content += "- None\n"
            optional_sections = item_template.get("optional_sections", [])
            export_content += "\n**Optional Sections**:\n"
            if isinstance(optional_sections, list) and optional_sections:
                for section in optional_sections:
                    export_content += f"- {section}\n"
            else:
                export_content += "- None\n"
            export_content += "\n**Provider-aware formatting**:\n"
            export_content += "- GitHub: Use markdown headings in body (`## Section Name`).\n"
            export_content += (
                "- ADO: Use markdown headings in body; adapter maps to provider fields during writeback.\n"
            )

        if item.story_points is not None or item.business_value is not None or item.priority is not None:
            export_content += "\n**Metrics**:\n"
            if item.story_points is not None:
                export_content += f"- Story Points: {item.story_points}\n"
            if item.business_value is not None:
                export_content += f"- Business Value: {item.business_value}\n"
            if item.priority is not None:
                export_content += f"- Priority: {item.priority} (1=highest)\n"
            if item.value_points is not None:
                export_content += f"- Value Points (SAFe): {item.value_points}\n"
            if item.work_item_type:
                export_content += f"- Work Item Type: {item.work_item_type}\n"

        if item.acceptance_criteria:
            export_content += f"\n**Acceptance Criteria**:\n{item.acceptance_criteria}\n"

        item_comments = comments_map.get(item.id, [])
        if item_comments:
            export_content += "\n**Comments (annotations):**\n"
            for comment in item_comments:
                export_content += f"- {comment}\n"

        export_content += f"\n**Body**:\n```markdown\n{item.body_markdown}\n```\n"
        export_content += "\n---\n\n"
    return export_content


@beartype
def _resolve_target_template_for_refine_item(
    item: BacklogItem,
    *,
    detector: TemplateDetector,
    registry: TemplateRegistry,
    template_id: str | None,
    normalized_adapter: str | None,
    normalized_framework: str | None,
    normalized_persona: str | None,
) -> BacklogTemplate | None:
    """Resolve target template for an item using the same precedence as refine flows."""
    if template_id:
        direct = registry.get_template(template_id)
        if direct is not None:
            return direct
    detection_result = detector.detect_template(
        item,
        provider=normalized_adapter,
        framework=normalized_framework,
        persona=normalized_persona,
    )
    if detection_result.template_id:
        detected = registry.get_template(detection_result.template_id)
        if detected is not None:
            return detected
    resolved = registry.resolve_template(
        provider=normalized_adapter,
        framework=normalized_framework,
        persona=normalized_persona,
    )
    if resolved is not None:
        return resolved
    templates = registry.list_templates(scope="corporate")
    return templates[0] if templates else None


def _run_interactive_daily(
    items: list[BacklogItem],
    standup_config: dict[str, Any],
    suggest_next: bool,
    adapter: str,
    repo_owner: str | None,
    repo_name: str | None,
    github_token: str | None,
    ado_org: str | None,
    ado_project: str | None,
    ado_token: str | None,
    first_comments: int | None = None,
    last_comments: int | None = None,
) -> None:
    """
    Run interactive step-by-step review: questionary selection, detail view, next/previous/back/exit.
    """
    try:
        import questionary  # type: ignore[reportMissingImports]
    except ImportError:
        console.print(
            "[red]Interactive mode requires the 'questionary' package. Install with: pip install questionary[/red]"
        )
        raise typer.Exit(1) from None

    adapter_kwargs = _build_adapter_kwargs(
        adapter,
        repo_owner=repo_owner,
        repo_name=repo_name,
        github_token=github_token,
        ado_org=ado_org,
        ado_project=ado_project,
        ado_token=ado_token,
    )
    registry = AdapterRegistry()
    adapter_instance = registry.get_adapter(adapter, **adapter_kwargs)
    get_comments_fn = getattr(adapter_instance, "get_comments", lambda _: [])

    n = len(items)
    choices = [
        f"{item.id} - {item.title[:50]}{'...' if len(item.title) > 50 else ''} [{item.state}] ({', '.join(item.assignees) or '—'})"
        for item in items
    ]
    choices.append("Exit")

    while True:
        selected = questionary.select("Select a story to review (or Exit)", choices=choices).ask()
        if selected is None or selected == "Exit":
            return
        try:
            idx = choices.index(selected)
        except ValueError:
            return
        if idx >= n:
            return

        current_idx = idx
        while True:
            item = items[current_idx]
            comments: list[str] = []
            total_comments = 0
            if callable(get_comments_fn):
                with contextlib.suppress(Exception):
                    raw = get_comments_fn(item)
                    raw_comments = list(raw) if isinstance(raw, list) else []
                    total_comments = len(raw_comments)
                    comments = _apply_comment_window(
                        raw_comments,
                        first_comments=first_comments,
                        last_comments=last_comments,
                    )
            explicit_comment_window = first_comments is not None or last_comments is not None
            detail = _format_daily_item_detail(
                item,
                comments,
                show_all_provided_comments=explicit_comment_window,
                total_comments=total_comments,
            )
            console.print(Panel(detail, title=f"Story: {item.id}", border_style="cyan"))
            console.print("\n[bold]Comments:[/bold]")
            for panel in _build_daily_interactive_comment_panels(
                comments,
                show_all_provided_comments=explicit_comment_window,
                total_comments=total_comments,
            ):
                console.print(panel)

            if suggest_next and n > 1:
                pending = [i for i in items if not i.assignees or i.story_points is not None]
                if pending:
                    best: BacklogItem | None = None
                    best_score: float = -1.0
                    for i in pending:
                        s = _compute_value_score(i)
                        if s is not None and s > best_score:
                            best_score = s
                            best = i
                    if best is not None:
                        console.print(
                            f"[dim]Suggested next (value score {best_score:.2f}): {best.id} - {best.title}[/dim]"
                        )

            can_post_comment = isinstance(adapter_instance, BacklogAdapter) and _post_standup_comment_supported(
                adapter_instance, item
            )
            nav_choices = _build_daily_navigation_choices(can_post_comment=can_post_comment)
            nav = questionary.select("Navigation", choices=nav_choices).ask()
            if nav is None or nav == "Exit":
                return
            if nav == "Post standup update":
                y = questionary.text("Yesterday (optional):").ask()
                t = questionary.text("Today (optional):").ask()
                b = questionary.text("Blockers (optional):").ask()
                body = _build_interactive_post_body(y, t, b)
                if body is None:
                    console.print("[yellow]No standup text provided; nothing posted.[/yellow]")
                    continue
                if isinstance(adapter_instance, BacklogAdapter) and _post_standup_to_item(adapter_instance, item, body):
                    console.print(f"[green]✓ Standup comment posted to story {item.id}: {item.url}[/green]")
                else:
                    console.print("[red]Failed to post standup comment for selected story.[/red]")
                continue
            if nav == "Back to list":
                break
            if nav == "Next story":
                current_idx = (current_idx + 1) % n
            elif nav == "Previous story":
                current_idx = (current_idx - 1) % n


def _extract_openspec_change_id(body: str) -> str | None:
    """
    Extract OpenSpec change proposal ID from issue body.

    Looks for patterns like:
    - *OpenSpec Change Proposal: `id`*
    - OpenSpec Change Proposal: `id`
    - OpenSpec.*proposal: `id`

    Args:
        body: Issue body text

    Returns:
        Change proposal ID if found, None otherwise
    """
    import re

    openspec_patterns = [
        r"OpenSpec Change Proposal[:\s]+`?([a-z0-9-]+)`?",
        r"\*OpenSpec Change Proposal:\s*`([a-z0-9-]+)`",
        r"OpenSpec.*proposal[:\s]+`?([a-z0-9-]+)`?",
    ]
    for pattern in openspec_patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def _infer_github_repo_from_cwd() -> tuple[str | None, str | None]:
    """
    Infer repo_owner and repo_name from git remote origin when run inside a GitHub clone.
    Returns (owner, repo) or (None, None) if not a GitHub remote or git unavailable.
    """
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode != 0 or not result.stdout or not result.stdout.strip():
            return (None, None)
        url = result.stdout.strip()
        owner, repo = None, None
        if url.startswith("git@"):
            part = url.split(":", 1)[-1].strip()
            if part.endswith(".git"):
                part = part[:-4]
            segments = part.split("/")
            if len(segments) >= 2 and "github" in url.lower():
                owner, repo = segments[-2], segments[-1]
        else:
            parsed = urlparse(url)
            if parsed.hostname and "github" in parsed.hostname.lower() and parsed.path:
                path = parsed.path.strip("/")
                if path.endswith(".git"):
                    path = path[:-4]
                segments = path.split("/")
                if len(segments) >= 2:
                    owner, repo = segments[-2], segments[-1]
        return (owner or None, repo or None)
    except Exception:
        return (None, None)


def _infer_ado_context_from_cwd() -> tuple[str | None, str | None]:
    """
    Infer org and project from git remote origin when run inside an Azure DevOps clone.
    Returns (org, project) or (None, None) if not an ADO remote or git unavailable.
    Supports:
    - HTTPS: https://dev.azure.com/org/project/_git/repo
    - SSH (keys): git@ssh.dev.azure.com:v3/<org>/<project>/<repo>
    - SSH (other): <user>@dev.azure.com:v3/<org>/<project>/<repo> (no ssh. subdomain)
    """
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode != 0 or not result.stdout or not result.stdout.strip():
            return (None, None)
        url = result.stdout.strip()
        org, project = None, None
        if "dev.azure.com" not in url.lower():
            return (None, None)
        if ":" in url and "v3/" in url:
            idx = url.find("v3/")
            if idx != -1:
                part = url[idx + 3 :].strip()
                segments = part.split("/")
                if len(segments) >= 2:
                    org, project = segments[0], segments[1]
        else:
            parsed = urlparse(url)
            if parsed.path:
                path = parsed.path.strip("/")
                segments = path.split("/")
                if len(segments) >= 2:
                    org, project = segments[0], segments[1]
        return (org or None, project or None)
    except Exception:
        return (None, None)


def _build_adapter_kwargs(
    adapter: str,
    repo_owner: str | None = None,
    repo_name: str | None = None,
    github_token: str | None = None,
    ado_org: str | None = None,
    ado_project: str | None = None,
    ado_team: str | None = None,
    ado_token: str | None = None,
) -> dict[str, Any]:
    """
    Build adapter kwargs from CLI args, then env, then .specfact/backlog.yaml.
    Resolution order: explicit arg > env (SPECFACT_GITHUB_REPO_OWNER, etc.) > config.
    Tokens are never read from config; only from explicit args (env handled by caller).
    """
    cfg = _load_backlog_config()
    kwargs: dict[str, Any] = {}
    if adapter.lower() == "github":
        owner = (
            repo_owner or os.environ.get("SPECFACT_GITHUB_REPO_OWNER") or (cfg.get("github") or {}).get("repo_owner")
        )
        name = repo_name or os.environ.get("SPECFACT_GITHUB_REPO_NAME") or (cfg.get("github") or {}).get("repo_name")
        if not owner or not name:
            inferred_owner, inferred_name = _infer_github_repo_from_cwd()
            if inferred_owner and inferred_name:
                owner = owner or inferred_owner
                name = name or inferred_name
        if owner:
            kwargs["repo_owner"] = owner
        if name:
            kwargs["repo_name"] = name
        if github_token:
            kwargs["api_token"] = github_token
    elif adapter.lower() == "ado":
        org = ado_org or os.environ.get("SPECFACT_ADO_ORG") or (cfg.get("ado") or {}).get("org")
        project = ado_project or os.environ.get("SPECFACT_ADO_PROJECT") or (cfg.get("ado") or {}).get("project")
        team = ado_team or os.environ.get("SPECFACT_ADO_TEAM") or (cfg.get("ado") or {}).get("team")
        if not org or not project:
            inferred_org, inferred_project = _infer_ado_context_from_cwd()
            if inferred_org and inferred_project:
                org = org or inferred_org
                project = project or inferred_project
        if org:
            kwargs["org"] = org
        if project:
            kwargs["project"] = project
        if team:
            kwargs["team"] = team
        if ado_token:
            kwargs["api_token"] = ado_token
    return kwargs


def _extract_body_from_block(block: str) -> str:
    """
    Extract **Body** content from a refined export block, handling nested fenced code.

    The body is wrapped in ```markdown ... ```. If the body itself contains fenced
    code blocks (e.g. ```python ... ```), the closing fence is matched by tracking
    depth: a line that is exactly ``` closes the current fence (body or inner).
    """
    start_marker = "**Body**:"
    fence_open = "```markdown"
    if start_marker not in block or fence_open not in block:
        return ""
    idx = block.find(start_marker)
    rest = block[idx + len(start_marker) :].lstrip()
    if not rest.startswith("```"):
        return ""
    if not rest.startswith(fence_open + "\n") and not rest.startswith(fence_open + "\r\n"):
        return ""
    after_open = rest[len(fence_open) :].lstrip("\n\r")
    if not after_open:
        return ""
    lines = after_open.split("\n")
    body_lines: list[str] = []
    depth = 1
    for line in lines:
        stripped = line.rstrip()
        if stripped == "```":
            if depth == 1:
                break
            depth -= 1
            body_lines.append(line)
        elif stripped.startswith("```") and stripped != "```":
            depth += 1
            body_lines.append(line)
        else:
            body_lines.append(line)
    return "\n".join(body_lines).strip()


def _parse_refined_export_markdown(content: str) -> dict[str, dict[str, Any]]:
    """
    Parse refined export markdown (same format as --export-to-tmp) into id -> fields.

    Splits by ## Item blocks, extracts **ID**, **Body** (from ```markdown ... ```),
    **Acceptance Criteria**, and optionally title and **Metrics** (story_points,
    business_value, priority). Body extraction is fence-aware so bodies containing
    nested code blocks are parsed correctly. Returns a dict mapping item id to
    parsed fields (body_markdown, acceptance_criteria, title?, story_points?,
    business_value?, priority?).
    """
    result: dict[str, dict[str, Any]] = {}
    blocks = re.split(r"\n## Item \d+:", content)
    for block in blocks:
        block = block.strip()
        if not block or block.startswith("# SpecFact") or "**ID**:" not in block:
            continue
        id_match = re.search(r"\*\*ID\*\*:\s*(.+?)(?:\n|$)", block)
        if not id_match:
            continue
        item_id = id_match.group(1).strip()
        fields: dict[str, Any] = {}

        fields["body_markdown"] = _extract_body_from_block(block)

        ac_match = re.search(r"\*\*Acceptance Criteria\*\*:\s*\n(.*?)(?=\n\*\*|\n---|\Z)", block, re.DOTALL)
        if ac_match:
            fields["acceptance_criteria"] = ac_match.group(1).strip() or None
        else:
            fields["acceptance_criteria"] = None

        first_line = block.split("\n")[0].strip() if block else ""
        if first_line and not first_line.startswith("**"):
            fields["title"] = first_line

        if "Story Points:" in block:
            sp_match = re.search(r"Story Points:\s*(\d+)", block)
            if sp_match:
                fields["story_points"] = int(sp_match.group(1))
        if "Business Value:" in block:
            bv_match = re.search(r"Business Value:\s*(\d+)", block)
            if bv_match:
                fields["business_value"] = int(bv_match.group(1))
        if "Priority:" in block:
            pri_match = re.search(r"Priority:\s*(\d+)", block)
            if pri_match:
                fields["priority"] = int(pri_match.group(1))

        result[item_id] = fields
    return result


@beartype
@require(lambda content: isinstance(content, str), "Refinement output must be a string")
@ensure(lambda result: isinstance(result, dict), "Must return a dict")
def _parse_refinement_output_fields(content: str) -> dict[str, Any]:
    """
    Parse refinement output into canonical fields for provider-safe writeback.

    Supports both:
    - Markdown heading style (`## Acceptance Criteria`, `## Story Points`, ...)
    - Label style (`Acceptance Criteria:`, `Story Points:`, ...)
    """
    normalized = content.replace("\r\n", "\n").strip()
    if not normalized:
        return {}

    parsed: dict[str, Any] = {}

    # First parse markdown-heading style using existing GitHub field semantics.
    from specfact_cli.backlog.mappers.github_mapper import GitHubFieldMapper

    heading_mapper = GitHubFieldMapper()
    heading_fields = heading_mapper.extract_fields({"body": normalized, "labels": []})

    description = (heading_fields.get("description") or "").strip()
    if description:
        parsed["description"] = description

    acceptance = heading_fields.get("acceptance_criteria")
    if isinstance(acceptance, str) and acceptance.strip():
        parsed["acceptance_criteria"] = acceptance.strip()

    for key in ("story_points", "business_value", "priority"):
        value = heading_fields.get(key)
        if isinstance(value, int):
            parsed[key] = value

    # Then parse label-style blocks; explicit labels override heading heuristics.
    label_aliases = {
        "description": "description",
        "acceptance criteria": "acceptance_criteria",
        "story points": "story_points",
        "business value": "business_value",
        "priority": "priority",
        "work item type": "work_item_type",
        "notes": "notes",
        "dependencies": "dependencies",
        "area path": "area_path",
        "iteration path": "iteration_path",
        "provider": "provider",
    }
    label_pattern = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*)?([A-Za-z][A-Za-z0-9 ()/_-]*?)(?:\*\*)?\s*:\s*(.*)\s*$")
    blocks: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    def _flush_current() -> None:
        nonlocal current_key, current_lines
        if current_key is None:
            return
        value = "\n".join(current_lines).strip()
        blocks[current_key] = value
        current_key = None
        current_lines = []

    for line in normalized.splitlines():
        match = label_pattern.match(line)
        if match:
            candidate = re.sub(r"\s+", " ", match.group(1).strip().lower())
            canonical = label_aliases.get(candidate)
            if canonical:
                _flush_current()
                current_key = canonical
                first_value = (match.group(2) or "").strip()
                current_lines = [first_value] if first_value else []
                continue
        if current_key is not None:
            current_lines.append(line.rstrip())
    _flush_current()

    if blocks.get("description"):
        parsed["description"] = blocks["description"]
    if blocks.get("acceptance_criteria"):
        parsed["acceptance_criteria"] = blocks["acceptance_criteria"]
    if blocks.get("work_item_type"):
        parsed["work_item_type"] = blocks["work_item_type"]

    def _parse_int(key: str) -> int | None:
        raw = blocks.get(key)
        if not raw:
            return None
        match = re.search(r"\d+", raw)
        if not match:
            return None
        return int(match.group(0))

    story_points = _parse_int("story_points")
    if story_points is not None:
        parsed["story_points"] = story_points
    business_value = _parse_int("business_value")
    if business_value is not None:
        parsed["business_value"] = business_value
    priority = _parse_int("priority")
    if priority is not None:
        parsed["priority"] = priority

    # Build a clean writeback body (description + narrative sections only).
    body_parts: list[str] = []
    cleaned_description = (parsed.get("description") or "").strip()
    if cleaned_description:
        body_parts.append(cleaned_description)
    for section_key, title in (("notes", "Notes"), ("dependencies", "Dependencies")):
        section_value = (blocks.get(section_key) or "").strip()
        if section_value:
            body_parts.append(f"## {title}\n\n{section_value}")

    cleaned_body = "\n\n".join(part for part in body_parts if part.strip()).strip()
    if cleaned_body:
        parsed["body_markdown"] = cleaned_body
    elif cleaned_description:
        parsed["body_markdown"] = cleaned_description
    else:
        parsed["body_markdown"] = normalized

    return parsed


@beartype
def _item_needs_refinement(
    item: BacklogItem,
    detector: TemplateDetector,
    registry: TemplateRegistry,
    template_id: str | None,
    normalized_adapter: str | None,
    normalized_framework: str | None,
    normalized_persona: str | None,
) -> bool:
    """
    Return True if the item needs refinement (should be processed); False if already refined (skip).

    Mirrors the "already refined" skip logic used in the refine loop: checkboxes + all required
    sections, or high confidence with no missing fields.
    """
    detection_result = detector.detect_template(
        item,
        provider=normalized_adapter,
        framework=normalized_framework,
        persona=normalized_persona,
    )
    if detection_result.template_id:
        target = registry.get_template(detection_result.template_id) if detection_result.template_id else None
        if target and target.required_sections:
            has_checkboxes = bool(
                re.search(r"^[\s]*- \[[ x]\]", item.body_markdown or "", re.MULTILINE | re.IGNORECASE)
            )
            all_present = all(
                bool(re.search(rf"^#+\s+{re.escape(s)}\s*$", item.body_markdown or "", re.MULTILINE | re.IGNORECASE))
                for s in target.required_sections
            )
            if has_checkboxes and all_present and not detection_result.missing_fields:
                return False
    already_refined = template_id is None and detection_result.confidence >= 0.8 and not detection_result.missing_fields
    return not already_refined


def _fetch_backlog_items(
    adapter_name: str,
    search_query: str | None = None,
    labels: list[str] | None = None,
    state: str | None = None,
    assignee: str | None = None,
    iteration: str | None = None,
    sprint: str | None = None,
    release: str | None = None,
    limit: int | None = None,
    repo_owner: str | None = None,
    repo_name: str | None = None,
    github_token: str | None = None,
    ado_org: str | None = None,
    ado_project: str | None = None,
    ado_team: str | None = None,
    ado_token: str | None = None,
) -> list[BacklogItem]:
    """
    Fetch backlog items using the specified adapter with filtering support.

    Args:
        adapter_name: Adapter name (github, ado, etc.)
        search_query: Optional search query to filter items (provider-specific syntax)
        labels: Filter by labels/tags (post-fetch filtering)
        state: Filter by state (post-fetch filtering)
        assignee: Filter by assignee (post-fetch filtering)
        iteration: Filter by iteration path (post-fetch filtering)
        sprint: Filter by sprint (post-fetch filtering)
        release: Filter by release (post-fetch filtering)
        limit: Maximum number of items to fetch

    Returns:
        List of BacklogItem instances (filtered)
    """
    from specfact_cli.backlog.adapters.base import BacklogAdapter

    registry = AdapterRegistry()

    # Build adapter kwargs based on adapter type
    adapter_kwargs = _build_adapter_kwargs(
        adapter_name,
        repo_owner=repo_owner,
        repo_name=repo_name,
        github_token=github_token,
        ado_org=ado_org,
        ado_project=ado_project,
        ado_team=ado_team,
        ado_token=ado_token,
    )

    if adapter_name.lower() == "github" and (
        not adapter_kwargs.get("repo_owner") or not adapter_kwargs.get("repo_name")
    ):
        console.print("[red]repo_owner and repo_name required for GitHub.[/red]")
        console.print(
            "Set via: [cyan]--repo-owner[/cyan]/[cyan]--repo-name[/cyan], "
            "env [cyan]SPECFACT_GITHUB_REPO_OWNER[/cyan]/[cyan]SPECFACT_GITHUB_REPO_NAME[/cyan], "
            "or [cyan].specfact/backlog.yaml[/cyan] (see docs/guides/devops-adapter-integration.md). "
            "When run from a GitHub clone, org/repo are auto-detected from git remote."
        )
        raise typer.Exit(1)
    if adapter_name.lower() == "ado" and (not adapter_kwargs.get("org") or not adapter_kwargs.get("project")):
        console.print("[red]ado_org and ado_project required for Azure DevOps.[/red]")
        console.print(
            "Set via: [cyan]--ado-org[/cyan]/[cyan]--ado-project[/cyan], "
            "env [cyan]SPECFACT_ADO_ORG[/cyan]/[cyan]SPECFACT_ADO_PROJECT[/cyan], "
            "or [cyan].specfact/backlog.yaml[/cyan]. "
            "When run from an ADO clone, org/project are auto-detected from git remote."
        )
        raise typer.Exit(1)

    adapter = registry.get_adapter(adapter_name, **adapter_kwargs)

    # Check if adapter implements BacklogAdapter interface
    if not isinstance(adapter, BacklogAdapter):
        msg = f"Adapter {adapter_name} does not implement BacklogAdapter interface"
        raise NotImplementedError(msg)

    # Create BacklogFilters from parameters
    filters = BacklogFilters(
        assignee=assignee,
        state=state,
        labels=labels,
        search=search_query,
        iteration=iteration,
        sprint=sprint,
        release=release,
        limit=limit,
    )

    # Fetch items using the adapter
    items = adapter.fetch_backlog_items(filters)

    # Apply limit deterministically (slice after filtering)
    if limit is not None and len(items) > limit:
        items = items[:limit]

    return items


@beartype
@require(lambda item: isinstance(item, BacklogItem), "Item must be BacklogItem")
@ensure(lambda result: isinstance(result, list), "Must return list")
def _build_refine_update_fields(item: BacklogItem) -> list[str]:
    """Build update field list for refine writeback based on populated canonical fields."""
    update_fields_list = ["title", "body_markdown"]
    if item.acceptance_criteria:
        update_fields_list.append("acceptance_criteria")
    if item.story_points is not None:
        update_fields_list.append("story_points")
    if item.business_value is not None:
        update_fields_list.append("business_value")
    if item.priority is not None:
        update_fields_list.append("priority")
    return update_fields_list


@beartype
def _maybe_add_refine_openspec_comment(
    adapter_instance: BacklogAdapter,
    updated_item: BacklogItem,
    item: BacklogItem,
    openspec_comment: bool,
) -> None:
    """Optionally add OpenSpec reference comment after successful writeback."""
    if not openspec_comment:
        return

    original_body = item.body_markdown or ""
    openspec_change_id = _extract_openspec_change_id(original_body)
    change_id = openspec_change_id or f"backlog-refine-{item.id}"
    comment_text = (
        f"## OpenSpec Change Proposal Reference\n\n"
        f"This backlog item was refined using SpecFact CLI template-driven refinement.\n\n"
        f"- **Change ID**: `{change_id}`\n"
        f"- **Template**: `{item.detected_template or 'auto-detected'}`\n"
        f"- **Confidence**: `{item.template_confidence or 0.0:.2f}`\n"
        f"- **Refined**: {item.refinement_timestamp or 'N/A'}\n\n"
        f"*Note: Original body preserved. "
        f"This comment provides OpenSpec reference for cross-sync.*"
    )
    if adapter_instance.add_comment(updated_item, comment_text):
        console.print("[green]✓ Added OpenSpec reference comment[/green]")
    else:
        console.print("[yellow]⚠ Failed to add comment (adapter may not support comments)[/yellow]")


@beartype
def _write_refined_backlog_item(
    adapter_registry: AdapterRegistry,
    adapter: str,
    item: BacklogItem,
    repo_owner: str | None,
    repo_name: str | None,
    github_token: str | None,
    ado_org: str | None,
    ado_project: str | None,
    ado_token: str | None,
    openspec_comment: bool,
) -> bool:
    """Write a refined item back to adapter and optionally add OpenSpec comment."""
    writeback_kwargs = _build_adapter_kwargs(
        adapter,
        repo_owner=repo_owner,
        repo_name=repo_name,
        github_token=github_token,
        ado_org=ado_org,
        ado_project=ado_project,
        ado_token=ado_token,
    )

    adapter_instance = adapter_registry.get_adapter(adapter, **writeback_kwargs)
    if not isinstance(adapter_instance, BacklogAdapter):
        console.print("[yellow]⚠ Adapter does not support backlog updates[/yellow]")
        return False

    update_fields_list = _build_refine_update_fields(item)
    updated_item = adapter_instance.update_backlog_item(item, update_fields=update_fields_list)
    console.print(f"[green]✓ Updated backlog item: {updated_item.url}[/green]")
    _maybe_add_refine_openspec_comment(adapter_instance, updated_item, item, openspec_comment)
    return True


@beartype
@ensure(lambda result: isinstance(result, str), "Must return string")
def _read_refined_content_from_stdin() -> str:
    """Read multiline refined content with sentinel commands from stdin."""
    refined_content_lines: list[str] = []
    console.print("[bold]Paste refined content below (type 'END' on a new line when done):[/bold]")
    console.print("[dim]Commands: :skip (skip this item), :quit or :abort (cancel session)[/dim]")

    while True:
        try:
            line = input()
            line_upper = line.strip().upper()
            if line_upper == "END":
                break
            if line_upper in (":SKIP", ":QUIT", ":ABORT"):
                return line_upper
            refined_content_lines.append(line)
        except EOFError:
            break
    return "\n".join(refined_content_lines).strip()


@beartype
@app.command()
@require(
    lambda adapter: isinstance(adapter, str) and len(adapter) > 0,
    "Adapter must be non-empty string",
)
def daily(
    adapter: str = typer.Argument(..., help="Backlog adapter name (github, ado, etc.)"),
    assignee: str | None = typer.Option(
        None,
        "--assignee",
        help="Filter by assignee (e.g. 'me' or username). Only matching items are listed.",
    ),
    search: str | None = typer.Option(
        None, "--search", "-s", help="Search query to filter backlog items (provider-specific syntax)"
    ),
    state: str | None = typer.Option(None, "--state", help="Filter by state (e.g. open, closed, Active)"),
    labels: list[str] | None = typer.Option(None, "--labels", "--tags", help="Filter by labels/tags"),
    release: str | None = typer.Option(None, "--release", help="Filter by release identifier"),
    issue_id: str | None = typer.Option(
        None,
        "--id",
        help="Show only this backlog item (issue or work item ID). Other items are ignored.",
    ),
    limit: int | None = typer.Option(None, "--limit", help="Maximum number of items to show"),
    first_issues: int | None = typer.Option(
        None,
        "--first-issues",
        min=1,
        help="Show only the first N backlog items after filters (lowest numeric issue/work-item IDs).",
    ),
    last_issues: int | None = typer.Option(
        None,
        "--last-issues",
        min=1,
        help="Show only the last N backlog items after filters (highest numeric issue/work-item IDs).",
    ),
    iteration: str | None = typer.Option(
        None,
        "--iteration",
        help="Filter by iteration (e.g. 'current' or literal path). ADO: full path; adapter must support.",
    ),
    sprint: str | None = typer.Option(
        None,
        "--sprint",
        help="Filter by sprint (e.g. 'current' or name). Adapter must support iteration/sprint.",
    ),
    show_unassigned: bool = typer.Option(
        True,
        "--show-unassigned/--no-show-unassigned",
        help="Show unassigned/pending items in a second table (default: true).",
    ),
    unassigned_only: bool = typer.Option(
        False,
        "--unassigned-only",
        help="Show only unassigned items (single table).",
    ),
    blockers_first: bool = typer.Option(
        False,
        "--blockers-first",
        help="Sort so items with non-empty blockers appear first.",
    ),
    mode: str = typer.Option(
        "scrum",
        "--mode",
        help="Standup mode defaults: scrum|kanban|safe.",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        help="Step-by-step review: select items with arrow keys and view full detail (refine-like) and comments.",
    ),
    copilot_export: str | None = typer.Option(
        None,
        "--copilot-export",
        help="Write summarized progress per story to a file for Copilot slash-command use during standup.",
    ),
    include_comments: bool = typer.Option(
        False,
        "--comments",
        "--annotations",
        help="Include item comments/annotations in summarize/copilot export (adapter must support get_comments).",
    ),
    first_comments: int | None = typer.Option(
        None,
        "--first-comments",
        min=1,
        help="Include only the first N comments per item (optional; default includes all comments).",
    ),
    last_comments: int | None = typer.Option(
        None,
        "--last-comments",
        min=1,
        help="Include only the last N comments per item (optional; default includes all comments).",
    ),
    summarize: bool = typer.Option(
        False,
        "--summarize",
        help="Output a prompt (instruction + filter context + standup data) for slash command or Copilot to generate a standup summary (prints to stdout).",
    ),
    summarize_to: str | None = typer.Option(
        None,
        "--summarize-to",
        help="Write the summarize prompt to this file (alternative to --summarize stdout).",
    ),
    suggest_next: bool = typer.Option(
        False,
        "--suggest-next",
        help="In interactive mode, show suggested next item by value score (business value / (story points * priority)).",
    ),
    patch: bool = typer.Option(
        False,
        "--patch",
        help="Emit a patch proposal preview for standup notes/missing fields when patch-mode is available (no silent writes).",
    ),
    post: bool = typer.Option(
        False,
        "--post",
        help="Post standup comment to the first item's issue. Requires at least one of --yesterday, --today, --blockers with a value (adapter must support comments).",
    ),
    yesterday: str | None = typer.Option(
        None,
        "--yesterday",
        help='Standup: what was done yesterday (used when posting with --post; pass a value e.g. --yesterday "Worked on X").',
    ),
    today: str | None = typer.Option(
        None,
        "--today",
        help='Standup: what will be done today (used when posting with --post; pass a value e.g. --today "Will do Y").',
    ),
    blockers: str | None = typer.Option(
        None,
        "--blockers",
        help='Standup: blockers (used when posting with --post; pass a value e.g. --blockers "None").',
    ),
    repo_owner: str | None = typer.Option(None, "--repo-owner", help="GitHub repository owner"),
    repo_name: str | None = typer.Option(None, "--repo-name", help="GitHub repository name"),
    github_token: str | None = typer.Option(None, "--github-token", help="GitHub API token"),
    ado_org: str | None = typer.Option(None, "--ado-org", help="Azure DevOps organization"),
    ado_project: str | None = typer.Option(None, "--ado-project", help="Azure DevOps project"),
    ado_team: str | None = typer.Option(
        None, "--ado-team", help="ADO team for current iteration (when --sprint current)"
    ),
    ado_token: str | None = typer.Option(None, "--ado-token", help="Azure DevOps PAT"),
) -> None:
    """
    Show daily standup view: list my/filtered backlog items with status and last activity.

    Optional standup summary lines (yesterday/today/blockers) are shown when present in item body.
    Use --post with --yesterday, --today, --blockers to post a standup comment to the first item's linked issue
    (only when the adapter supports comments, e.g. GitHub).
    Default scope: state=open, limit=20 (overridable via SPECFACT_STANDUP_* env or .specfact/standup.yaml).
    """
    standup_config = _load_standup_config()
    normalized_mode = mode.lower().strip()
    if normalized_mode not in {"scrum", "kanban", "safe"}:
        console.print("[red]Invalid --mode. Use one of: scrum, kanban, safe.[/red]")
        raise typer.Exit(1)
    effective_state, effective_limit, effective_assignee = _resolve_standup_options(
        state, limit, assignee, standup_config
    )
    effective_state = _resolve_daily_mode_state(
        mode=normalized_mode,
        cli_state=state,
        effective_state=effective_state,
    )
    fetch_limit = _resolve_daily_fetch_limit(
        effective_limit,
        first_issues=first_issues,
        last_issues=last_issues,
    )
    display_limit = _resolve_daily_display_limit(
        effective_limit,
        first_issues=first_issues,
        last_issues=last_issues,
    )
    items = _fetch_backlog_items(
        adapter,
        search_query=search,
        state=effective_state,
        assignee=effective_assignee,
        labels=labels,
        release=release,
        limit=fetch_limit,
        iteration=iteration,
        sprint=sprint,
        repo_owner=repo_owner,
        repo_name=repo_name,
        github_token=github_token,
        ado_org=ado_org,
        ado_project=ado_project,
        ado_team=ado_team,
        ado_token=ado_token,
    )
    filtered = _apply_filters(
        items,
        labels=labels,
        state=effective_state,
        assignee=_resolve_post_fetch_assignee_filter(adapter, effective_assignee),
        iteration=iteration,
        sprint=sprint,
        release=release,
    )
    filtered = _apply_issue_id_filter(filtered, issue_id)
    if issue_id is not None and not filtered:
        console.print(
            f"[bold red]✗[/bold red] No backlog item with id {issue_id!r} found. "
            "Check filters and adapter configuration."
        )
        raise typer.Exit(1)
    try:
        filtered = _resolve_daily_issue_window(filtered, first_issues=first_issues, last_issues=last_issues)
    except ValueError as exc:
        console.print(f"[red]{exc}.[/red]")
        raise typer.Exit(1) from exc
    if display_limit is not None and len(filtered) > display_limit:
        filtered = filtered[:display_limit]

    if not filtered:
        console.print("[yellow]No backlog items found.[/yellow]")
        return

    if first_comments is not None and last_comments is not None:
        console.print("[red]Use only one of --first-comments or --last-comments.[/red]")
        raise typer.Exit(1)

    comments_by_item_id: dict[str, list[str]] = {}
    if include_comments and (copilot_export is not None or summarize or summarize_to is not None):
        comments_by_item_id = _collect_comment_annotations(
            adapter,
            filtered,
            repo_owner=repo_owner,
            repo_name=repo_name,
            github_token=github_token,
            ado_org=ado_org,
            ado_project=ado_project,
            ado_token=ado_token,
            first_comments=first_comments,
            last_comments=last_comments,
        )

    if copilot_export is not None:
        include_score = suggest_next or bool(standup_config.get("suggest_next"))
        export_path = Path(copilot_export)
        content = _build_copilot_export_content(
            filtered,
            include_value_score=include_score,
            include_comments=include_comments,
            comments_by_item_id=comments_by_item_id or None,
        )
        export_path.write_text(content, encoding="utf-8")
        console.print(f"[dim]Exported {len(filtered)} item(s) to {export_path}[/dim]")

    if summarize or summarize_to is not None:
        include_score = suggest_next or bool(standup_config.get("suggest_next"))
        filter_ctx: dict[str, Any] = {
            "adapter": adapter,
            "state": effective_state or "—",
            "sprint": sprint or iteration or "—",
            "assignee": effective_assignee or "—",
            "limit": effective_limit,
        }
        content = _build_summarize_prompt_content(
            filtered,
            filter_context=filter_ctx,
            include_value_score=include_score,
            comments_by_item_id=comments_by_item_id or None,
            include_comments=include_comments,
        )
        if summarize_to:
            Path(summarize_to).write_text(content, encoding="utf-8")
            console.print(f"[dim]Summarize prompt written to {summarize_to} ({len(filtered)} item(s))[/dim]")
        else:
            console.print(content)
        return

    if interactive:
        _run_interactive_daily(
            filtered,
            standup_config=standup_config,
            suggest_next=suggest_next,
            adapter=adapter,
            repo_owner=repo_owner,
            repo_name=repo_name,
            github_token=github_token,
            ado_org=ado_org,
            ado_project=ado_project,
            ado_token=ado_token,
            first_comments=first_comments,
            last_comments=last_comments,
        )
        return

    first_item = filtered[0]
    include_priority = bool(standup_config.get("show_priority") or standup_config.get("show_value"))
    rows_unassigned: list[dict[str, Any]] = []
    if unassigned_only:
        _, filtered = _split_assigned_unassigned(filtered)
        if not filtered:
            console.print("[yellow]No unassigned items in scope.[/yellow]")
            return
        rows = _build_standup_rows(filtered, include_priority=include_priority)
        if blockers_first:
            rows = _sort_standup_rows_blockers_first(rows)
    else:
        assigned, unassigned = _split_assigned_unassigned(filtered)
        rows = _build_standup_rows(assigned, include_priority=include_priority)
        if blockers_first:
            rows = _sort_standup_rows_blockers_first(rows)
        if show_unassigned and unassigned:
            rows_unassigned = _build_standup_rows(unassigned, include_priority=include_priority)

    if post:
        y = (yesterday or "").strip()
        t = (today or "").strip()
        b = (blockers or "").strip()
        if not y and not t and not b:
            console.print("[yellow]Use --yesterday, --today, and/or --blockers with values when using --post.[/yellow]")
            console.print('[dim]Example: --yesterday "Worked on X" --today "Will do Y" --blockers "None" --post[/dim]')
            return
        body = _format_standup_comment(y, t, b)
        item = first_item
        registry = AdapterRegistry()
        adapter_kwargs = _build_adapter_kwargs(
            adapter,
            repo_owner=repo_owner,
            repo_name=repo_name,
            github_token=github_token,
            ado_org=ado_org,
            ado_project=ado_project,
            ado_token=ado_token,
        )
        adapter_instance = registry.get_adapter(adapter, **adapter_kwargs)
        if not isinstance(adapter_instance, BacklogAdapter):
            console.print("[red]Adapter does not implement BacklogAdapter.[/red]")
            raise typer.Exit(1)
        if not _post_standup_comment_supported(adapter_instance, item):
            console.print("[yellow]Posting comments is not supported for this adapter.[/yellow]")
            return
        ok = _post_standup_to_item(adapter_instance, item, body)
        if ok:
            console.print(f"[green]✓ Standup comment posted to {item.url}[/green]")
        else:
            console.print("[red]Failed to post standup comment.[/red]")
            raise typer.Exit(1)
        return

    sprint_end = standup_config.get("sprint_end_date") or os.environ.get("SPECFACT_STANDUP_SPRINT_END")
    if sprint_end and (sprint or iteration):
        try:
            from datetime import datetime as dt

            end_date = dt.strptime(str(sprint_end)[:10], "%Y-%m-%d").date()
            console.print(f"[dim]{_format_sprint_end_header(end_date)}[/dim]")
        except (ValueError, TypeError):
            console.print("[dim]Sprint end date could not be parsed; header skipped.[/dim]")

    def _add_standup_rows_to_table(tbl: Table, row_list: list[dict[str, Any]], include_pri: bool) -> None:
        for r in row_list:
            cells: list[Any] = [
                str(r["id"]),
                str(r["title"])[:50],
                str(r["status"]),
                str(r.get("assignees", "—"))[:30],
                r["last_updated"].strftime("%Y-%m-%d %H:%M")
                if hasattr(r["last_updated"], "strftime")
                else str(r["last_updated"]),
                (r.get("yesterday") or "")[:30],
                (r.get("today") or "")[:30],
                (r.get("blockers") or "")[:20],
            ]
            if include_pri and "priority" in r:
                cells.append(str(r["priority"]))
            tbl.add_row(*cells)

    def _make_standup_table(title: str) -> Table:
        table_obj = Table(title=title, show_header=True, header_style="bold cyan")
        table_obj.add_column("ID", style="dim")
        table_obj.add_column("Title")
        table_obj.add_column("Status")
        table_obj.add_column("Assignee", style="dim", max_width=30)
        table_obj.add_column("Last updated")
        table_obj.add_column("Yesterday", style="dim", max_width=30)
        table_obj.add_column("Today", style="dim", max_width=30)
        table_obj.add_column("Blockers", style="dim", max_width=20)
        if include_priority:
            table_obj.add_column("Priority", style="dim")
        return table_obj

    exceptions_rows, normal_rows = _split_exception_rows(rows)
    if exceptions_rows:
        exceptions_table = _make_standup_table("Exceptions")
        _add_standup_rows_to_table(exceptions_table, exceptions_rows, include_priority)
        console.print(exceptions_table)
    if normal_rows:
        normal_table = _make_standup_table("Daily standup")
        _add_standup_rows_to_table(normal_table, normal_rows, include_priority)
        console.print(normal_table)
    if not exceptions_rows and not normal_rows:
        empty_table = _make_standup_table("Daily standup")
        console.print(empty_table)
    if not unassigned_only and show_unassigned and rows_unassigned:
        table_pending = Table(
            title="Pending / open for commitment",
            show_header=True,
            header_style="bold cyan",
        )
        table_pending.add_column("ID", style="dim")
        table_pending.add_column("Title")
        table_pending.add_column("Status")
        table_pending.add_column("Assignee", style="dim", max_width=30)
        table_pending.add_column("Last updated")
        table_pending.add_column("Yesterday", style="dim", max_width=30)
        table_pending.add_column("Today", style="dim", max_width=30)
        table_pending.add_column("Blockers", style="dim", max_width=20)
        if include_priority:
            table_pending.add_column("Priority", style="dim")
        _add_standup_rows_to_table(table_pending, rows_unassigned, include_priority)
        console.print(table_pending)

    if patch:
        if _is_patch_mode_available():
            proposal = _build_daily_patch_proposal(filtered, mode=normalized_mode)
            console.print("\n[bold]Patch proposal preview:[/bold]")
            console.print(Panel(proposal, border_style="yellow"))
            console.print("[dim]No changes applied. Review/apply explicitly via patch workflow.[/dim]")
        else:
            console.print(
                "[dim]Patch proposal requested, but patch-mode is not available yet. "
                "Continuing without patch output.[/dim]"
            )


@beartype
@app.command()
@require(
    lambda adapter: isinstance(adapter, str) and len(adapter) > 0,
    "Adapter must be non-empty string",
)
def refine(
    adapter: str = typer.Argument(..., help="Backlog adapter name (github, ado, etc.)"),
    # Common filters
    labels: list[str] | None = typer.Option(
        None, "--labels", "--tags", help="Filter by labels/tags (can specify multiple)"
    ),
    state: str | None = typer.Option(
        None, "--state", help="Filter by state (case-insensitive, e.g., 'open', 'closed', 'Active', 'New')"
    ),
    assignee: str | None = typer.Option(
        None,
        "--assignee",
        help="Filter by assignee (case-insensitive). GitHub: login or @username. ADO: displayName, uniqueName, or mail",
    ),
    # Iteration/sprint filters
    iteration: str | None = typer.Option(
        None,
        "--iteration",
        help="Filter by iteration path (ADO format: 'Project\\Sprint 1' or 'current' for current iteration). Must be exact full path from ADO.",
    ),
    sprint: str | None = typer.Option(
        None,
        "--sprint",
        help="Filter by sprint (case-insensitive). ADO: use full iteration path (e.g., 'Project\\Sprint 1') to avoid ambiguity. If omitted, defaults to current active iteration.",
    ),
    release: str | None = typer.Option(None, "--release", help="Filter by release identifier"),
    # Template filters
    persona: str | None = typer.Option(
        None, "--persona", help="Filter templates by persona (product-owner, architect, developer)"
    ),
    framework: str | None = typer.Option(
        None, "--framework", help="Filter templates by framework (agile, scrum, safe, kanban)"
    ),
    # Existing options
    search: str | None = typer.Option(
        None, "--search", "-s", help="Search query to filter backlog items (provider-specific syntax)"
    ),
    limit: int | None = typer.Option(
        None,
        "--limit",
        help="Maximum number of items to process in this refinement session. Use to cap batch size and avoid processing too many items at once.",
    ),
    first_issues: int | None = typer.Option(
        None,
        "--first-issues",
        min=1,
        help="Process only the first N backlog items after filters/refinement checks.",
    ),
    last_issues: int | None = typer.Option(
        None,
        "--last-issues",
        min=1,
        help="Process only the last N backlog items after filters/refinement checks.",
    ),
    ignore_refined: bool = typer.Option(
        True,
        "--ignore-refined/--no-ignore-refined",
        help="When set (default), exclude already-refined items from the batch so --limit applies to items that need refinement. Use --no-ignore-refined to process the first N items in order (already-refined skipped in loop).",
    ),
    issue_id: str | None = typer.Option(
        None,
        "--id",
        help="Refine only this backlog item (issue or work item ID). Other items are ignored.",
    ),
    template_id: str | None = typer.Option(None, "--template", "-t", help="Target template ID (default: auto-detect)"),
    auto_accept_high_confidence: bool = typer.Option(
        False, "--auto-accept-high-confidence", help="Auto-accept refinements with confidence >= 0.85"
    ),
    bundle: str | None = typer.Option(None, "--bundle", "-b", help="OpenSpec bundle path to import refined items"),
    auto_bundle: bool = typer.Option(False, "--auto-bundle", help="Auto-import refined items to OpenSpec bundle"),
    openspec_comment: bool = typer.Option(
        False, "--openspec-comment", help="Add OpenSpec change proposal reference as comment (preserves original body)"
    ),
    # Preview/write flags (production safety)
    preview: bool = typer.Option(
        True,
        "--preview/--no-preview",
        help="Preview mode: show what will be written without updating backlog (default: True)",
    ),
    write: bool = typer.Option(
        False, "--write", help="Write mode: explicitly opt-in to update remote backlog (requires --write flag)"
    ),
    # Export/import for copilot processing
    export_to_tmp: bool = typer.Option(
        False,
        "--export-to-tmp",
        help="Export backlog items to temporary file for copilot processing (default: <system-temp>/specfact-backlog-refine-<timestamp>.md)",
    ),
    import_from_tmp: bool = typer.Option(
        False,
        "--import-from-tmp",
        help="Import refined content from temporary file after copilot processing (default: <system-temp>/specfact-backlog-refine-<timestamp>-refined.md)",
    ),
    tmp_file: Path | None = typer.Option(
        None,
        "--tmp-file",
        help="Custom temporary file path (overrides default)",
    ),
    first_comments: int | None = typer.Option(
        None,
        "--first-comments",
        min=1,
        help="For refine preview/write prompt context, include only the first N comments per item.",
    ),
    last_comments: int | None = typer.Option(
        None,
        "--last-comments",
        min=1,
        help="For refine preview/write prompt context, include only the last N comments per item (default preview shows last 2; write prompts default to full comments).",
    ),
    # DoR validation
    check_dor: bool = typer.Option(
        False, "--check-dor", help="Check Definition of Ready (DoR) rules before refinement"
    ),
    # Adapter configuration (GitHub)
    repo_owner: str | None = typer.Option(
        None, "--repo-owner", help="GitHub repository owner (required for GitHub adapter)"
    ),
    repo_name: str | None = typer.Option(
        None, "--repo-name", help="GitHub repository name (required for GitHub adapter)"
    ),
    github_token: str | None = typer.Option(
        None, "--github-token", help="GitHub API token (optional, uses GITHUB_TOKEN env var or gh CLI if not provided)"
    ),
    # Adapter configuration (ADO)
    ado_org: str | None = typer.Option(None, "--ado-org", help="Azure DevOps organization (required for ADO adapter)"),
    ado_project: str | None = typer.Option(
        None, "--ado-project", help="Azure DevOps project (required for ADO adapter)"
    ),
    ado_team: str | None = typer.Option(
        None,
        "--ado-team",
        help="Azure DevOps team name for iteration lookup (defaults to project name). Used when resolving current iteration when --sprint is omitted.",
    ),
    ado_token: str | None = typer.Option(
        None, "--ado-token", help="Azure DevOps PAT (optional, uses AZURE_DEVOPS_TOKEN env var if not provided)"
    ),
    custom_field_mapping: str | None = typer.Option(
        None,
        "--custom-field-mapping",
        help="Path to custom ADO field mapping YAML file (overrides default mappings)",
    ),
) -> None:
    """
    Refine backlog items using AI-assisted template matching.

    This command:
    1. Fetches backlog items from the specified adapter
    2. Detects template matches with confidence scores
    3. Identifies items needing refinement (low confidence or no match)
    4. Generates prompts for IDE AI copilot to refine items
    5. Validates refined content from IDE AI copilot
    6. Updates remote backlog with refined content
    7. Optionally imports refined items to OpenSpec bundle

    SpecFact CLI Architecture:
    - This command generates prompts for IDE AI copilots (Cursor, Claude Code, etc.)
    - IDE AI copilots execute those prompts using their native LLM
    - IDE AI copilots feed refined content back to this command
    - This command validates and processes the refined content
    """
    try:
        # Show initialization progress to provide feedback during setup
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        ) as init_progress:
            # Initialize template registry and load templates
            init_task = init_progress.add_task("[cyan]Initializing templates...[/cyan]", total=None)
            registry = TemplateRegistry()

            # Determine template directories (built-in first so custom overrides take effect)
            from specfact_cli.utils.ide_setup import find_package_resources_path

            current_dir = Path.cwd()

            # 1. Load built-in templates from resources/templates/backlog/ (preferred location)
            # Try to find resources directory using package resource finder (for installed packages)
            resources_path = find_package_resources_path("specfact_cli", "resources/templates/backlog")
            built_in_loaded = False
            if resources_path and resources_path.exists():
                registry.load_templates_from_directory(resources_path)
                built_in_loaded = True
            else:
                # Fallback: Try relative to repo root (development mode)
                # __file__ = src/specfact_cli/modules/backlog/src/commands.py → 6 parents to repo root
                repo_root = Path(__file__).parent.parent.parent.parent.parent.parent
                resources_templates_dir = repo_root / "resources" / "templates" / "backlog"
                if resources_templates_dir.exists():
                    registry.load_templates_from_directory(resources_templates_dir)
                    built_in_loaded = True
                else:
                    # 2. Fallback to src/specfact_cli/templates/ for backward compatibility
                    # __file__ → 4 parents to reach src/specfact_cli/
                    src_templates_dir = Path(__file__).parent.parent.parent.parent / "templates"
                    if src_templates_dir.exists():
                        registry.load_templates_from_directory(src_templates_dir)
                        built_in_loaded = True

            if not built_in_loaded:
                console.print(
                    "[yellow]⚠ No built-in backlog templates found; continuing with custom templates only.[/yellow]"
                )

            # 3. Load custom templates from project directory (highest priority)
            project_templates_dir = current_dir / ".specfact" / "templates" / "backlog"
            if project_templates_dir.exists():
                registry.load_templates_from_directory(project_templates_dir)

            init_progress.update(init_task, description="[green]✓[/green] Templates initialized")

            # Initialize template detector
            detector_task = init_progress.add_task("[cyan]Initializing template detector...[/cyan]", total=None)
            detector = TemplateDetector(registry)
            init_progress.update(detector_task, description="[green]✓[/green] Template detector ready")

            # Initialize AI refiner (prompt generator and validator)
            refiner_task = init_progress.add_task("[cyan]Initializing AI refiner...[/cyan]", total=None)
            refiner = BacklogAIRefiner()
            init_progress.update(refiner_task, description="[green]✓[/green] AI refiner ready")

            # Get adapter registry for writeback
            adapter_task = init_progress.add_task("[cyan]Initializing adapter...[/cyan]", total=None)
            adapter_registry = AdapterRegistry()
            init_progress.update(adapter_task, description="[green]✓[/green] Adapter registry ready")

            # Load DoR configuration (if --check-dor flag set)
            dor_config: DefinitionOfReady | None = None
            if check_dor:
                dor_task = init_progress.add_task("[cyan]Loading DoR configuration...[/cyan]", total=None)
                repo_path = Path(".")
                dor_config = DefinitionOfReady.load_from_repo(repo_path)
                if dor_config:
                    init_progress.update(dor_task, description="[green]✓[/green] DoR configuration loaded")
                else:
                    init_progress.update(dor_task, description="[yellow]⚠[/yellow] Using default DoR rules")
                    # Use default DoR rules
                    dor_config = DefinitionOfReady(
                        rules={
                            "story_points": True,
                            "value_points": False,  # Optional by default
                            "priority": True,
                            "business_value": True,
                            "acceptance_criteria": True,
                            "dependencies": False,  # Optional by default
                        }
                    )

            # Normalize adapter, framework, and persona to lowercase for template matching
            # Template metadata in YAML uses lowercase (e.g., provider: github, framework: scrum)
            # This ensures case-insensitive matching regardless of CLI input case
            normalized_adapter = adapter.lower() if adapter else None
            normalized_framework = framework.lower() if framework else None
            normalized_persona = persona.lower() if persona else None

            # Validate adapter-specific required parameters (use same resolution as daily: CLI > env > config > git)
            validate_task = init_progress.add_task("[cyan]Validating adapter configuration...[/cyan]", total=None)
            writeback_kwargs = _build_adapter_kwargs(
                adapter,
                repo_owner=repo_owner,
                repo_name=repo_name,
                github_token=github_token,
                ado_org=ado_org,
                ado_project=ado_project,
                ado_team=ado_team,
                ado_token=ado_token,
            )
            if normalized_adapter == "github" and (
                not writeback_kwargs.get("repo_owner") or not writeback_kwargs.get("repo_name")
            ):
                init_progress.stop()
                console.print("[red]repo_owner and repo_name required for GitHub.[/red]")
                console.print(
                    "Set via: [cyan]--repo-owner[/cyan]/[cyan]--repo-name[/cyan], "
                    "env [cyan]SPECFACT_GITHUB_REPO_OWNER[/cyan]/[cyan]SPECFACT_GITHUB_REPO_NAME[/cyan], "
                    "or [cyan].specfact/backlog.yaml[/cyan] (see docs/guides/devops-adapter-integration.md)."
                )
                raise typer.Exit(1)
            if normalized_adapter == "ado" and (not writeback_kwargs.get("org") or not writeback_kwargs.get("project")):
                init_progress.stop()
                console.print(
                    "[red]ado_org and ado_project required for Azure DevOps.[/red] "
                    "Set via --ado-org/--ado-project, env SPECFACT_ADO_ORG/SPECFACT_ADO_PROJECT, or .specfact/backlog.yaml."
                )
                raise typer.Exit(1)

            # Validate and set custom field mapping (if provided)
            if custom_field_mapping:
                mapping_path = Path(custom_field_mapping)
                if not mapping_path.exists():
                    init_progress.stop()
                    console.print(f"[red]Error:[/red] Custom field mapping file not found: {custom_field_mapping}")
                    sys.exit(1)
                if not mapping_path.is_file():
                    init_progress.stop()
                    console.print(f"[red]Error:[/red] Custom field mapping path is not a file: {custom_field_mapping}")
                    sys.exit(1)
                # Validate file format by attempting to load it
                try:
                    from specfact_cli.backlog.mappers.template_config import FieldMappingConfig

                    FieldMappingConfig.from_file(mapping_path)
                    init_progress.update(validate_task, description="[green]✓[/green] Field mapping validated")
                except (FileNotFoundError, ValueError, yaml.YAMLError) as e:
                    init_progress.stop()
                    console.print(f"[red]Error:[/red] Invalid custom field mapping file: {e}")
                    sys.exit(1)
                # Set environment variable for converter to use
                os.environ["SPECFACT_ADO_CUSTOM_MAPPING"] = str(mapping_path.absolute())
            else:
                init_progress.update(validate_task, description="[green]✓[/green] Configuration validated")

        # Fetch backlog items with filters
        # When ignore_refined and limit are set, fetch more candidates so we have enough after filtering
        fetch_limit: int | None = limit
        if ignore_refined and limit is not None and limit > 0:
            fetch_limit = limit * 5
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        ) as progress:
            fetch_task = progress.add_task(f"[cyan]Fetching backlog items from {adapter}...[/cyan]", total=None)
            items = _fetch_backlog_items(
                adapter,
                search_query=search,
                labels=labels,
                state=state,
                assignee=assignee,
                iteration=iteration,
                sprint=sprint,
                release=release,
                limit=fetch_limit,
                repo_owner=repo_owner,
                repo_name=repo_name,
                github_token=github_token,
                ado_org=ado_org,
                ado_project=ado_project,
                ado_team=ado_team,
                ado_token=ado_token,
            )
            progress.update(fetch_task, description="[green]✓[/green] Fetched backlog items")

        if not items:
            # Provide helpful message when no items found, especially if filters were used
            filter_info = []
            if state:
                filter_info.append(f"state={state}")
            if assignee:
                filter_info.append(f"assignee={assignee}")
            if iteration:
                filter_info.append(f"iteration={iteration}")
            if sprint:
                filter_info.append(f"sprint={sprint}")
            if release:
                filter_info.append(f"release={release}")

            if filter_info:
                console.print(
                    f"[yellow]No backlog items found with the specified filters:[/yellow] {', '.join(filter_info)}\n"
                    f"[cyan]Tips:[/cyan]\n"
                    f"  • Verify the iteration path exists in Azure DevOps (Project Settings → Boards → Iterations)\n"
                    f"  • Try using [bold]--iteration current[/bold] to use the current active iteration\n"
                    f"  • Try using [bold]--sprint[/bold] with just the sprint name for automatic matching\n"
                    f"  • Check that items exist in the specified iteration/sprint"
                )
            else:
                console.print("[yellow]No backlog items found.[/yellow]")
            return

        # Filter by issue ID when --id is set
        if issue_id is not None:
            items = [i for i in items if str(i.id) == str(issue_id)]
            if not items:
                console.print(
                    f"[bold red]✗[/bold red] No backlog item with id {issue_id!r} found. "
                    "Check filters and adapter configuration."
                )
                raise typer.Exit(1)

        # When ignore_refined (default), keep only items that need refinement; then apply windowing/limit
        if ignore_refined:
            items = [
                i
                for i in items
                if _item_needs_refinement(
                    i, detector, registry, template_id, normalized_adapter, normalized_framework, normalized_persona
                )
            ]
            if ignore_refined and (
                limit is not None or issue_id is not None or first_issues is not None or last_issues is not None
            ):
                console.print(
                    f"[dim]Filtered to {len(items)} item(s) needing refinement"
                    + (f" (limit {limit})" if limit is not None else "")
                    + "[/dim]"
                )

        # Validate export/import flags
        if export_to_tmp and import_from_tmp:
            console.print("[bold red]✗[/bold red] --export-to-tmp and --import-from-tmp are mutually exclusive")
            raise typer.Exit(1)
        if first_comments is not None and last_comments is not None:
            console.print("[bold red]✗[/bold red] Use only one of --first-comments or --last-comments")
            raise typer.Exit(1)
        if first_issues is not None and last_issues is not None:
            console.print("[bold red]✗[/bold red] Use only one of --first-issues or --last-issues")
            raise typer.Exit(1)

        items = _apply_issue_window(items, first_issues=first_issues, last_issues=last_issues)

        # Handle export mode
        if export_to_tmp:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            export_file = tmp_file or (Path(tempfile.gettempdir()) / f"specfact-backlog-refine-{timestamp}.md")

            console.print(f"[bold cyan]Exporting {len(items)} backlog item(s) to: {export_file}[/bold cyan]")
            if first_comments is not None or last_comments is not None:
                console.print(
                    "[dim]Note: --first-comments/--last-comments apply to preview and write prompt context; export always includes full comments.[/dim]"
                )
            export_first_comments, export_last_comments = _resolve_refine_export_comment_window(
                first_comments=first_comments,
                last_comments=last_comments,
            )
            comments_by_item_id = _collect_comment_annotations(
                adapter,
                items,
                repo_owner=repo_owner,
                repo_name=repo_name,
                github_token=github_token,
                ado_org=ado_org,
                ado_project=ado_project,
                ado_token=ado_token,
                first_comments=export_first_comments,
                last_comments=export_last_comments,
            )
            template_guidance_by_item_id: dict[str, dict[str, Any]] = {}
            for export_item in items:
                target_template = _resolve_target_template_for_refine_item(
                    export_item,
                    detector=detector,
                    registry=registry,
                    template_id=template_id,
                    normalized_adapter=normalized_adapter,
                    normalized_framework=normalized_framework,
                    normalized_persona=normalized_persona,
                )
                if target_template is not None:
                    template_guidance_by_item_id[export_item.id] = {
                        "template_id": target_template.template_id,
                        "name": target_template.name,
                        "description": target_template.description,
                        "required_sections": list(target_template.required_sections or []),
                        "optional_sections": list(target_template.optional_sections or []),
                    }
            export_content = _build_refine_export_content(
                adapter,
                items,
                comments_by_item_id=comments_by_item_id or None,
                template_guidance_by_item_id=template_guidance_by_item_id or None,
            )

            export_file.write_text(export_content, encoding="utf-8")
            console.print(f"[green]✓ Exported to: {export_file}[/green]")
            console.print("[dim]Process items with copilot, then use --import-from-tmp to import refined content[/dim]")
            return

        # Handle import mode
        if import_from_tmp:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            import_file = tmp_file or (Path(tempfile.gettempdir()) / f"specfact-backlog-refine-{timestamp}-refined.md")

            if not import_file.exists():
                console.print(f"[bold red]✗[/bold red] Import file not found: {import_file}")
                console.print(f"[dim]Expected file: {import_file}[/dim]")
                console.print("[dim]Or specify custom path with --tmp-file[/dim]")
                raise typer.Exit(1)

            console.print(f"[bold cyan]Importing refined content from: {import_file}[/bold cyan]")
            try:
                raw = import_file.read_text(encoding="utf-8")
                if is_debug_mode():
                    debug_log_operation("file_read", str(import_file), "success")
            except OSError as e:
                if is_debug_mode():
                    debug_log_operation("file_read", str(import_file), "error", error=str(e))
                raise
            parsed_by_id = _parse_refined_export_markdown(raw)
            if not parsed_by_id:
                console.print(
                    "[yellow]No valid item blocks found in import file (expected ## Item N: and **ID**:)[/yellow]"
                )
                raise typer.Exit(1)

            updated_items: list[BacklogItem] = []
            for item in items:
                if item.id not in parsed_by_id:
                    continue
                data = parsed_by_id[item.id]
                body = data.get("body_markdown", item.body_markdown or "")
                item.body_markdown = body if body is not None else (item.body_markdown or "")
                if "acceptance_criteria" in data:
                    item.acceptance_criteria = data["acceptance_criteria"]
                if data.get("title"):
                    item.title = data["title"]
                if "story_points" in data:
                    item.story_points = data["story_points"]
                if "business_value" in data:
                    item.business_value = data["business_value"]
                if "priority" in data:
                    item.priority = data["priority"]
                updated_items.append(item)

            if not write:
                console.print(f"[green]Would update {len(updated_items)} item(s)[/green]")
                console.print("[dim]Run with --write to apply changes to the backlog[/dim]")
                return

            writeback_kwargs = _build_adapter_kwargs(
                adapter,
                repo_owner=repo_owner,
                repo_name=repo_name,
                github_token=github_token,
                ado_org=ado_org,
                ado_project=ado_project,
                ado_team=ado_team,
                ado_token=ado_token,
            )
            adapter_instance = adapter_registry.get_adapter(adapter, **writeback_kwargs)
            if not isinstance(adapter_instance, BacklogAdapter):
                console.print("[bold red]✗[/bold red] Adapter does not support backlog updates")
                raise typer.Exit(1)

            for item in updated_items:
                update_fields_list = ["title", "body_markdown"]
                if item.acceptance_criteria:
                    update_fields_list.append("acceptance_criteria")
                if item.story_points is not None:
                    update_fields_list.append("story_points")
                if item.business_value is not None:
                    update_fields_list.append("business_value")
                if item.priority is not None:
                    update_fields_list.append("priority")
                adapter_instance.update_backlog_item(item, update_fields=update_fields_list)
                console.print(f"[green]✓ Updated backlog item: {item.url}[/green]")
            console.print(f"[green]✓ Updated {len(updated_items)} backlog item(s)[/green]")
            return

        # Apply limit if specified
        if limit is not None and len(items) > limit:
            items = items[:limit]
            console.print(f"[yellow]Limited to {limit} items (found {len(items)} total)[/yellow]")
        else:
            console.print(f"[green]Found {len(items)} backlog items[/green]")

        # Process each item
        refined_count = 0
        skipped_count = 0
        cancelled = False
        comments_by_item_id: dict[str, list[str]] = {}
        if preview and not write:
            preview_first_comments, preview_last_comments = _resolve_refine_preview_comment_window(
                first_comments=first_comments,
                last_comments=last_comments,
            )
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                console=console,
                transient=False,
            ) as preview_comment_progress:
                preview_comment_task = preview_comment_progress.add_task(
                    _build_comment_fetch_progress_description(0, len(items), "-"),
                    total=None,
                )

                def _on_preview_comment_progress(index: int, total: int, item: BacklogItem) -> None:
                    preview_comment_progress.update(
                        preview_comment_task,
                        description=_build_comment_fetch_progress_description(index, total, item.id),
                    )

                comments_by_item_id = _collect_comment_annotations(
                    adapter,
                    items,
                    repo_owner=repo_owner,
                    repo_name=repo_name,
                    github_token=github_token,
                    ado_org=ado_org,
                    ado_project=ado_project,
                    ado_token=ado_token,
                    first_comments=preview_first_comments,
                    last_comments=preview_last_comments,
                    progress_callback=_on_preview_comment_progress,
                )
                preview_comment_progress.update(
                    preview_comment_task,
                    description=f"[green]✓[/green] Fetched comments for {len(items)} issue(s)",
                )
        elif write:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                console=console,
                transient=False,
            ) as write_comment_progress:
                write_comment_task = write_comment_progress.add_task(
                    _build_comment_fetch_progress_description(0, len(items), "-"),
                    total=None,
                )

                def _on_write_comment_progress(index: int, total: int, item: BacklogItem) -> None:
                    write_comment_progress.update(
                        write_comment_task,
                        description=_build_comment_fetch_progress_description(index, total, item.id),
                    )

                comments_by_item_id = _collect_comment_annotations(
                    adapter,
                    items,
                    repo_owner=repo_owner,
                    repo_name=repo_name,
                    github_token=github_token,
                    ado_org=ado_org,
                    ado_project=ado_project,
                    ado_token=ado_token,
                    first_comments=first_comments,
                    last_comments=last_comments,
                    progress_callback=_on_write_comment_progress,
                )
                write_comment_progress.update(
                    write_comment_task,
                    description=f"[green]✓[/green] Fetched comments for {len(items)} issue(s)",
                )

        # Process items without progress bar during refinement to avoid conflicts with interactive prompts
        for idx, item in enumerate(items, 1):
            # Check for cancellation
            if cancelled:
                break

            # Show simple status text instead of progress bar
            console.print(f"\n[bold cyan]Refining item {idx} of {len(items)}: {item.title}[/bold cyan]")

            # Check DoR (if enabled)
            if check_dor and dor_config:
                item_dict = item.model_dump()
                dor_errors = dor_config.validate_item(item_dict)
                if dor_errors:
                    console.print("[yellow]⚠ Definition of Ready (DoR) issues:[/yellow]")
                    for error in dor_errors:
                        console.print(f"  - {error}")
                    console.print("[yellow]Item may not be ready for sprint planning[/yellow]")
                else:
                    console.print("[green]✓ Definition of Ready (DoR) satisfied[/green]")

            # Detect template with persona/framework/provider filtering
            # Use normalized values for case-insensitive template matching
            detection_result = detector.detect_template(
                item, provider=normalized_adapter, framework=normalized_framework, persona=normalized_persona
            )

            if detection_result.template_id:
                template_id_str = detection_result.template_id
                confidence_str = f"{detection_result.confidence:.2f}"
                console.print(f"[green]✓ Detected template: {template_id_str} (confidence: {confidence_str})[/green]")
                item.detected_template = detection_result.template_id
                item.template_confidence = detection_result.confidence
                item.template_missing_fields = detection_result.missing_fields

                # Check if item already has checkboxes in required sections (already refined)
                # Items with checkboxes (- [ ] or - [x]) in required sections are considered already refined
                target_template_for_check = (
                    registry.get_template(detection_result.template_id) if detection_result.template_id else None
                )
                if target_template_for_check:
                    import re

                    has_checkboxes = bool(
                        re.search(r"^[\s]*- \[[ x]\]", item.body_markdown, re.MULTILINE | re.IGNORECASE)
                    )
                    # Check if all required sections are present
                    all_sections_present = True
                    for section in target_template_for_check.required_sections:
                        # Look for section heading (## Section Name or ### Section Name)
                        section_pattern = rf"^#+\s+{re.escape(section)}\s*$"
                        if not re.search(section_pattern, item.body_markdown, re.MULTILINE | re.IGNORECASE):
                            all_sections_present = False
                            break
                    # If item has checkboxes and all required sections, it's already refined - skip it
                    if has_checkboxes and all_sections_present and not detection_result.missing_fields:
                        console.print(
                            "[green]Item already refined with checkboxes and all required sections - skipping[/green]"
                        )
                        skipped_count += 1
                        continue

                # High confidence AND no missing required fields - no refinement needed
                # Note: Even with high confidence, if required sections are missing, refinement is needed
                if template_id is None and detection_result.confidence >= 0.8 and not detection_result.missing_fields:
                    console.print(
                        "[green]High confidence match with all required sections - no refinement needed[/green]"
                    )
                    skipped_count += 1
                    continue
                if detection_result.missing_fields:
                    missing_str = ", ".join(detection_result.missing_fields)
                    console.print(f"[yellow]⚠ Missing required sections: {missing_str} - refinement needed[/yellow]")

            # Low confidence or no match - needs refinement
            # Get target template using priority-based resolution
            target_template = None
            if template_id:
                target_template = registry.get_template(template_id)
                if not target_template:
                    console.print(f"[yellow]Template {template_id} not found, using auto-detection[/yellow]")
            elif detection_result.template_id:
                target_template = registry.get_template(detection_result.template_id)
            else:
                # Use priority-based template resolution
                # Use normalized values for case-insensitive template matching
                target_template = registry.resolve_template(
                    provider=normalized_adapter, framework=normalized_framework, persona=normalized_persona
                )
                if target_template:
                    resolved_id = target_template.template_id
                    console.print(f"[yellow]No template detected, using resolved template: {resolved_id}[/yellow]")
                else:
                    # Fallback: Use first available template as default
                    templates = registry.list_templates(scope="corporate")
                    if templates:
                        target_template = templates[0]
                        console.print(
                            f"[yellow]No template resolved, using default: {target_template.template_id}[/yellow]"
                        )

            if not target_template:
                console.print("[yellow]No template available for refinement[/yellow]")
                skipped_count += 1
                continue

            # In preview mode without --write, show full item details but skip interactive refinement
            if preview and not write:
                console.print("\n[bold]Preview Mode: Full Item Details[/bold]")
                console.print(f"[bold]Title:[/bold] {item.title}")
                console.print(f"[bold]URL:[/bold] {item.url}")
                if item.canonical_url:
                    console.print(f"[bold]Canonical URL:[/bold] {item.canonical_url}")
                console.print(f"[bold]State:[/bold] {item.state}")
                console.print(f"[bold]Provider:[/bold] {item.provider}")
                console.print(f"[bold]Assignee:[/bold] {', '.join(item.assignees) if item.assignees else 'Unassigned'}")

                # Show metrics if available
                if item.story_points is not None or item.business_value is not None or item.priority is not None:
                    console.print("\n[bold]Story Metrics:[/bold]")
                    if item.story_points is not None:
                        console.print(f"  - Story Points: {item.story_points}")
                    if item.business_value is not None:
                        console.print(f"  - Business Value: {item.business_value}")
                    if item.priority is not None:
                        console.print(f"  - Priority: {item.priority} (1=highest)")
                    if item.value_points is not None:
                        console.print(f"  - Value Points (SAFe): {item.value_points}")
                    if item.work_item_type:
                        console.print(f"  - Work Item Type: {item.work_item_type}")

                # Always show acceptance criteria if it's a required section, even if empty
                # This helps copilot understand what fields need to be added
                is_acceptance_criteria_required = (
                    target_template.required_sections and "Acceptance Criteria" in target_template.required_sections
                )
                if is_acceptance_criteria_required or item.acceptance_criteria:
                    console.print("\n[bold]Acceptance Criteria:[/bold]")
                    if item.acceptance_criteria:
                        console.print(Panel(item.acceptance_criteria))
                    else:
                        # Show empty state so copilot knows to add it
                        console.print(Panel("[dim](empty - required field)[/dim]", border_style="dim"))

                # Always show body (Description is typically required)
                console.print("\n[bold]Body:[/bold]")
                body_content = (
                    item.body_markdown[:1000] + "..." if len(item.body_markdown) > 1000 else item.body_markdown
                )
                if not body_content.strip():
                    # Show empty state so copilot knows to add it
                    console.print(Panel("[dim](empty - required field)[/dim]", border_style="dim"))
                else:
                    console.print(Panel(body_content))

                preview_comments = comments_by_item_id.get(item.id, [])
                console.print("\n[bold]Comments:[/bold]")
                if preview_comments:
                    for panel in _build_refine_preview_comment_panels(preview_comments):
                        console.print(panel)
                else:
                    console.print(_build_refine_preview_comment_empty_panel())

                # Show template info
                console.print(
                    f"\n[bold]Target Template:[/bold] {target_template.name} (ID: {target_template.template_id})"
                )
                console.print(f"[bold]Template Description:[/bold] {target_template.description}")

                # Show what would be updated
                console.print(
                    "\n[yellow]⚠ Preview mode: Item needs refinement but interactive prompts are skipped[/yellow]"
                )
                console.print(
                    "[yellow]   Use [bold]--write[/bold] flag to enable interactive refinement and writeback[/yellow]"
                )
                console.print(
                    "[yellow]   Or use [bold]--export-to-tmp[/bold] to export items for copilot processing[/yellow]"
                )
                skipped_count += 1
                continue

            # Generate prompt for IDE AI copilot
            console.print(f"[bold]Generating refinement prompt for template: {target_template.name}...[/bold]")
            prompt_comments = comments_by_item_id.get(item.id, [])
            prompt = refiner.generate_refinement_prompt(item, target_template, comments=prompt_comments)

            # Display prompt for IDE AI copilot
            console.print("\n[bold]Refinement Prompt for IDE AI Copilot:[/bold]")
            console.print(Panel(prompt, title="Copy this prompt to your IDE AI copilot"))

            # Prompt user to get refined content from IDE AI copilot
            console.print("\n[yellow]Instructions:[/yellow]")
            console.print("1. Copy the prompt above to your IDE AI copilot (Cursor, Claude Code, etc.)")
            console.print("2. Execute the prompt in your IDE AI copilot")
            console.print("3. Copy the refined content from the AI copilot response")
            console.print("4. Paste the refined content below, then type 'END' on a new line when done\n")

            try:
                refined_content = _read_refined_content_from_stdin()
            except KeyboardInterrupt:
                console.print("\n[yellow]Input cancelled - skipping[/yellow]")
                skipped_count += 1
                continue

            if refined_content == ":SKIP":
                console.print("[yellow]Skipping current item[/yellow]")
                skipped_count += 1
                continue
            if refined_content in (":QUIT", ":ABORT"):
                console.print("[yellow]Cancelling refinement session[/yellow]")
                cancelled = True
                break
            if not refined_content.strip():
                console.print("[yellow]No refined content provided - skipping[/yellow]")
                skipped_count += 1
                continue

            # Validate and score refined content (provider-aware)
            try:
                refinement_result = refiner.validate_and_score_refinement(
                    refined_content, item.body_markdown, target_template, item
                )

                # Print newline to separate validation results
                console.print()

                # Display validation result
                console.print("[bold]Refinement Validation Result:[/bold]")
                console.print(f"[green]Confidence: {refinement_result.confidence:.2f}[/green]")
                if refinement_result.has_todo_markers:
                    console.print("[yellow]⚠ Contains TODO markers[/yellow]")
                if refinement_result.has_notes_section:
                    console.print("[yellow]⚠ Contains NOTES section[/yellow]")

                # Display story metrics if available
                if item.story_points is not None or item.business_value is not None or item.priority is not None:
                    console.print("\n[bold]Story Metrics:[/bold]")
                    if item.story_points is not None:
                        console.print(f"  - Story Points: {item.story_points}")
                    if item.business_value is not None:
                        console.print(f"  - Business Value: {item.business_value}")
                    if item.priority is not None:
                        console.print(f"  - Priority: {item.priority} (1=highest)")
                    if item.value_points is not None:
                        console.print(f"  - Value Points (SAFe): {item.value_points}")
                    if item.work_item_type:
                        console.print(f"  - Work Item Type: {item.work_item_type}")

                # Display story splitting suggestion if needed
                if refinement_result.needs_splitting and refinement_result.splitting_suggestion:
                    console.print("\n[yellow]⚠ Story Splitting Recommendation:[/yellow]")
                    console.print(Panel(refinement_result.splitting_suggestion, title="Splitting Suggestion"))

                # Show preview with field preservation information
                console.print("\n[bold]Preview: What will be updated[/bold]")
                console.print("[dim]Fields that will be UPDATED:[/dim]")
                console.print("  - title: Will be updated if changed")
                console.print("  - body_markdown: Will be updated with refined content")
                console.print("[dim]Fields that will be PRESERVED (not modified):[/dim]")
                console.print("  - assignees: Preserved")
                console.print("  - tags: Preserved")
                console.print("  - state: Preserved")
                console.print("  - priority: Preserved (if present in provider_fields)")
                console.print("  - due_date: Preserved (if present in provider_fields)")
                console.print("  - story_points: Preserved (if present in provider_fields)")
                console.print("  - business_value: Preserved (if present in provider_fields)")
                console.print("  - priority: Preserved (if present in provider_fields)")
                console.print("  - acceptance_criteria: Preserved (if present in provider_fields)")
                console.print("  - All other metadata: Preserved in provider_fields")

                console.print("\n[bold]Original:[/bold]")
                console.print(
                    Panel(item.body_markdown[:500] + "..." if len(item.body_markdown) > 500 else item.body_markdown)
                )
                console.print("\n[bold]Refined:[/bold]")
                console.print(
                    Panel(
                        refinement_result.refined_body[:500] + "..."
                        if len(refinement_result.refined_body) > 500
                        else refinement_result.refined_body
                    )
                )

                # Parse structured refinement output before writeback so provider fields
                # are updated from canonical values instead of writing prompt labels verbatim.
                parsed_refined_fields = _parse_refinement_output_fields(refinement_result.refined_body)
                item.refined_body = parsed_refined_fields.get("body_markdown", refinement_result.refined_body)

                if parsed_refined_fields.get("acceptance_criteria"):
                    item.acceptance_criteria = parsed_refined_fields["acceptance_criteria"]
                if parsed_refined_fields.get("story_points") is not None:
                    item.story_points = parsed_refined_fields["story_points"]
                if parsed_refined_fields.get("business_value") is not None:
                    item.business_value = parsed_refined_fields["business_value"]
                if parsed_refined_fields.get("priority") is not None:
                    item.priority = parsed_refined_fields["priority"]
                if parsed_refined_fields.get("work_item_type"):
                    item.work_item_type = parsed_refined_fields["work_item_type"]

                # Preview mode (default) - don't write, just show preview
                if preview and not write:
                    console.print("\n[yellow]Preview mode: Refinement will NOT be written to backlog[/yellow]")
                    console.print("[yellow]Use --write flag to explicitly opt-in to writeback[/yellow]")
                    refined_count += 1  # Count as refined for preview purposes
                    continue

                if write:
                    should_write = False
                    if auto_accept_high_confidence and refinement_result.confidence >= 0.85:
                        console.print("[green]Auto-accepting high-confidence refinement and writing to backlog[/green]")
                        should_write = True
                    else:
                        console.print()
                        should_write = Confirm.ask("Accept refinement and write to backlog?", default=False)

                    if should_write:
                        item.apply_refinement()
                        _write_refined_backlog_item(
                            adapter_registry=adapter_registry,
                            adapter=adapter,
                            item=item,
                            repo_owner=repo_owner,
                            repo_name=repo_name,
                            github_token=github_token,
                            ado_org=ado_org,
                            ado_project=ado_project,
                            ado_token=ado_token,
                            openspec_comment=openspec_comment,
                        )
                        refined_count += 1
                    else:
                        console.print("[yellow]Refinement rejected - not writing to backlog[/yellow]")
                        skipped_count += 1
                else:
                    # Preview mode but user didn't explicitly set --write
                    console.print("[yellow]Preview mode: Use --write to update backlog[/yellow]")
                    refined_count += 1

            except ValueError as e:
                console.print(f"[red]Validation failed: {e}[/red]")
                console.print("[yellow]Please fix the refined content and try again[/yellow]")
                skipped_count += 1
                continue

        # OpenSpec bundle import (if requested)
        if (bundle or auto_bundle) and refined_count > 0:
            console.print("\n[bold]OpenSpec Bundle Import:[/bold]")
            try:
                # Determine bundle path
                bundle_path: Path | None = None
                if bundle:
                    bundle_path = Path(bundle)
                elif auto_bundle:
                    # Auto-detect bundle from current directory
                    current_dir = Path.cwd()
                    bundle_path = current_dir / ".specfact" / "bundle.yaml"
                    if not bundle_path.exists():
                        bundle_path = current_dir / "bundle.yaml"

                if bundle_path and bundle_path.exists():
                    console.print(
                        f"[green]Importing {refined_count} refined items to OpenSpec bundle: {bundle_path}[/green]"
                    )
                    # TODO: Implement actual import logic using import command functionality
                    console.print(
                        "[yellow]⚠ OpenSpec bundle import integration pending (use import command separately)[/yellow]"
                    )
                else:
                    console.print("[yellow]⚠ Bundle path not found. Skipping import.[/yellow]")
            except Exception as e:
                console.print(f"[yellow]⚠ Failed to import to OpenSpec bundle: {e}[/yellow]")

        # Summary
        console.print("\n[bold]Summary:[/bold]")
        if cancelled:
            console.print("[yellow]Session cancelled by user[/yellow]")
        if limit:
            console.print(f"[dim]Limit applied: {limit} items[/dim]")
        if first_issues is not None:
            console.print(f"[dim]Issue window applied: first {first_issues} items[/dim]")
        if last_issues is not None:
            console.print(f"[dim]Issue window applied: last {last_issues} items[/dim]")
        console.print(f"[green]Refined: {refined_count}[/green]")
        console.print(f"[yellow]Skipped: {skipped_count}[/yellow]")

        # Note: Writeback is handled per-item above when --write flag is set

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


@app.command("map-fields")
@require(
    lambda ado_org, ado_project: isinstance(ado_org, str)
    and len(ado_org) > 0
    and isinstance(ado_project, str)
    and len(ado_project) > 0,
    "ADO org and project must be non-empty strings",
)
@beartype
def map_fields(
    ado_org: str = typer.Option(..., "--ado-org", help="Azure DevOps organization (required)"),
    ado_project: str = typer.Option(..., "--ado-project", help="Azure DevOps project (required)"),
    ado_token: str | None = typer.Option(
        None, "--ado-token", help="Azure DevOps PAT (optional, uses AZURE_DEVOPS_TOKEN env var if not provided)"
    ),
    ado_base_url: str | None = typer.Option(
        None, "--ado-base-url", help="Azure DevOps base URL (defaults to https://dev.azure.com)"
    ),
    reset: bool = typer.Option(
        False, "--reset", help="Reset custom field mapping to defaults (deletes ado_custom.yaml)"
    ),
) -> None:
    """
    Interactive command to map ADO fields to canonical field names.

    Fetches available fields from Azure DevOps API and guides you through
    mapping them to canonical field names (description, acceptance_criteria, etc.).
    Saves the mapping to .specfact/templates/backlog/field_mappings/ado_custom.yaml.

    Examples:
        specfact backlog map-fields --ado-org myorg --ado-project myproject
        specfact backlog map-fields --ado-org myorg --ado-project myproject --ado-token <token>
        specfact backlog map-fields --ado-org myorg --ado-project myproject --reset
    """
    import base64
    import re

    import requests

    from specfact_cli.backlog.mappers.template_config import FieldMappingConfig
    from specfact_cli.utils.auth_tokens import get_token

    def _find_potential_match(canonical_field: str, available_fields: list[dict[str, Any]]) -> str | None:
        """
        Find a potential ADO field match for a canonical field using regex/fuzzy matching.

        Args:
            canonical_field: Canonical field name (e.g., "acceptance_criteria")
            available_fields: List of ADO field dicts with "referenceName" and "name"

        Returns:
            Reference name of best matching field, or None if no good match found
        """
        # Convert canonical field to search patterns
        # e.g., "acceptance_criteria" -> ["acceptance", "criteria"]
        field_parts = re.split(r"[_\s-]+", canonical_field.lower())

        best_match: tuple[str, int] | None = None
        best_score = 0

        for field in available_fields:
            ref_name = field.get("referenceName", "")
            name = field.get("name", ref_name)

            # Search in both reference name and display name
            search_text = f"{ref_name} {name}".lower()

            # Calculate match score
            score = 0
            matched_parts = 0

            for part in field_parts:
                # Exact match in reference name (highest priority)
                if part in ref_name.lower():
                    score += 10
                    matched_parts += 1
                # Exact match in display name
                elif part in name.lower():
                    score += 5
                    matched_parts += 1
                # Partial match (contains substring)
                elif part in search_text:
                    score += 2
                    matched_parts += 1

            # Bonus for matching all parts
            if matched_parts == len(field_parts):
                score += 5

            # Prefer Microsoft.VSTS.Common.* fields
            if ref_name.startswith("Microsoft.VSTS.Common."):
                score += 3

            if score > best_score and matched_parts > 0:
                best_score = score
                best_match = (ref_name, score)

        # Only return if we have a reasonable match (score >= 5)
        if best_match and best_score >= 5:
            return best_match[0]

        return None

    # Resolve token (explicit > env var > stored token)
    api_token: str | None = None
    auth_scheme = "basic"
    if ado_token:
        api_token = ado_token
        auth_scheme = "basic"
    elif os.environ.get("AZURE_DEVOPS_TOKEN"):
        api_token = os.environ.get("AZURE_DEVOPS_TOKEN")
        auth_scheme = "basic"
    elif stored_token := get_token("azure-devops", allow_expired=False):
        # Valid, non-expired token found
        api_token = stored_token.get("access_token")
        token_type = (stored_token.get("token_type") or "bearer").lower()
        auth_scheme = "bearer" if token_type == "bearer" else "basic"
    elif stored_token_expired := get_token("azure-devops", allow_expired=True):
        # Token exists but is expired - use it anyway for this command (user can refresh later)
        api_token = stored_token_expired.get("access_token")
        token_type = (stored_token_expired.get("token_type") or "bearer").lower()
        auth_scheme = "bearer" if token_type == "bearer" else "basic"
        console.print(
            "[yellow]⚠[/yellow] Using expired stored token. If authentication fails, refresh with: specfact auth azure-devops"
        )

    if not api_token:
        console.print("[red]Error:[/red] Azure DevOps token required")
        console.print("[yellow]Options:[/yellow]")
        console.print("  1. Use --ado-token option")
        console.print("  2. Set AZURE_DEVOPS_TOKEN environment variable")
        console.print("  3. Use: specfact auth azure-devops")
        raise typer.Exit(1)

    # Build base URL
    base_url = (ado_base_url or "https://dev.azure.com").rstrip("/")

    # Fetch fields from ADO API
    console.print("[cyan]Fetching fields from Azure DevOps...[/cyan]")
    fields_url = f"{base_url}/{ado_org}/{ado_project}/_apis/wit/fields?api-version=7.1"

    # Prepare authentication headers based on auth scheme
    headers: dict[str, str] = {}
    if auth_scheme == "bearer":
        headers["Authorization"] = f"Bearer {api_token}"
    else:
        # Basic auth for PAT tokens
        auth_header = base64.b64encode(f":{api_token}".encode()).decode()
        headers["Authorization"] = f"Basic {auth_header}"

    try:
        response = requests.get(fields_url, headers=headers, timeout=30)
        response.raise_for_status()
        fields_data = response.json()
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error:[/red] Failed to fetch fields from Azure DevOps: {e}")
        raise typer.Exit(1) from e

    # Extract fields and filter out system-only fields
    all_fields = fields_data.get("value", [])
    system_only_fields = {
        "System.Id",
        "System.Rev",
        "System.ChangedDate",
        "System.CreatedDate",
        "System.ChangedBy",
        "System.CreatedBy",
        "System.AreaId",
        "System.IterationId",
        "System.TeamProject",
        "System.NodeName",
        "System.AreaLevel1",
        "System.AreaLevel2",
        "System.AreaLevel3",
        "System.AreaLevel4",
        "System.AreaLevel5",
        "System.AreaLevel6",
        "System.AreaLevel7",
        "System.AreaLevel8",
        "System.AreaLevel9",
        "System.AreaLevel10",
        "System.IterationLevel1",
        "System.IterationLevel2",
        "System.IterationLevel3",
        "System.IterationLevel4",
        "System.IterationLevel5",
        "System.IterationLevel6",
        "System.IterationLevel7",
        "System.IterationLevel8",
        "System.IterationLevel9",
        "System.IterationLevel10",
    }

    # Filter relevant fields
    relevant_fields = [
        field
        for field in all_fields
        if field.get("referenceName") not in system_only_fields
        and not field.get("referenceName", "").startswith("System.History")
        and not field.get("referenceName", "").startswith("System.Watermark")
    ]

    # Sort fields by reference name
    relevant_fields.sort(key=lambda f: f.get("referenceName", ""))

    # Canonical fields to map
    canonical_fields = {
        "description": "Description",
        "acceptance_criteria": "Acceptance Criteria",
        "story_points": "Story Points",
        "business_value": "Business Value",
        "priority": "Priority",
        "work_item_type": "Work Item Type",
    }

    # Load default mappings from AdoFieldMapper
    from specfact_cli.backlog.mappers.ado_mapper import AdoFieldMapper

    default_mappings = AdoFieldMapper.DEFAULT_FIELD_MAPPINGS
    # Reverse default mappings: canonical -> list of ADO fields
    default_mappings_reversed: dict[str, list[str]] = {}
    for ado_field, canonical in default_mappings.items():
        if canonical not in default_mappings_reversed:
            default_mappings_reversed[canonical] = []
        default_mappings_reversed[canonical].append(ado_field)

    # Handle --reset flag
    current_dir = Path.cwd()
    custom_mapping_file = current_dir / ".specfact" / "templates" / "backlog" / "field_mappings" / "ado_custom.yaml"

    if reset:
        if custom_mapping_file.exists():
            custom_mapping_file.unlink()
            console.print(f"[green]✓[/green] Reset custom field mapping (deleted {custom_mapping_file})")
            console.print("[dim]Custom mappings removed. Default mappings will be used.[/dim]")
        else:
            console.print("[yellow]⚠[/yellow] No custom mapping file found. Nothing to reset.")
        return

    # Load existing mapping if it exists
    existing_mapping: dict[str, str] = {}
    existing_work_item_type_mappings: dict[str, str] = {}
    existing_config: FieldMappingConfig | None = None
    if custom_mapping_file.exists():
        try:
            existing_config = FieldMappingConfig.from_file(custom_mapping_file)
            existing_mapping = existing_config.field_mappings
            existing_work_item_type_mappings = existing_config.work_item_type_mappings or {}
            console.print(f"[green]✓[/green] Loaded existing mapping from {custom_mapping_file}")
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Failed to load existing mapping: {e}")

    # Build combined mapping: existing > default (checking which defaults exist in fetched fields)
    combined_mapping: dict[str, str] = {}
    # Get list of available ADO field reference names
    available_ado_refs = {field.get("referenceName", "") for field in relevant_fields}

    # First add defaults, but only if they exist in the fetched ADO fields
    for canonical_field in canonical_fields:
        if canonical_field in default_mappings_reversed:
            # Find which default mappings actually exist in the fetched ADO fields
            # Prefer more common field names (Microsoft.VSTS.Common.* over System.*)
            default_options = default_mappings_reversed[canonical_field]
            existing_defaults = [ado_field for ado_field in default_options if ado_field in available_ado_refs]

            if existing_defaults:
                # Prefer Microsoft.VSTS.Common.* over System.* for better compatibility
                preferred = None
                for ado_field in existing_defaults:
                    if ado_field.startswith("Microsoft.VSTS.Common."):
                        preferred = ado_field
                        break
                # If no Microsoft.VSTS.Common.* found, use first existing
                if preferred is None:
                    preferred = existing_defaults[0]
                combined_mapping[preferred] = canonical_field
            else:
                # No default mapping exists - try to find a potential match using regex/fuzzy matching
                potential_match = _find_potential_match(canonical_field, relevant_fields)
                if potential_match:
                    combined_mapping[potential_match] = canonical_field
    # Then override with existing mappings
    combined_mapping.update(existing_mapping)

    # Interactive mapping
    try:
        import questionary  # type: ignore[reportMissingImports]
    except ImportError:
        console.print(
            "[red]Interactive field mapping requires the 'questionary' package. Install with: pip install questionary[/red]"
        )
        raise typer.Exit(1) from None

    console.print()
    console.print(Panel("[bold cyan]Interactive Field Mapping[/bold cyan]", border_style="cyan"))
    console.print("[dim]Use ↑↓ to navigate, ⏎ to select. Map ADO fields to canonical field names.[/dim]")
    console.print()

    new_mapping: dict[str, str] = {}

    # Build choice list with display names
    field_choices_display: list[str] = ["<no mapping>"]
    field_choices_refs: list[str] = ["<no mapping>"]
    for field in relevant_fields:
        ref_name = field.get("referenceName", "")
        name = field.get("name", ref_name)
        display = f"{ref_name} ({name})"
        field_choices_display.append(display)
        field_choices_refs.append(ref_name)

    for canonical_field, display_name in canonical_fields.items():
        # Find current mapping (existing > default)
        current_ado_fields = [
            ado_field for ado_field, canonical in combined_mapping.items() if canonical == canonical_field
        ]

        # Determine default selection
        default_selection = "<no mapping>"
        if current_ado_fields:
            # Find the current mapping in the choices list
            current_ref = current_ado_fields[0]
            if current_ref in field_choices_refs:
                default_selection = field_choices_display[field_choices_refs.index(current_ref)]
            else:
                # If current mapping not in available fields, use "<no mapping>"
                default_selection = "<no mapping>"

        # Use interactive selection menu with questionary
        console.print(f"[bold]{display_name}[/bold] (canonical: {canonical_field})")
        if current_ado_fields:
            console.print(f"[dim]Current: {', '.join(current_ado_fields)}[/dim]")
        else:
            console.print("[dim]Current: <no mapping>[/dim]")

        # Find default index
        default_index = 0
        if default_selection != "<no mapping>" and default_selection in field_choices_display:
            default_index = field_choices_display.index(default_selection)

        # Use questionary for interactive selection with arrow keys
        try:
            selected_display = questionary.select(
                f"Select ADO field for {display_name}",
                choices=field_choices_display,
                default=field_choices_display[default_index] if default_index < len(field_choices_display) else None,
                use_arrow_keys=True,
                use_jk_keys=False,
            ).ask()
            if selected_display is None:
                selected_display = "<no mapping>"
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Selection cancelled.[/yellow]")
            raise typer.Exit(0) from None

        # Convert display name back to reference name
        if selected_display and selected_display != "<no mapping>" and selected_display in field_choices_display:
            selected_ref = field_choices_refs[field_choices_display.index(selected_display)]
            new_mapping[selected_ref] = canonical_field

        console.print()

    # Validate mapping
    console.print("[cyan]Validating mapping...[/cyan]")
    duplicate_ado_fields = {}
    for ado_field, canonical in new_mapping.items():
        if ado_field in duplicate_ado_fields:
            duplicate_ado_fields[ado_field].append(canonical)
        else:
            # Check if this ADO field is already mapped to a different canonical field
            for other_ado, other_canonical in new_mapping.items():
                if other_ado == ado_field and other_canonical != canonical:
                    if ado_field not in duplicate_ado_fields:
                        duplicate_ado_fields[ado_field] = []
                    duplicate_ado_fields[ado_field].extend([canonical, other_canonical])

    if duplicate_ado_fields:
        console.print("[yellow]⚠[/yellow] Warning: Some ADO fields are mapped to multiple canonical fields:")
        for ado_field, canonicals in duplicate_ado_fields.items():
            console.print(f"  {ado_field}: {', '.join(set(canonicals))}")
        if not Confirm.ask("Continue anyway?", default=False):
            console.print("[yellow]Mapping cancelled.[/yellow]")
            raise typer.Exit(0)

    # Merge with existing mapping (new mapping takes precedence)
    final_mapping = existing_mapping.copy()
    final_mapping.update(new_mapping)

    # Preserve existing work_item_type_mappings if they exist
    # This prevents erasing custom work item type mappings when updating field mappings
    work_item_type_mappings = existing_work_item_type_mappings.copy() if existing_work_item_type_mappings else {}

    # Create FieldMappingConfig
    config = FieldMappingConfig(
        framework=existing_config.framework if existing_config else "default",
        field_mappings=final_mapping,
        work_item_type_mappings=work_item_type_mappings,
    )

    # Save to file
    custom_mapping_file.parent.mkdir(parents=True, exist_ok=True)
    with custom_mapping_file.open("w", encoding="utf-8") as f:
        yaml.dump(config.model_dump(), f, default_flow_style=False, sort_keys=False)

    console.print()
    console.print(Panel("[bold green]✓ Mapping saved successfully[/bold green]", border_style="green"))
    console.print(f"[green]Location:[/green] {custom_mapping_file}")
    console.print()
    console.print("[dim]You can now use this mapping with specfact backlog refine.[/dim]")
