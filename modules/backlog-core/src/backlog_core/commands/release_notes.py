"""Backlog release notes generation command."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer
from beartype import beartype

from specfact_cli.utils.prompts import print_success

from .shared import fetch_current_graph


DONE_STATES = {"done", "completed", "closed", "resolved"}


@beartype
def _default_output_path() -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return Path(".specfact/release-notes") / f"release-notes-{timestamp}.md"


@beartype
def _render_release_notes(project_id: str, adapter: str, done_items: list[tuple[str, str, str]]) -> str:
    lines = [
        "# Release Notes",
        "",
        f"- Project: {project_id}",
        f"- Adapter: {adapter}",
        f"- Generated: {datetime.now(UTC).isoformat()}",
        "",
        "## Completed Items",
        "",
    ]
    if not done_items:
        lines.append("- No completed items found.")
    else:
        for item_id, key, title in done_items:
            lines.append(f"- {key or item_id}: {title}")
    lines.append("")
    return "\n".join(lines)


@beartype
def generate_release_notes(
    project_id: Annotated[str, typer.Option("--project-id", help="Backlog project identifier")],
    adapter: Annotated[str, typer.Option("--adapter", help="Adapter to use")] = "github",
    output: Annotated[Path | None, typer.Option("--output", help="Release notes markdown output path")] = None,
    template: Annotated[str, typer.Option("--template", help="Template name for mapping")] = "github_projects",
) -> None:
    """Generate release notes from completed backlog items."""
    graph = fetch_current_graph(project_id, adapter, template)
    done_items = [
        (item.id, item.key, item.title) for item in graph.items.values() if item.status.lower().strip() in DONE_STATES
    ]
    done_items.sort(key=lambda row: row[1] or row[0])

    output_path = output or _default_output_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_render_release_notes(project_id, adapter, done_items), encoding="utf-8")
    print_success(f"Release notes written: {output_path}")
