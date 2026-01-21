"""
Base classes and utilities for backlog adapters.

This module provides reusable patterns and abstractions for implementing backlog
adapters (GitHub, Azure DevOps, Jira, Linear, etc.) that support bidirectional
sync between backlog management tools and OpenSpec change proposals.

All backlog adapters should inherit from BacklogAdapterMixin to get common
functionality for status mapping, metadata extraction, and conflict resolution.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.change import ChangeProposal
from specfact_cli.models.source_tracking import SourceTracking


class BacklogAdapterMixin(ABC):
    """
    Mixin class providing common functionality for backlog adapters.

    This mixin provides tool-agnostic patterns for:
    - Status mapping (backlog status ↔ OpenSpec status)
    - Metadata extraction (backlog item → change proposal)
    - Conflict resolution (when status differs)

    Future backlog adapters (ADO, Jira, Linear) should inherit from this mixin
    and implement the abstract methods to provide tool-specific implementations.
    """

    @abstractmethod
    @beartype
    @require(lambda status: isinstance(status, str) and len(status) > 0, "Status must be non-empty string")
    @ensure(lambda result: isinstance(result, str) and len(result) > 0, "Must return non-empty status string")
    def map_backlog_status_to_openspec(self, status: str) -> str:
        """
        Map backlog tool status to OpenSpec change status.

        Args:
            status: Backlog tool status (e.g., GitHub label, ADO state, Jira status, Linear state)

        Returns:
            OpenSpec change status (proposed, in-progress, applied, deprecated, discarded)

        Note:
            This method must be implemented by each backlog adapter to provide
            tool-specific status mapping logic.
        """

    @abstractmethod
    @beartype
    @require(lambda status: isinstance(status, str) and len(status) > 0, "Status must be non-empty string")
    @ensure(lambda result: isinstance(result, (str, list)), "Must return status string or list of status strings")
    def map_openspec_status_to_backlog(self, status: str) -> str | list[str]:
        """
        Map OpenSpec change status to backlog tool status.

        Args:
            status: OpenSpec change status (proposed, in-progress, applied, deprecated, discarded)

        Returns:
            Backlog tool status (e.g., GitHub label, ADO state, Jira status, Linear state)
            or list of status strings for tools that support multiple status indicators

        Note:
            This method must be implemented by each backlog adapter to provide
            tool-specific status mapping logic.
        """

    @beartype
    @require(
        lambda source_state: isinstance(source_state, str) and len(source_state) > 0,
        "Source state must be non-empty string",
    )
    @require(
        lambda source_adapter_type: isinstance(source_adapter_type, str) and len(source_adapter_type) > 0,
        "Source adapter type must be non-empty string",
    )
    @require(
        lambda target_adapter: isinstance(target_adapter, BacklogAdapterMixin),
        "Target adapter must implement BacklogAdapterMixin",
    )
    @ensure(lambda result: isinstance(result, str), "Must return status string")
    def map_backlog_state_between_adapters(
        self, source_state: str, source_adapter_type: str, target_adapter: BacklogAdapterMixin
    ) -> str:
        """
        Map backlog state from one adapter to another using OpenSpec as intermediate format.

        This method provides generic cross-adapter state mapping by:
        1. Getting the source adapter instance
        2. Mapping source state to OpenSpec status using source adapter's mapping
        3. Mapping OpenSpec status to target state using target adapter's mapping

        Args:
            source_state: State from source adapter (e.g., "open", "closed", "New", "Active")
            source_adapter_type: Source adapter type (e.g., "github", "ado", "jira")
            target_adapter: Target adapter instance (must implement BacklogAdapterMixin)

        Returns:
            Target adapter state string

        Note:
            This is a generic method that works for any adapter pair by using OpenSpec
            as the intermediate format. It requires the source adapter to be registered
            in AdapterRegistry to retrieve its mapping methods.
        """
        from specfact_cli.adapters.registry import AdapterRegistry

        # Get source adapter instance to use its mapping methods
        source_adapter = AdapterRegistry.get_adapter(source_adapter_type)
        if not source_adapter or not isinstance(source_adapter, BacklogAdapterMixin):
            # Fallback: if source adapter not found, try to map directly
            # This handles cases where source adapter might not be registered
            # In this case, we'll use the target adapter's default mapping
            openspec_status = "proposed"  # Default fallback
        else:
            # Step 1: Map source state to OpenSpec status using source adapter
            openspec_status = source_adapter.map_backlog_status_to_openspec(source_state)

        # Step 2: Map OpenSpec status to target state using target adapter
        # Special handling for GitHub adapter: use issue state method instead of labels
        if hasattr(target_adapter, "map_openspec_status_to_issue_state"):
            # GitHub adapter: use issue state mapping (open/closed)
            return target_adapter.map_openspec_status_to_issue_state(openspec_status)

        target_state = target_adapter.map_openspec_status_to_backlog(openspec_status)

        # Handle list return type (some adapters return lists)
        if isinstance(target_state, list):
            # Use first element if list (typically the primary state)
            return target_state[0] if target_state else "New"

        return target_state

    @abstractmethod
    @beartype
    @require(lambda item_data: isinstance(item_data, dict), "Item data must be dict")
    @ensure(lambda result: isinstance(result, dict), "Must return dict with extracted fields")
    def extract_change_proposal_data(self, item_data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract change proposal data from backlog item.

        Args:
            item_data: Backlog item data (e.g., GitHub issue dict, ADO work item dict, Jira issue dict, Linear issue dict)

        Returns:
            Dict with change proposal fields:
            - title: str
            - description: str (What Changes section)
            - rationale: str (Why section)
            - status: str (mapped to OpenSpec status)
            - Other optional fields (timeline, owner, stakeholders, dependencies)

        Raises:
            ValueError: If required fields are missing or data is malformed

        Note:
            This method must be implemented by each backlog adapter to parse
            tool-specific data formats (GitHub issue body, ADO work item fields, etc.).
        """

    @beartype
    @require(lambda item_data: isinstance(item_data, dict), "Item data must be dict")
    @require(lambda tool_name: isinstance(tool_name, str) and len(tool_name) > 0, "Tool name must be non-empty")
    @ensure(lambda result: isinstance(result, SourceTracking), "Must return SourceTracking")
    def create_source_tracking(
        self, item_data: dict[str, Any], tool_name: str, bridge_config: Any = None
    ) -> SourceTracking:
        """
        Create SourceTracking from backlog item metadata.

        This is a reusable utility method that all backlog adapters can use
        to store tool-specific metadata in source_tracking.

        Args:
            item_data: Backlog item data with metadata (ID, URL, status, assignees, etc.)
            tool_name: Tool identifier (e.g., "github", "ado", "jira", "linear")
            bridge_config: Optional bridge configuration (for cross-repo support)

        Returns:
            SourceTracking instance with tool-specific metadata stored in source_metadata

        Note:
            This method provides a common pattern for storing backlog item metadata.
            Each adapter should call this method and add tool-specific fields to source_metadata.
        """
        source_metadata: dict[str, Any] = {}

        # Extract common fields (ID, URL) if present
        source_id = None
        if tool_name.lower() == "github":
            source_id = item_data.get("number") or item_data.get("id")
            # GitHub: convert to string for consistency (GitHub issue numbers are strings)
            if source_id is not None:
                source_metadata["source_id"] = str(source_id)
        else:
            # For ADO and other adapters: preserve original type
            # ADO work item IDs are integers, so keep as int
            source_id = item_data.get("id") or item_data.get("number")
            if source_id is not None:
                source_metadata["source_id"] = source_id
        # Prefer html_url (user-friendly) over url (API URL)
        if "html_url" in item_data:
            source_metadata["source_url"] = item_data.get("html_url")
        elif "url" in item_data:
            source_metadata["source_url"] = item_data.get("url")
        if "state" in item_data:
            source_metadata["source_state"] = item_data.get("state")
        if "assignees" in item_data or "assignee" in item_data:
            assignees = item_data.get("assignees", [])
            if not assignees and "assignee" in item_data:
                assignees = [item_data["assignee"]] if item_data["assignee"] else []
            source_metadata["assignees"] = assignees

        # Add cross-repo support if bridge_config has external_base_path
        if bridge_config and hasattr(bridge_config, "external_base_path") and bridge_config.external_base_path:
            source_metadata["external_base_path"] = str(bridge_config.external_base_path)

        return SourceTracking(tool=tool_name, source_metadata=source_metadata)

    @beartype
    @require(
        lambda openspec_status: isinstance(openspec_status, str) and len(openspec_status) > 0,
        "Status must be non-empty",
    )
    @require(
        lambda backlog_status: isinstance(backlog_status, str) and len(backlog_status) > 0, "Status must be non-empty"
    )
    @ensure(lambda result: isinstance(result, str), "Must return conflict resolution strategy name")
    def resolve_status_conflict(
        self, openspec_status: str, backlog_status: str, strategy: str = "prefer_openspec"
    ) -> str:
        """
        Resolve status conflict when OpenSpec and backlog status differ.

        Args:
            openspec_status: OpenSpec change status
            backlog_status: Backlog tool status (mapped to OpenSpec format)
            strategy: Conflict resolution strategy:
                - "prefer_openspec": Use OpenSpec status (default)
                - "prefer_backlog": Use backlog status
                - "merge": Use most advanced status (in-progress > proposed, applied > in-progress)

        Returns:
            Resolved status (OpenSpec format)

        Note:
            This provides a reusable conflict resolution pattern that all backlog
            adapters can use. The default strategy prefers OpenSpec as the source of truth.
        """
        if openspec_status == backlog_status:
            return openspec_status

        if strategy == "prefer_openspec":
            return openspec_status
        if strategy == "prefer_backlog":
            return backlog_status
        if strategy == "merge":
            # Status priority: applied > in-progress > proposed > deprecated > discarded
            status_priority = {
                "applied": 5,
                "in-progress": 4,
                "proposed": 3,
                "deprecated": 2,
                "discarded": 1,
            }
            openspec_priority = status_priority.get(openspec_status, 0)
            backlog_priority = status_priority.get(backlog_status, 0)
            return openspec_status if openspec_priority >= backlog_priority else backlog_status

        # Default: prefer OpenSpec
        return openspec_status

    @beartype
    @require(lambda item_data: isinstance(item_data, dict), "Item data must be dict")
    @require(lambda tool_name: isinstance(tool_name, str) and len(tool_name) > 0, "Tool name must be non-empty")
    @ensure(lambda result: isinstance(result, ChangeProposal) or result is None, "Must return ChangeProposal or None")
    def import_backlog_item_as_proposal(
        self, item_data: dict[str, Any], tool_name: str, bridge_config: Any = None
    ) -> ChangeProposal | None:
        """
        Import backlog item as OpenSpec change proposal (reusable pattern).

        This method provides a common workflow that all backlog adapters can use:
        1. Extract change proposal data from backlog item
        2. Map backlog status to OpenSpec status
        3. Create SourceTracking with tool-specific metadata
        4. Create ChangeProposal instance

        Args:
            item_data: Backlog item data (tool-specific format)
            tool_name: Tool identifier (e.g., "github", "ado", "jira", "linear")
            bridge_config: Optional bridge configuration (for cross-repo support)

        Returns:
            ChangeProposal instance if successful, None if data is invalid

        Raises:
            ValueError: If required fields are missing or data is malformed

        Note:
            This method implements the common import pattern. Each backlog adapter
            should call this method after implementing extract_change_proposal_data()
            and map_backlog_status_to_openspec().
        """
        try:
            # Extract change proposal data (tool-specific parsing)
            proposal_data = self.extract_change_proposal_data(item_data)

            # Get status from extracted data or map from backlog item
            if "status" in proposal_data:
                openspec_status = proposal_data["status"]
            else:
                # Map backlog status to OpenSpec status
                backlog_status = item_data.get("state") or item_data.get("status") or "open"
                openspec_status = self.map_backlog_status_to_openspec(backlog_status)

            # Create source tracking
            source_tracking = self.create_source_tracking(item_data, tool_name, bridge_config)

            # Create change proposal
            change_id = proposal_data.get("change_id") or item_data.get("id") or item_data.get("number") or "unknown"
            return ChangeProposal(
                name=change_id,
                title=proposal_data.get("title", "Untitled Change Proposal"),
                description=proposal_data.get("description", ""),
                rationale=proposal_data.get("rationale", ""),
                timeline=proposal_data.get("timeline"),
                owner=proposal_data.get("owner"),
                stakeholders=proposal_data.get("stakeholders", []),
                dependencies=proposal_data.get("dependencies", []),
                status=openspec_status,
                created_at=proposal_data.get("created_at") or datetime.now(UTC).isoformat(),
                applied_at=proposal_data.get("applied_at"),
                archived_at=proposal_data.get("archived_at"),
                source_tracking=source_tracking,
            )
        except (KeyError, ValueError, TypeError) as e:
            msg = f"Failed to import backlog item as change proposal: {e}"
            raise ValueError(msg) from e
