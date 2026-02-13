"""Backlog dependency analysis commands."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import typer
import yaml
from beartype import beartype
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from backlog_core.adapters.backlog_protocol import require_backlog_graph_protocol
from backlog_core.analyzers.dependency import DependencyAnalyzer
from backlog_core.graph.builder import BacklogGraphBuilder
from backlog_core.graph.models import BacklogGraph
from specfact_cli.adapters.registry import AdapterRegistry
from specfact_cli.utils.prompts import print_info, print_success, print_warning


console = Console()


@beartype
def _load_custom_config(custom_config: Path | None) -> dict[str, Any]:
    if custom_config is None:
        return {}
    if not custom_config.exists():
        raise ValueError(f"Custom config file not found: {custom_config}")
    loaded = yaml.safe_load(custom_config.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


@beartype
def _compute_graph(
    project_id: str,
    adapter: str,
    template: str,
    custom_config: Path | None,
) -> tuple[BacklogGraph, DependencyAnalyzer]:
    adapter_instance = AdapterRegistry.get_adapter(adapter)
    graph_adapter = require_backlog_graph_protocol(adapter_instance)

    custom = _load_custom_config(custom_config)
    items = graph_adapter.fetch_all_issues(project_id, filters=custom.get("filters"))
    relationships = graph_adapter.fetch_relationships(project_id)

    builder = BacklogGraphBuilder(
        provider=adapter,
        template_name=template,
        custom_config={**custom, "project_key": project_id},
    )
    graph = builder.add_items(items).add_dependencies(relationships).build()
    analyzer = DependencyAnalyzer(graph)
    return graph, analyzer


@beartype
def export_graph_json(graph: BacklogGraph, export_path: Path) -> None:
    """Export graph as JSON."""
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_text(graph.to_json(), encoding="utf-8")


@beartype
def generate_dependency_report(graph: BacklogGraph, analyzer: DependencyAnalyzer) -> str:
    """Render dependency analysis summary in rich tables and return markdown summary."""
    cycles = analyzer.detect_cycles()
    critical_path = analyzer.critical_path()
    coverage = analyzer.coverage_analysis()

    summary = Table(title="Dependency Analysis Summary")
    summary.add_column("Metric", style="cyan")
    summary.add_column("Value", style="green")
    summary.add_row("Provider", graph.provider)
    summary.add_row("Project", graph.project_key)
    summary.add_row("Items", str(len(graph.items)))
    summary.add_row("Dependencies", str(len(graph.dependencies)))
    summary.add_row("Cycles", str(len(cycles)))
    summary.add_row("Orphans", str(len(graph.orphans)))
    summary.add_row("Critical Path Length", str(len(critical_path)))
    summary.add_row("Typed Coverage", f"{coverage['properly_typed_pct']}%")

    console.print(Panel("Dependency Graph Analysis", border_style="blue"))
    console.print(summary)

    markdown_lines = [
        "# Dependency Analysis",
        "",
        f"- Provider: {graph.provider}",
        f"- Project: {graph.project_key}",
        f"- Items: {len(graph.items)}",
        f"- Dependencies: {len(graph.dependencies)}",
        f"- Cycles: {len(cycles)}",
        f"- Orphans: {len(graph.orphans)}",
        f"- Critical path: {' -> '.join(critical_path) if critical_path else '(none)'}",
        f"- Typed coverage: {coverage['properly_typed_pct']}%",
    ]
    return "\n".join(markdown_lines) + "\n"


@beartype
def analyze_deps(
    project_id: Annotated[str, typer.Option("--project-id", help="Backlog project identifier")],
    adapter: Annotated[str, typer.Option("--adapter", help="Adapter to use")] = "github",
    template: Annotated[str, typer.Option("--template", help="Template name for mapping")] = "github_projects",
    custom_config: Annotated[Path | None, typer.Option("--custom-config", help="Path to custom mapping YAML")] = None,
    output: Annotated[Path | None, typer.Option("--output", help="Optional markdown report output path")] = None,
    json_export: Annotated[Path | None, typer.Option("--json-export", help="Optional graph JSON export path")] = None,
) -> None:
    """Analyze backlog dependencies for a project."""
    graph, analyzer = _compute_graph(project_id, adapter, template, custom_config)

    report_markdown = generate_dependency_report(graph, analyzer)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report_markdown, encoding="utf-8")
        print_success(f"Dependency report written to {output}")

    if json_export is not None:
        export_graph_json(graph, json_export)
        print_success(f"Dependency graph JSON exported to {json_export}")


@beartype
def trace_impact(
    item_id: Annotated[str, typer.Argument(help="Item ID to analyze")],
    project_id: Annotated[str, typer.Option("--project-id", help="Backlog project identifier")],
    adapter: Annotated[str, typer.Option("--adapter", help="Adapter to use")] = "github",
    template: Annotated[str, typer.Option("--template", help="Template name for mapping")] = "github_projects",
    custom_config: Annotated[Path | None, typer.Option("--custom-config", help="Path to custom mapping YAML")] = None,
) -> None:
    """Trace downstream impact for a backlog item."""
    graph, analyzer = _compute_graph(project_id, adapter, template, custom_config)

    if item_id not in graph.items:
        print_warning(f"Item '{item_id}' not found in graph")
        raise typer.Exit(code=1)

    impact = analyzer.impact_analysis(item_id)
    print_info(f"Direct dependents: {', '.join(impact['direct_dependents']) or '(none)'}")
    print_info(f"Transitive dependents: {', '.join(impact['transitive_dependents']) or '(none)'}")
    print_info(f"Blockers: {', '.join(impact['blockers']) or '(none)'}")
    print_success(f"Estimated impact count: {impact['estimated_impact_count']}")
