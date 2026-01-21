"""
Unit tests for BacklogAdapter interface.

Tests the abstract BacklogAdapter interface and its contract requirements.
"""

from __future__ import annotations

from beartype import beartype

from specfact_cli.backlog.adapters.base import BacklogAdapter
from specfact_cli.backlog.filters import BacklogFilters
from specfact_cli.models.backlog_item import BacklogItem


class MockBacklogAdapter(BacklogAdapter):
    """Mock implementation of BacklogAdapter for testing."""

    def __init__(self, name: str = "mock", supports_format_type: str = "markdown") -> None:
        """Initialize mock adapter."""
        self._name = name
        self._supports_format_type = supports_format_type
        self._items: list[BacklogItem] = []

    @beartype
    def name(self) -> str:
        """Get adapter name."""
        return self._name

    @beartype
    def supports_format(self, format_type: str) -> bool:
        """Check if adapter supports format."""
        return format_type.lower() == self._supports_format_type.lower()

    @beartype
    def fetch_backlog_items(self, filters: BacklogFilters) -> list[BacklogItem]:
        """Fetch backlog items."""
        filtered = self._items.copy()

        if filters.state:
            filtered = [item for item in filtered if item.state.lower() == filters.state.lower()]

        if filters.assignee:
            filtered = [
                item
                for item in filtered
                if any(assignee.lower() == filters.assignee.lower() for assignee in item.assignees)
            ]

        if filters.labels:
            filtered = [item for item in filtered if any(label in item.tags for label in filters.labels)]

        return filtered

    @beartype
    def update_backlog_item(self, item: BacklogItem, update_fields: list[str] | None = None) -> BacklogItem:
        """Update backlog item."""
        # Find and update item in mock storage
        for i, existing_item in enumerate(self._items):
            if existing_item.id == item.id and existing_item.provider == item.provider:
                if update_fields is None:
                    self._items[i] = item
                else:
                    # Update only specified fields
                    updated_dict = existing_item.model_dump()
                    for field in update_fields:
                        if hasattr(item, field):
                            updated_dict[field] = getattr(item, field)
                    self._items[i] = BacklogItem(**updated_dict)
                return self._items[i]

        # If not found, add it
        self._items.append(item)
        return item

    def add_test_item(self, item: BacklogItem) -> None:
        """Add test item to mock storage."""
        self._items.append(item)


