"""Shared command helpers for backlog-core command modules."""

from __future__ import annotations

from beartype import beartype

from backlog_core.adapters.backlog_protocol import require_backlog_graph_protocol
from backlog_core.graph.builder import BacklogGraphBuilder
from backlog_core.graph.models import BacklogGraph
from specfact_cli.adapters.registry import AdapterRegistry


@beartype
def fetch_current_graph(project_id: str, adapter: str, template: str) -> BacklogGraph:
    """Fetch and build the current backlog dependency graph."""
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
