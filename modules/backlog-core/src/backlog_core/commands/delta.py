"""Delta analysis subcommands for backlog-core."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Annotated, Any

import typer
from beartype import beartype
from rich.console import Console
from rich.table import Table

from backlog_core.adapters.backlog_protocol import require_backlog_graph_protocol
from backlog_core.analyzers.dependency import DependencyAnalyzer
from backlog_core.commands.sync import compute_delta
from backlog_core.graph.builder import BacklogGraphBuilder
from backlog_core.graph.models import BacklogGraph
from specfact_cli.adapters.registry import AdapterRegistry
from specfact_cli.utils.prompts import print_info, print_success, print_warning


console = Console()
delta_app = typer.Typer(name="delta", help="Backlog delta analysis and impact tracking")


@beartype
def _load_baseline_graph(baseline_file: Path) -> BacklogGraph:
    if not baseline_file.exists():
        return BacklogGraph(provider="unknown", project_key="unknown")
    return BacklogGraph.from_json(baseline_file.read_text(encoding="utf-8"))


@beartype
def _fetch_current_graph(project_id: str, adapter: str, template: str) -> BacklogGraph:
    adapter_instance = AdapterRegistry.get_adapter(adapter)
    graph_adapter = require_backlog_graph_protocol(adapter_instance)
    items = graph_adapter.fetch_all_issues(project_id)
    relationships = graph_adapter.fetch_relationships(project_id)
    return (
        BacklogGraphBuilder(provider=adapter, template_name=template, custom_config={"project_key": project_id})
        .add_items(items)
        .add_dependencies(relationships)
        .build()
    )


@beartype
def _empty_delta() -> dict[str, Any]:
    return {
        "added_items": [],
        "removed_items": [],
        "updated_items": [],
        "status_transitions": [],
        "new_dependencies": [],
        "removed_dependencies": [],
    }


@beartype
def _render_delta_table(delta: dict[str, Any], title: str = "Delta Status") -> None:
    table = Table(title=title)
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
def status(
    project_id: Annotated[str, typer.Option("--project-id", help="Backlog project identifier")],
    adapter: Annotated[str, typer.Option("--adapter", help="Adapter to use")] = "github",
    since: Annotated[str | None, typer.Option("--since", help="ISO timestamp filter")] = None,
    baseline_file: Annotated[Path, typer.Option("--baseline-file", help="Path to baseline graph JSON")] = Path(
        ".specfact/backlog-baseline.json"
    ),
    template: Annotated[str, typer.Option("--template", help="Template name for mapping")] = "github_projects",
) -> None:
    """Show backlog delta status compared to baseline."""
    baseline_graph = _load_baseline_graph(baseline_file)
    current_graph = _fetch_current_graph(project_id, adapter, template)
    delta = compute_delta(baseline_graph, current_graph)

    if since is not None:
        try:
            since_dt = datetime.fromisoformat(since)
        except ValueError as exc:
            raise typer.BadParameter(f"Invalid --since timestamp: {since}") from exc
        if current_graph.fetched_at.replace(tzinfo=None) <= since_dt.replace(tzinfo=None):
            print_warning("No changes after --since timestamp.")
            delta = _empty_delta()

    _render_delta_table(delta, title="Backlog Delta Status")


@beartype
def impact(
    item_id: Annotated[str, typer.Argument(help="Item id to inspect")],
    project_id: Annotated[str, typer.Option("--project-id", help="Backlog project identifier")],
    adapter: Annotated[str, typer.Option("--adapter", help="Adapter to use")] = "github",
    template: Annotated[str, typer.Option("--template", help="Template name for mapping")] = "github_projects",
) -> None:
    """Show downstream dependency impact for an item."""
    graph = _fetch_current_graph(project_id, adapter, template)
    analyzer = DependencyAnalyzer(graph)
    if item_id not in graph.items:
        print_warning(f"Item '{item_id}' not found in graph.")
        raise typer.Exit(code=1)
    result = analyzer.impact_analysis(item_id)
    print_info(f"Direct dependents: {', '.join(result['direct_dependents']) or '(none)'}")
    print_info(f"Transitive dependents: {', '.join(result['transitive_dependents']) or '(none)'}")
    print_success(f"Estimated impact count: {result['estimated_impact_count']}")


@beartype
def cost_estimate(
    project_id: Annotated[str, typer.Option("--project-id", help="Backlog project identifier")],
    adapter: Annotated[str, typer.Option("--adapter", help="Adapter to use")] = "github",
    baseline_file: Annotated[Path, typer.Option("--baseline-file", help="Path to baseline graph JSON")] = Path(
        ".specfact/backlog-baseline.json"
    ),
    template: Annotated[str, typer.Option("--template", help="Template name for mapping")] = "github_projects",
) -> None:
    """Estimate effort based on detected delta volume."""
    baseline_graph = _load_baseline_graph(baseline_file)
    current_graph = _fetch_current_graph(project_id, adapter, template)
    delta = compute_delta(baseline_graph, current_graph)

    points = (
        len(delta["added_items"]) * 3
        + len(delta["updated_items"]) * 2
        + len(delta["removed_items"])
        + len(delta["new_dependencies"])
    )
    print_success(f"Estimated delta effort points: {points}")


@beartype
def rollback_analysis(
    project_id: Annotated[str, typer.Option("--project-id", help="Backlog project identifier")],
    adapter: Annotated[str, typer.Option("--adapter", help="Adapter to use")] = "github",
    baseline_file: Annotated[Path, typer.Option("--baseline-file", help="Path to baseline graph JSON")] = Path(
        ".specfact/backlog-baseline.json"
    ),
    template: Annotated[str, typer.Option("--template", help="Template name for mapping")] = "github_projects",
) -> None:
    """Analyze rollback exposure from current delta."""
    baseline_graph = _load_baseline_graph(baseline_file)
    current_graph = _fetch_current_graph(project_id, adapter, template)
    delta = compute_delta(baseline_graph, current_graph)

    high_risk = len(delta["removed_items"]) > 0 or len(delta["removed_dependencies"]) > 0
    risk = "HIGH" if high_risk else "LOW"
    print_info(f"Rollback risk: {risk}")
    _render_delta_table(delta, title="Rollback Impact")


delta_app.command("status")(status)
delta_app.command("impact")(impact)
delta_app.command("cost-estimate")(cost_estimate)
delta_app.command("rollback-analysis")(rollback_analysis)
