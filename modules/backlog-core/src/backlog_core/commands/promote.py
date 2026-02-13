"""Backlog promote command."""

from __future__ import annotations

from typing import Annotated

import typer
from beartype import beartype

from backlog_core.analyzers.dependency import DependencyAnalyzer
from specfact_cli.utils.prompts import print_info, print_success, print_warning

from .shared import fetch_current_graph


@beartype
def promote(
    project_id: Annotated[str, typer.Option("--project-id", help="Backlog project identifier")],
    item_id: Annotated[str, typer.Option("--item-id", help="Item id to promote")],
    to_status: Annotated[str, typer.Option("--to-status", help="Target workflow status")],
    adapter: Annotated[str, typer.Option("--adapter", help="Adapter to use")] = "github",
    template: Annotated[str, typer.Option("--template", help="Template name for mapping")] = "github_projects",
) -> None:
    """Validate promotion impact for an item and print promotion intent."""
    graph = fetch_current_graph(project_id, adapter, template)
    item = graph.items.get(item_id)
    if item is None:
        print_warning(f"Item '{item_id}' not found in graph.")
        raise typer.Exit(code=1)

    analyzer = DependencyAnalyzer(graph)
    impact = analyzer.impact_analysis(item_id)
    blockers = impact["blockers"]
    if blockers:
        print_warning(f"Item '{item_id}' has blockers: {', '.join(blockers)}")

    print_info(f"Promote item '{item_id}' from '{item.status}' to '{to_status}'")
    print_info(f"Downstream impact count: {impact['estimated_impact_count']}")
    if blockers:
        raise typer.Exit(code=1)
    print_success("Promotion validation passed.")
