"""
Backlog adapter base interface.

This module defines the standard BacklogAdapter interface that all backlog
sources (GitHub, ADO, JIRA, GitLab, etc.) must implement for the backlog
refinement feature.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from beartype import beartype
from icontract import ensure, require

from specfact_cli.backlog.filters import BacklogFilters
from specfact_cli.models.backlog_item import BacklogItem


class BacklogAdapter(ABC):
    """
    Abstract base interface for backlog adapters.

    This interface provides a standard contract for all backlog sources,
    enabling extensible backlog support with consistent filtering and updates.
    """

    @abstractmethod
    @beartype
    @ensure(lambda result: isinstance(result, str) and len(result) > 0, "Must return non-empty adapter name")
    def name(self) -> str:
        """
        Get the adapter name.

        Returns:
            Adapter name (e.g., "github", "ado", "jira", "local_yaml")
        """
        ...

    @abstractmethod
    @beartype
    @require(lambda format_type: isinstance(format_type, str) and len(format_type) > 0, "Format type must be non-empty")
    @ensure(lambda result: isinstance(result, bool), "Must return boolean")
    def supports_format(self, format_type: str) -> bool:
        """
        Check if adapter supports the specified format.

        Args:
            format_type: Format type (e.g., "markdown", "yaml", "json")

        Returns:
            True if adapter supports the format, False otherwise
        """
        ...

    @abstractmethod
    @beartype
    @require(lambda filters: isinstance(filters, BacklogFilters), "Filters must be BacklogFilters instance")
    @ensure(lambda result: isinstance(result, list), "Must return list of BacklogItem")
    @ensure(
        lambda result, filters: all(isinstance(item, BacklogItem) for item in result), "All items must be BacklogItem"
    )
    def fetch_backlog_items(self, filters: BacklogFilters) -> list[BacklogItem]:
        """
        Fetch backlog items matching the specified filters.

        Args:
            filters: BacklogFilters instance with filter criteria

        Returns:
            List of BacklogItem instances matching the filters

        Note:
            Adapters should apply filters as appropriate for their provider's
            capabilities. Some filters may be applied post-fetch if the provider
            API doesn't support them directly.
        """
        ...

    @abstractmethod
    @beartype
    @require(lambda item: isinstance(item, BacklogItem), "Item must be BacklogItem")
    @require(
        lambda update_fields: update_fields is None or isinstance(update_fields, list),
        "Update fields must be None or list",
    )
    @ensure(lambda result: isinstance(result, BacklogItem), "Must return BacklogItem")
    @ensure(
        lambda result, item: result.id == item.id and result.provider == item.provider,
        "Updated item must preserve id and provider",
    )
    def update_backlog_item(self, item: BacklogItem, update_fields: list[str] | None = None) -> BacklogItem:
        """
        Update a backlog item.

        Args:
            item: BacklogItem to update
            update_fields: Optional list of field names to update (None = update all fields)

        Returns:
            Updated BacklogItem instance

        Note:
            If update_fields is None, all fields should be updated.
            If update_fields is specified, only those fields should be updated.
        """
        ...

    @beartype
    @require(lambda original: isinstance(original, BacklogItem), "Original must be BacklogItem")
    @require(lambda updated: isinstance(updated, BacklogItem), "Updated must be BacklogItem")
    @ensure(lambda result: isinstance(result, bool), "Must return boolean")
    def validate_round_trip(self, original: BacklogItem, updated: BacklogItem) -> bool:
        """
        Validate that round-trip preserves essential content.

        Args:
            original: Original BacklogItem before round-trip
            updated: BacklogItem after round-trip

        Returns:
            True if round-trip preserved id, title, body_markdown, and state

        Note:
            This method has a default implementation but can be overridden
            by adapters that need custom validation logic.
        """
        return (
            original.id == updated.id
            and original.provider == updated.provider
            and original.title == updated.title
            and original.body_markdown == updated.body_markdown
            and original.state == updated.state
        )

    @beartype
    def create_backlog_item_from_spec(self) -> BacklogItem | None:
        """
        Create a backlog item from an OpenSpec change proposal (optional).

        Returns:
            BacklogItem instance if supported, None otherwise

        Note:
            This is an optional method. Adapters that don't support creating
            items from specs can use the default None implementation.
        """
        return None

    @beartype
    def add_comment(self, item: BacklogItem, comment: str) -> bool:
        """
        Add a comment to a backlog item (optional).

        Args:
            item: BacklogItem to add comment to
            comment: Comment text to add

        Returns:
            True if comment was added successfully, False otherwise

        Note:
            This is an optional method. Adapters that don't support comments
            can use the default False implementation.
        """
        return False
