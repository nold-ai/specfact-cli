"""Release readiness verification command."""

from __future__ import annotations

from typing import Annotated

import typer
from beartype import beartype
from rich.console import Console
from rich.panel import Panel

from backlog_core.adapters.backlog_protocol import require_backlog_graph_protocol
from backlog_core.analyzers.dependency import DependencyAnalyzer
from backlog_core.graph.builder import BacklogGraphBuilder
from backlog_core.graph.models import DependencyType
from specfact_cli.adapters.registry import AdapterRegistry
from specfact_cli.utils.prompts import print_warning


console = Console()
DONE_STATES = {"done", "completed", "closed", "resolved"}
KNOWN_STATES = {"todo", "new", "planned", "in_progress", "active", "blocked", "open", *DONE_STATES}


@beartype
def _fetch_graph(project_id: str, adapter: str, template: str):
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
def verify_readiness(
    project_id: Annotated[str, typer.Option("--project-id", help="Backlog project identifier")],
    adapter: Annotated[str, typer.Option("--adapter", help="Adapter to use")] = "github",
    target_items: Annotated[str, typer.Option("--target-items", help="Comma-separated item ids to verify")] = "",
    template: Annotated[str, typer.Option("--template", help="Template name for mapping")] = "github_projects",
) -> None:
    """Verify release readiness for selected backlog items."""
    graph = _fetch_graph(project_id, adapter, template)
    analyzer = DependencyAnalyzer(graph)
    target_ids = [x.strip() for x in target_items.split(",") if x.strip()]
    if not target_ids:
        target_ids = sorted(graph.items.keys())

    findings: list[str] = []

    cycles = analyzer.detect_cycles()
    if cycles:
        findings.append(f"Circular dependencies detected ({len(cycles)} cycles).")

    for item_id in target_ids:
        if item_id not in graph.items:
            findings.append(f"Target item '{item_id}' not found.")
            continue

        impact = analyzer.impact_analysis(item_id)
        if impact["blockers"]:
            findings.append(f"Item '{item_id}' has blockers: {', '.join(impact['blockers'])}.")

        # Status transition/readiness sanity: unknown states are treated as not release-ready.
        current_status = graph.items[item_id].status.lower().strip()
        if current_status not in KNOWN_STATES:
            findings.append(f"Item '{item_id}' has unrecognized status '{graph.items[item_id].status}'.")

    parent_to_children: dict[str, list[str]] = {}
    for dep in graph.dependencies:
        if dep.type != DependencyType.PARENT_CHILD:
            continue
        parent_to_children.setdefault(dep.source_id, []).append(dep.target_id)

    for parent_id, children in parent_to_children.items():
        parent = graph.items.get(parent_id)
        if parent is None:
            continue
        if parent.status.lower() not in DONE_STATES:
            continue
        not_done_children = [
            child
            for child in children
            if graph.items.get(child) and graph.items[child].status.lower() not in DONE_STATES
        ]
        if not_done_children:
            findings.append(
                f"Parent '{parent_id}' is in completed state but children not completed: {', '.join(sorted(not_done_children))}."
            )

    ready = len(findings) == 0
    if ready:
        console.print(Panel("Release readiness: READY", style="green"))
        raise typer.Exit(code=0)

    for finding in findings:
        print_warning(finding)
    console.print(Panel("Release readiness: BLOCKED", style="red"))
    raise typer.Exit(code=1)
