"""Backlog sync command and delta utilities."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

import typer
import yaml
from beartype import beartype
from rich.console import Console
from rich.table import Table

from backlog_core.adapters.backlog_protocol import require_backlog_graph_protocol
from backlog_core.graph.builder import BacklogGraphBuilder
from backlog_core.graph.models import BacklogGraph
from specfact_cli.adapters.registry import AdapterRegistry
from specfact_cli.utils.prompts import print_info, print_success, print_warning


console = Console()


@beartype
def _load_baseline_graph(baseline_file: Path) -> BacklogGraph:
    if not baseline_file.exists():
        return BacklogGraph(provider="unknown", project_key="unknown")
    return BacklogGraph.from_json(baseline_file.read_text(encoding="utf-8"))


@beartype
def _fetch_current_graph(
    project_id: str,
    adapter: str,
    template: str,
) -> BacklogGraph:
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
def compute_delta(baseline_graph: BacklogGraph, current_graph: BacklogGraph) -> dict[str, Any]:
    baseline_ids = set(baseline_graph.items.keys())
    current_ids = set(current_graph.items.keys())

    added_items = sorted(current_ids - baseline_ids)
    removed_items = sorted(baseline_ids - current_ids)
    common_ids = baseline_ids & current_ids

    updated_items: list[str] = []
    status_transitions: list[dict[str, str]] = []
    for item_id in sorted(common_ids):
        old_item = baseline_graph.items[item_id]
        new_item = current_graph.items[item_id]
        if old_item.model_dump(exclude={"raw_data"}) != new_item.model_dump(exclude={"raw_data"}):
            updated_items.append(item_id)
        if old_item.status != new_item.status:
            status_transitions.append({"id": item_id, "from": old_item.status, "to": new_item.status})

    baseline_edges = {(dep.source_id, dep.target_id, dep.type.value) for dep in baseline_graph.dependencies}
    current_edges = {(dep.source_id, dep.target_id, dep.type.value) for dep in current_graph.dependencies}

    return {
        "added_items": added_items,
        "removed_items": removed_items,
        "updated_items": updated_items,
        "status_transitions": status_transitions,
        "new_dependencies": sorted(current_edges - baseline_edges),
        "removed_dependencies": sorted(baseline_edges - current_edges),
    }


@beartype
class BacklogGraphToPlanBundle:
    """Convert backlog sync state into a plan-bundle-shaped payload."""

    @beartype
    def convert(
        self,
        graph: BacklogGraph,
        delta: dict[str, Any],
        project_id: str,
        adapter: str,
    ) -> dict[str, Any]:
        return {
            "bundle_name": f"backlog-sync-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}",
            "metadata": {
                "generated_at": datetime.now(UTC).isoformat(),
                "source": {"project_id": project_id, "adapter": adapter},
                "delta_summary": {
                    "added": len(delta["added_items"]),
                    "updated": len(delta["updated_items"]),
                    "removed": len(delta["removed_items"]),
                    "new_dependencies": len(delta["new_dependencies"]),
                },
            },
            "backlog_graph": graph.model_dump(mode="json"),
        }


@beartype
def _render_delta_summary(delta: dict[str, Any]) -> None:
    table = Table(title="Backlog Sync Delta")
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
def sync(
    project_id: Annotated[str, typer.Option("--project-id", help="Backlog project identifier")],
    adapter: Annotated[str, typer.Option("--adapter", help="Adapter to use")] = "github",
    baseline_file: Annotated[Path, typer.Option("--baseline-file", help="Path to baseline graph JSON")] = Path(
        ".specfact/backlog-baseline.json"
    ),
    output_format: Annotated[str, typer.Option("--output-format", help="Output format: plan|json")] = "plan",
    template: Annotated[str, typer.Option("--template", help="Template name for mapping")] = "github_projects",
) -> None:
    """Sync current backlog graph with stored baseline and export delta outputs."""
    if output_format not in {"plan", "json"}:
        print_warning(f"Unsupported output format '{output_format}'. Use 'plan' or 'json'.")
        raise typer.Exit(code=1)

    baseline_graph = _load_baseline_graph(baseline_file)
    current_graph = _fetch_current_graph(project_id, adapter, template)
    delta = compute_delta(baseline_graph, current_graph)

    _render_delta_summary(delta)

    baseline_file.parent.mkdir(parents=True, exist_ok=True)
    baseline_file.write_text(current_graph.to_json(), encoding="utf-8")
    print_success(f"Updated baseline graph: {baseline_file}")

    if output_format == "plan":
        converter = BacklogGraphToPlanBundle()
        bundle_payload = converter.convert(current_graph, delta, project_id, adapter)
        plans_dir = Path(".specfact/plans")
        plans_dir.mkdir(parents=True, exist_ok=True)
        output_path = plans_dir / f"backlog-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}.yaml"
        output_path.write_text(yaml.safe_dump(bundle_payload, sort_keys=False), encoding="utf-8")
        print_success(f"Plan bundle written: {output_path}")
    else:
        print_info("JSON output selected: baseline file contains current graph snapshot.")
