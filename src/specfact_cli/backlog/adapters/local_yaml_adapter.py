"""
Local YAML backlog adapter example.

This module provides an example implementation of a backlog adapter that reads
from and writes to a local YAML file, demonstrating the extensibility of the
BacklogAdapter interface.
"""

from __future__ import annotations

from pathlib import Path

from beartype import beartype
from icontract import ensure, require

from specfact_cli.backlog.adapters.base import BacklogAdapter
from specfact_cli.backlog.filters import BacklogFilters
from specfact_cli.backlog.formats.structured_format import StructuredFormat
from specfact_cli.models.backlog_item import BacklogItem
from specfact_cli.utils.yaml_utils import dump_yaml, load_yaml


class LocalYAMLBacklogAdapter(BacklogAdapter):
    """
    Local YAML backlog adapter example.

    This adapter reads backlog items from `.specfact/backlog.yaml` and writes
    updates back to the same file. This demonstrates how easy it is to add new
    backlog sources using the BacklogAdapter interface.
    """

    def __init__(self, backlog_file: Path | None = None) -> None:
        """
        Initialize local YAML adapter.

        Args:
            backlog_file: Path to backlog YAML file (defaults to `.specfact/backlog.yaml`)
        """
        if backlog_file is None:
            backlog_file = Path(".specfact") / "backlog.yaml"
        self.backlog_file = Path(backlog_file)
        self._format = StructuredFormat(format_type="yaml")

    @beartype
    @ensure(lambda result: isinstance(result, str) and len(result) > 0, "Must return non-empty adapter name")
    def name(self) -> str:
        """Get the adapter name."""
        return "local_yaml"

    @beartype
    @require(lambda format_type: isinstance(format_type, str) and len(format_type) > 0, "Format type must be non-empty")
    @ensure(lambda result: isinstance(result, bool), "Must return boolean")
    def supports_format(self, format_type: str) -> bool:
        """Check if adapter supports the specified format."""
        return format_type.lower() == "yaml"

    @beartype
    @require(lambda filters: isinstance(filters, BacklogFilters), "Filters must be BacklogFilters instance")
    @ensure(lambda result: isinstance(result, list), "Must return list of BacklogItem")
    @ensure(
        lambda result, filters: all(isinstance(item, BacklogItem) for item in result), "All items must be BacklogItem"
    )
    def fetch_backlog_items(self, filters: BacklogFilters) -> list[BacklogItem]:
        """
        Fetch backlog items from local YAML file.

        Reads items from `.specfact/backlog.yaml` and applies filters.
        """
        if not self.backlog_file.exists():
            return []

        # Load YAML file
        data = load_yaml(self.backlog_file)
        items_data = data.get("items", [])

        # Convert to BacklogItem instances
        items: list[BacklogItem] = []
        for item_data in items_data:
            try:
                item = BacklogItem(**item_data)
                items.append(item)
            except Exception:
                # Skip invalid items
                continue

        # Apply filters
        filtered_items = items

        if filters.state:
            filtered_items = [item for item in filtered_items if item.state.lower() == filters.state.lower()]

        if filters.assignee:
            filtered_items = [
                item
                for item in filtered_items
                if any(assignee.lower() == filters.assignee.lower() for assignee in item.assignees)
            ]

        if filters.labels:
            filtered_items = [item for item in filtered_items if any(label in item.tags for label in filters.labels)]

        if filters.iteration:
            filtered_items = [item for item in filtered_items if item.iteration and item.iteration == filters.iteration]

        if filters.sprint:
            filtered_items = [item for item in filtered_items if item.sprint and item.sprint == filters.sprint]

        if filters.release:
            filtered_items = [item for item in filtered_items if item.release and item.release == filters.release]

        if filters.area:
            # Area filtering not applicable for local YAML
            pass

        if filters.search:
            # Simple text search in title and body
            search_lower = filters.search.lower()
            filtered_items = [
                item
                for item in filtered_items
                if search_lower in item.title.lower() or search_lower in item.body_markdown.lower()
            ]

        return filtered_items

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
        Update a backlog item in local YAML file.

        Updates the item in `.specfact/backlog.yaml` and returns the updated item.
        """
        # Ensure directory exists
        self.backlog_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing items
        if self.backlog_file.exists():
            data = load_yaml(self.backlog_file)
            items_data = data.get("items", [])
        else:
            items_data = []

        # Find and update item
        updated = False
        for i, existing_item_data in enumerate(items_data):
            if existing_item_data.get("id") == item.id and existing_item_data.get("provider") == item.provider:
                # Update item
                if update_fields is None:
                    # Update all fields
                    items_data[i] = item.model_dump()
                else:
                    # Update only specified fields
                    for field in update_fields:
                        if hasattr(item, field):
                            items_data[i][field] = getattr(item, field)
                updated = True
                break

        # If item not found, add it
        if not updated:
            items_data.append(item.model_dump())

        # Save back to YAML file
        data = {"items": items_data}
        dump_yaml(data, self.backlog_file)

        return item