class TestBacklogAdapter:
    """Test BacklogAdapter interface."""

    @beartype
    def test_adapter_name(self) -> None:
        """Test adapter name method."""
        adapter = MockBacklogAdapter(name="test_adapter")
        assert adapter.name() == "test_adapter"

    @beartype
    def test_supports_format_true(self) -> None:
        """Test supports_format returns True for supported format."""
        adapter = MockBacklogAdapter(supports_format_type="markdown")
        assert adapter.supports_format("markdown") is True
        assert adapter.supports_format("MARKDOWN") is True  # Case insensitive

    @beartype
    def test_supports_format_false(self) -> None:
        """Test supports_format returns False for unsupported format."""
        adapter = MockBacklogAdapter(supports_format_type="markdown")
        assert adapter.supports_format("yaml") is False
        assert adapter.supports_format("json") is False

    @beartype
    def test_fetch_backlog_items_empty(self) -> None:
        """Test fetching items when adapter has no items."""
        adapter = MockBacklogAdapter()
        filters = BacklogFilters()
        items = adapter.fetch_backlog_items(filters)
        assert items == []

    @beartype
    def test_fetch_backlog_items_with_state_filter(self) -> None:
        """Test fetching items with state filter."""
        adapter = MockBacklogAdapter()
        item1 = BacklogItem(id="1", provider="test", url="", title="Item 1", state="open")
        item2 = BacklogItem(id="2", provider="test", url="", title="Item 2", state="closed")
        adapter.add_test_item(item1)
        adapter.add_test_item(item2)

        filters = BacklogFilters(state="open")
        items = adapter.fetch_backlog_items(filters)
        assert len(items) == 1
        assert items[0].id == "1"
        assert items[0].state == "open"

    @beartype
    def test_fetch_backlog_items_with_assignee_filter(self) -> None:
        """Test fetching items with assignee filter."""
        adapter = MockBacklogAdapter()
        item1 = BacklogItem(id="1", provider="test", url="", title="Item 1", state="open", assignees=["alice"])
        item2 = BacklogItem(id="2", provider="test", url="", title="Item 2", state="open", assignees=["bob"])
        adapter.add_test_item(item1)
        adapter.add_test_item(item2)

        filters = BacklogFilters(assignee="alice")
        items = adapter.fetch_backlog_items(filters)
        assert len(items) == 1
        assert items[0].id == "1"
        assert "alice" in items[0].assignees

    @beartype
    def test_fetch_backlog_items_with_labels_filter(self) -> None:
        """Test fetching items with labels filter."""
        adapter = MockBacklogAdapter()
        item1 = BacklogItem(id="1", provider="test", url="", title="Item 1", state="open", tags=["feature"])
        item2 = BacklogItem(id="2", provider="test", url="", title="Item 2", state="open", tags=["bug"])
        adapter.add_test_item(item1)
        adapter.add_test_item(item2)

        filters = BacklogFilters(labels=["feature"])
        items = adapter.fetch_backlog_items(filters)
        assert len(items) == 1
        assert items[0].id == "1"
        assert "feature" in items[0].tags

    @beartype
    def test_fetch_backlog_items_multiple_filters(self) -> None:
        """Test fetching items with multiple filters."""
        adapter = MockBacklogAdapter()
        item1 = BacklogItem(
            id="1", provider="test", url="", title="Item 1", state="open", assignees=["alice"], tags=["feature"]
        )
        item2 = BacklogItem(
            id="2", provider="test", url="", title="Item 2", state="open", assignees=["bob"], tags=["feature"]
        )
        adapter.add_test_item(item1)
        adapter.add_test_item(item2)

        filters = BacklogFilters(state="open", assignee="alice", labels=["feature"])
        items = adapter.fetch_backlog_items(filters)
        assert len(items) == 1
        assert items[0].id == "1"

    @beartype
    def test_update_backlog_item_all_fields(self) -> None:
        """Test updating all fields of a backlog item."""
        adapter = MockBacklogAdapter()
        original_item = BacklogItem(
            id="1", provider="test", url="", title="Original Title", body_markdown="Original body", state="open"
        )
        adapter.add_test_item(original_item)

        updated_item = BacklogItem(
            id="1", provider="test", url="", title="Updated Title", body_markdown="Updated body", state="closed"
        )
        result = adapter.update_backlog_item(updated_item, update_fields=None)

        assert result.title == "Updated Title"
        assert result.body_markdown == "Updated body"
        assert result.state == "closed"
        assert result.id == "1"
        assert result.provider == "test"

    @beartype
    def test_update_backlog_item_selective_fields(self) -> None:
        """Test updating only selected fields."""
        adapter = MockBacklogAdapter()
        original_item = BacklogItem(
            id="1", provider="test", url="", title="Original Title", body_markdown="Original body", state="open"
        )
        adapter.add_test_item(original_item)

        updated_item = BacklogItem(
            id="1", provider="test", url="", title="Updated Title", body_markdown="Updated body", state="closed"
        )
        result = adapter.update_backlog_item(updated_item, update_fields=["title"])

        assert result.title == "Updated Title"
        assert result.body_markdown == "Original body"  # Not updated
        assert result.state == "open"  # Not updated

    @beartype
    def test_update_backlog_item_new_item(self) -> None:
        """Test updating a non-existent item (creates new)."""
        adapter = MockBacklogAdapter()
        new_item = BacklogItem(id="1", provider="test", url="", title="New Item", state="open")
        result = adapter.update_backlog_item(new_item)

        assert result.id == "1"
        assert len(adapter._items) == 1

    @beartype
    def test_validate_round_trip_success(self) -> None:
        """Test validate_round_trip returns True for preserved content."""
        adapter = MockBacklogAdapter()
        original = BacklogItem(
            id="1", provider="test", url="http://test.com/1", title="Test", body_markdown="Body", state="open"
        )
        updated = BacklogItem(
            id="1", provider="test", url="http://test.com/1", title="Test", body_markdown="Body", state="open"
        )

        assert adapter.validate_round_trip(original, updated) is True

    @beartype
    def test_validate_round_trip_failure_id_mismatch(self) -> None:
        """Test validate_round_trip returns False for id mismatch."""
        adapter = MockBacklogAdapter()
        original = BacklogItem(id="1", provider="test", url="", title="Test", state="open")
        updated = BacklogItem(id="2", provider="test", url="", title="Test", state="open")

        assert adapter.validate_round_trip(original, updated) is False

    @beartype
    def test_validate_round_trip_failure_title_mismatch(self) -> None:
        """Test validate_round_trip returns False for title mismatch."""
        adapter = MockBacklogAdapter()
        original = BacklogItem(id="1", provider="test", url="", title="Original", state="open")
        updated = BacklogItem(id="1", provider="test", url="", title="Updated", state="open")

        assert adapter.validate_round_trip(original, updated) is False

    @beartype
    def test_create_backlog_item_from_spec_default(self) -> None:
        """Test create_backlog_item_from_spec returns None by default."""
        adapter = MockBacklogAdapter()
        result = adapter.create_backlog_item_from_spec()
        assert result is None
