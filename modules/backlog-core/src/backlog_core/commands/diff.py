"""Backlog diff command."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from beartype import beartype
from rich.console import Console
from rich.table import Table

from backlog_core.commands.sync import compute_delta
from backlog_core.graph.models import BacklogGraph
from specfact_cli.utils.prompts import print_warning

from .shared import fetch_current_graph


console = Console()


@beartype
def _load_baseline_graph(baseline_file: Path) -> BacklogGraph:
    if not baseline_file.exists():
        return BacklogGraph(provider="unknown", project_key="unknown")
    return BacklogGraph.from_json(baseline_file.read_text(encoding="utf-8"))


@beartype
def _render_diff(delta: dict[str, object]) -> None:
    table = Table(title="Backlog Diff")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="green")
    table.add_row("Added items", str(len(delta["added_items"])))
    table.add_row("Updated items", str(len(delta["updated_items"])))
    table.add_row("Removed items", str(len(delta["removed_items"])))
    table.add_row("Status transitions", str(len(delta["status_transitions"])))
    table.add_row("New dependencies", str(len(delta["new_dependencies"])))
    table.add_row("Removed dependencies", str(len(delta["removed_dependencies"])))
    console.print(table)


@beartype
def diff(
    project_id: Annotated[str, typer.Option("--project-id", help="Backlog project identifier")],
    adapter: Annotated[str, typer.Option("--adapter", help="Adapter to use")] = "github",
    baseline_file: Annotated[Path, typer.Option("--baseline-file", help="Path to baseline graph JSON")] = Path(
        ".specfact/backlog-baseline.json"
    ),
    template: Annotated[str, typer.Option("--template", help="Template name for mapping")] = "github_projects",
) -> None:
    """Show changes since baseline sync."""
    if not baseline_file.exists():
        print_warning(f"Baseline file not found: {baseline_file}. Comparing against empty baseline.")
    baseline_graph = _load_baseline_graph(baseline_file)
    current_graph = fetch_current_graph(project_id, adapter, template)
    delta = compute_delta(baseline_graph, current_graph)
    _render_diff(delta)
