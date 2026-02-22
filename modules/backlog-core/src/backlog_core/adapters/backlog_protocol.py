"""Bridge protocol for backlog graph-capable adapters."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from beartype import beartype
from icontract import ensure, require

from specfact_cli.registry.bridge_registry import BRIDGE_PROTOCOL_REGISTRY


@runtime_checkable
class BacklogGraphProtocol(Protocol):
    """Protocol for bulk issue and relationship retrieval for graph analysis."""

    @beartype
    @require(lambda project_id: project_id.strip() != "", "project_id must be non-empty")
    @ensure(lambda result: isinstance(result, list), "fetch_all_issues must return list")
    def fetch_all_issues(self, project_id: str, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Fetch all backlog issues/work items for a project."""

    @beartype
    @require(lambda project_id: project_id.strip() != "", "project_id must be non-empty")
    @ensure(lambda result: isinstance(result, list), "fetch_relationships must return list")
    def fetch_relationships(self, project_id: str) -> list[dict[str, Any]]:
        """Fetch all issue/work-item relationships for a project."""

    @beartype
    @require(lambda project_id: project_id.strip() != "", "project_id must be non-empty")
    @require(lambda payload: isinstance(payload, dict), "payload must be dict")
    @ensure(lambda result: isinstance(result, dict), "create_issue must return dict")
    def create_issue(self, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a provider issue/work item and return id/key/url metadata."""


@beartype
@require(lambda adapter: adapter is not None, "adapter must be provided")
@ensure(lambda result: isinstance(result, BacklogGraphProtocol), "adapter must satisfy BacklogGraphProtocol")
def require_backlog_graph_protocol(adapter: Any) -> BacklogGraphProtocol:
    """Validate adapter protocol support and return typed protocol view."""
    if not isinstance(adapter, BacklogGraphProtocol):
        msg = (
            f"Adapter '{type(adapter).__name__}' does not support BacklogGraphProtocol. "
            "Expected methods: fetch_all_issues(project_id, filters), fetch_relationships(project_id), create_issue(project_id, payload)."
        )
        raise TypeError(msg)
    return adapter


BRIDGE_PROTOCOL_REGISTRY.register_protocol("backlog_graph", BacklogGraphProtocol)
