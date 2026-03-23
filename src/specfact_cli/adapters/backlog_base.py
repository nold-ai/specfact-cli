"""
Base classes and utilities for backlog adapters.

This module provides reusable patterns and abstractions for implementing backlog
adapters (GitHub, Azure DevOps, Jira, Linear, etc.) that support bidirectional
sync between backlog management tools and OpenSpec change proposals.

All backlog adapters should inherit from BacklogAdapterMixin to get common
functionality for status mapping, metadata extraction, and conflict resolution.
"""

from __future__ import annotations

import re
import time
from abc import ABC, abstractmethod
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, cast

import requests
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

    RETRYABLE_HTTP_STATUSES: tuple[int, ...] = (429, 500, 502, 503, 504)
    RETRY_DEFAULT_ATTEMPTS: int = 3
    RETRY_BACKOFF_SECONDS: float = 0.5

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
            return target_adapter.map_openspec_status_to_issue_state(openspec_status)  # type: ignore[attr-defined]

        target_state = target_adapter.map_openspec_status_to_backlog(openspec_status)

        # Handle list return type (some adapters return lists)
        if isinstance(target_state, list):
            # Use first element if list (typically the primary state)
            return target_state[0] if target_state else "New"

        return target_state

    @beartype
    @require(lambda attempts: attempts is None or attempts > 0, "attempts must be > 0 when provided")
    @require(
        lambda backoff_seconds: backoff_seconds is None or backoff_seconds >= 0,
        "backoff_seconds must be >= 0 when provided",
    )
    @require(
        lambda retry_on_ambiguous_transport: isinstance(retry_on_ambiguous_transport, bool), "retry flag must be bool"
    )
    @ensure(lambda result: hasattr(result, "raise_for_status"), "Result must support raise_for_status")
    def _request_with_retry(
        self,
        request_callable: Any,
        *,
        attempts: int | None = None,
        backoff_seconds: float | None = None,
        retry_on_ambiguous_transport: bool = True,
    ) -> Any:
        """Execute HTTP request with central retry policy for transient failures.

        For non-idempotent writes, callers can disable transport-error replay by passing
        retry_on_ambiguous_transport=False to avoid accidental duplicate side effects.
        """
        max_attempts = attempts or self.RETRY_DEFAULT_ATTEMPTS
        delay = backoff_seconds if backoff_seconds is not None else self.RETRY_BACKOFF_SECONDS

        last_error: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                response = request_callable()
                status_code = int(getattr(response, "status_code", 0) or 0)
                if self._should_retry_http_status(status_code, attempt, max_attempts):
                    self._backoff_sleep(delay, attempt)
                    continue
                response.raise_for_status()
                return response
            except requests.HTTPError as error:
                last_error = error
                if self._http_error_is_retryable_transient(error, attempt, max_attempts):
                    self._backoff_sleep(delay, attempt)
                    continue
                raise
            except (requests.Timeout, requests.ConnectionError) as error:
                last_error = error
                if retry_on_ambiguous_transport and attempt < max_attempts:
                    self._backoff_sleep(delay, attempt)
                    continue
                raise

        if last_error is not None:
            raise last_error
        raise RuntimeError("Retry logic failed without response or error")

    @staticmethod
    def _backoff_sleep(delay: float, attempt: int) -> None:
        time.sleep(delay * (2 ** (attempt - 1)))

    def _should_retry_http_status(self, status_code: int, attempt: int, max_attempts: int) -> bool:
        return status_code in self.RETRYABLE_HTTP_STATUSES and attempt < max_attempts

    def _http_error_is_retryable_transient(self, error: requests.HTTPError, attempt: int, max_attempts: int) -> bool:
        status_code = int(getattr(error.response, "status_code", 0) or 0)
        return status_code in self.RETRYABLE_HTTP_STATUSES and attempt < max_attempts

    @abstractmethod
    @beartype
    @require(
        lambda project_id: isinstance(project_id, str) and len(project_id.strip()) > 0, "Project ID must be non-empty"
    )
    @require(lambda payload: isinstance(payload, dict), "Payload must be dict")
    @ensure(lambda result: isinstance(result, dict), "Must return created issue metadata dict")
    def create_issue(self, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Create backlog issue/work item from provider-agnostic payload."""

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
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def _slugify_imported_change_title(self, title: str) -> str:
        """Return a stable kebab-case slug for imported backlog titles."""
        normalized = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        normalized = re.sub(r"-{2,}", "-", normalized)
        return normalized or "change"

    @beartype
    @ensure(lambda result: isinstance(result, str) and len(result) > 0, "Must return non-empty change id")
    def _normalize_imported_change_id(
        self,
        proposal_data: dict[str, Any],
        item_data: dict[str, Any],
        tool_name: str,
        existing_proposals: dict[str, ChangeProposal] | None = None,
    ) -> str:
        """Normalize imported change IDs so title-based slugs win over numeric fallbacks."""
        raw_change_id = self._get_imported_change_id_seed(proposal_data, item_data)
        title = str(proposal_data.get("title") or item_data.get("title") or "").strip()
        candidate = self._prefer_imported_title_slug(raw_change_id, title)
        proposals = existing_proposals or {}
        return self._dedupe_imported_change_id(candidate, raw_change_id, item_data, tool_name, proposals)

    @beartype
    @ensure(lambda result: isinstance(result, str) and len(result) > 0, "Must return non-empty seed")
    def _get_imported_change_id_seed(self, proposal_data: dict[str, Any], item_data: dict[str, Any]) -> str:
        return str(proposal_data.get("change_id") or item_data.get("id") or item_data.get("number") or "unknown")

    @beartype
    @ensure(lambda result: isinstance(result, str) and len(result) > 0, "Must return non-empty candidate")
    def _prefer_imported_title_slug(self, raw_change_id: str, title: str) -> str:
        if raw_change_id and raw_change_id != "unknown" and not raw_change_id.isdigit():
            return raw_change_id
        if not title:
            return raw_change_id or "unknown"
        return self._slugify_imported_change_title(title)

    @beartype
    @ensure(lambda result: isinstance(result, str) and len(result) > 0, "Must return non-empty change id")
    def _dedupe_imported_change_id(
        self,
        candidate: str,
        raw_change_id: str,
        item_data: dict[str, Any],
        tool_name: str,
        existing_proposals: dict[str, ChangeProposal],
    ) -> str:
        existing_change_id = self._find_existing_imported_change_id_by_source(
            item_data,
            tool_name,
            existing_proposals,
        )
        if existing_change_id:
            return existing_change_id

        existing_proposal = existing_proposals.get(candidate)
        if existing_proposal is None:
            return candidate or raw_change_id or "unknown"

        if self._matches_existing_import_source(existing_proposal, item_data, tool_name):
            return candidate

        source_id = item_data.get("id") or item_data.get("number")
        if source_id is None:
            return candidate or raw_change_id or "unknown"

        deduped_candidate = f"{candidate}-{source_id}"
        existing_deduped = existing_proposals.get(deduped_candidate)
        if existing_deduped and self._matches_existing_import_source(existing_deduped, item_data, tool_name):
            return deduped_candidate
        return deduped_candidate

    @beartype
    @ensure(lambda result: result is None or isinstance(result, str), "Must return change id or None")
    def _find_existing_imported_change_id_by_source(
        self,
        item_data: dict[str, Any],
        tool_name: str,
        existing_proposals: dict[str, ChangeProposal],
    ) -> str | None:
        for change_id, proposal in existing_proposals.items():
            if self._matches_existing_import_source(proposal, item_data, tool_name):
                return change_id
        return None

    @beartype
    @ensure(lambda result: isinstance(result, str), "Must return source URL string")
    def _get_import_source_url(self, item_data: dict[str, Any]) -> str:
        html_url = item_data.get("html_url")
        if isinstance(html_url, str) and html_url:
            return html_url

        url = item_data.get("url")
        if isinstance(url, str) and url:
            return url

        links = item_data.get("_links")
        if not isinstance(links, Mapping):
            return ""
        html_link = cast(Mapping[str, Any], links).get("html")
        if not isinstance(html_link, Mapping):
            return ""
        href = cast(Mapping[str, Any], html_link).get("href")
        return href if isinstance(href, str) else ""

    @beartype
    @ensure(lambda result: isinstance(result, bool), "Must return match flag")
    def _matches_existing_import_source(
        self,
        proposal: ChangeProposal,
        item_data: dict[str, Any],
        tool_name: str,
    ) -> bool:
        source_tracking = proposal.source_tracking
        if source_tracking is None or not isinstance(source_tracking.source_metadata, dict):
            return False

        source_id = item_data.get("id") or item_data.get("number")
        source_id_str = str(source_id) if source_id is not None else None
        source_url = self._get_import_source_url(item_data)
        source_type = tool_name.lower()
        source_metadata = source_tracking.source_metadata
        backlog_entries = source_metadata.get("backlog_entries")
        if isinstance(backlog_entries, list):
            for entry in backlog_entries:
                if isinstance(entry, dict) and self._source_metadata_matches(
                    entry, source_type, source_id_str, source_url
                ):
                    return True

        fallback_metadata = dict(source_metadata)
        fallback_metadata.setdefault("source_type", source_tracking.tool)
        return self._source_metadata_matches(fallback_metadata, source_type, source_id_str, source_url)

    @beartype
    @ensure(lambda result: isinstance(result, bool), "Must return match flag")
    def _source_metadata_matches(
        self,
        source_metadata: dict[str, Any],
        source_type: str,
        source_id: str | None,
        source_url: str,
    ) -> bool:
        entry_type = str(source_metadata.get("source_type") or source_metadata.get("tool") or "").lower()
        if entry_type and entry_type != source_type:
            return False

        entry_url = source_metadata.get("source_url")
        if source_url and isinstance(entry_url, str) and entry_url == source_url:
            return True

        entry_id = source_metadata.get("source_id")
        if source_id is None or entry_id is None:
            return False
        return str(entry_id) == source_id

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
        self._merge_source_id_into_metadata(tool_name, item_data, source_metadata)
        self._merge_source_urls_state_assignees(item_data, source_metadata)
        if bridge_config and hasattr(bridge_config, "external_base_path") and bridge_config.external_base_path:
            source_metadata["external_base_path"] = str(bridge_config.external_base_path)

        return SourceTracking(tool=tool_name, source_metadata=source_metadata)

    def _merge_source_id_into_metadata(
        self, tool_name: str, item_data: dict[str, Any], source_metadata: dict[str, Any]
    ) -> None:
        if tool_name.lower() == "github":
            source_id = item_data.get("number") or item_data.get("id")
            if source_id is not None:
                source_metadata["source_id"] = str(source_id)
            return
        source_id = item_data.get("id") or item_data.get("number")
        if source_id is not None:
            source_metadata["source_id"] = source_id

    @staticmethod
    def _merge_source_urls_state_assignees(item_data: dict[str, Any], source_metadata: dict[str, Any]) -> None:
        if "html_url" in item_data:
            source_metadata["source_url"] = item_data.get("html_url")
        elif "url" in item_data:
            source_metadata["source_url"] = item_data.get("url")
        if "state" in item_data:
            source_metadata["source_state"] = item_data.get("state")
        if "assignees" not in item_data and "assignee" not in item_data:
            return
        assignees = item_data.get("assignees", [])
        if not assignees and "assignee" in item_data:
            assignees = [item_data["assignee"]] if item_data["assignee"] else []
        source_metadata["assignees"] = assignees

    @beartype
    @require(
        lambda openspec_status: isinstance(openspec_status, str) and len(openspec_status) > 0,
        "Status must be non-empty",
    )
    @require(
        lambda backlog_status: isinstance(backlog_status, str) and len(backlog_status) > 0,
        "Status must be non-empty",
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

        return openspec_status

    @beartype
    @require(lambda item_data: isinstance(item_data, dict), "Item data must be dict")
    @require(lambda tool_name: isinstance(tool_name, str) and len(tool_name) > 0, "Tool name must be non-empty")
    @ensure(lambda result: isinstance(result, ChangeProposal) or result is None, "Must return ChangeProposal or None")
    def import_backlog_item_as_proposal(
        self,
        item_data: dict[str, Any],
        tool_name: str,
        bridge_config: Any = None,
        existing_proposals: dict[str, ChangeProposal] | None = None,
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
            existing_proposals: Existing proposals used for collision-safe and idempotent imported IDs

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
            proposal_data = self.extract_change_proposal_data(item_data)

            if "status" in proposal_data:
                openspec_status = proposal_data["status"]
            else:
                backlog_status = item_data.get("state") or item_data.get("status") or "open"
                openspec_status = self.map_backlog_status_to_openspec(backlog_status)

            source_tracking = self.create_source_tracking(item_data, tool_name, bridge_config)
            change_id = self._normalize_imported_change_id(proposal_data, item_data, tool_name, existing_proposals)
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
