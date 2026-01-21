"""
Unit tests for LocalYAMLBacklogAdapter.

Tests the local YAML adapter implementation.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from beartype import beartype

from specfact_cli.backlog.adapters.local_yaml_adapter import LocalYAMLBacklogAdapter
from specfact_cli.backlog.filters import BacklogFilters
from specfact_cli.models.backlog_item import BacklogItem


@pytest.fixture
def temp_backlog_file(tmp_path: Path) -> Path:
    """Create temporary backlog YAML file."""
    backlog_file = tmp_path / ".specfact" / "backlog.yaml"
    backlog_file.parent.mkdir(parents=True, exist_ok=True)
    return backlog_file


@pytest.fixture
def sample_backlog_items() -> list[BacklogItem]:
    """Create sample backlog items for testing."""
    return [
        BacklogItem(
            id="1",
            provider="local_yaml",
            url="",
            title="Open feature",
            body_markdown="Feature description",
            state="open",
            assignees=["alice"],
            tags=["feature"],
        ),
        BacklogItem(
            id="2",
            provider="local_yaml",
            url="",
            title="Closed bug",
            body_markdown="Bug description",
            state="closed",
            assignees=["bob"],
            tags=["bug"],
        ),
        BacklogItem(
            id="3",
            provider="local_yaml",
            url="",
            title="Open task",
            body_markdown="Task description",
            state="open",
            assignees=["alice"],
            tags=["task"],
        ),
    ]


class TestLocalYAMLBacklogAdapter:
    """Test LocalYAMLBacklogAdapter."""

    @beartype
    def test_adapter_name(self) -> None:
        """Test adapter name."""
        adapter = LocalYAMLBacklogAdapter()
        assert adapter.name() == "local_yaml"

    @beartype
    def test_supports_format_yaml(self) -> None:
        """Test supports_format for YAML."""
        adapter = LocalYAMLBacklogAdapter()
        assert adapter.supports_format("yaml") is True
        assert adapter.supports_format("YAML") is True

    @beartype
    def test_supports_format_other(self) -> None:
        """Test supports_format for other formats."""
        adapter = LocalYAMLBacklogAdapter()
        assert adapter.supports_format("markdown") is False
        assert adapter.supports_format("json") is False

    @beartype
    def test_fetch_backlog_items_empty_file(self, temp_backlog_file: Path) -> None:
        """Test fetching from empty file."""
        adapter = LocalYAMLBacklogAdapter(backlog_file=temp_backlog_file)
        filters = BacklogFilters()
        items = adapter.fetch_backlog_items(filters)
        assert items == []

    @beartype
    def test_fetch_backlog_items_with_state_filter(
        self, temp_backlog_file: Path, sample_backlog_items: list[BacklogItem]
    ) -> None:
        """Test fetching with state filter."""
        from specfact_cli.utils.yaml_utils import dump_yaml

        # Create backlog file with items
        data = {"items": [item.model_dump() for item in sample_backlog_items]}
        dump_yaml(data, temp_backlog_file)

        adapter = LocalYAMLBacklogAdapter(backlog_file=temp_backlog_file)
        filters = BacklogFilters(state="open")
        items = adapter.fetch_backlog_items(filters)

        assert len(items) == 2
        assert all(item.state == "open" for item in items)

    @beartype
    def test_fetch_backlog_items_with_assignee_filter(
        self, temp_backlog_file: Path, sample_backlog_items: list[BacklogItem]
    ) -> None:
        """Test fetching with assignee filter."""
        from specfact_cli.utils.yaml_utils import dump_yaml

        data = {"items": [item.model_dump() for item in sample_backlog_items]}
        dump_yaml(data, temp_backlog_file)

        adapter = LocalYAMLBacklogAdapter(backlog_file=temp_backlog_file)
        filters = BacklogFilters(assignee="alice")
        items = adapter.fetch_backlog_items(filters)

        assert len(items) == 2
        assert all("alice" in item.assignees for item in items)

    @beartype
    def test_fetch_backlog_items_with_labels_filter(
        self, temp_backlog_file: Path, sample_backlog_items: list[BacklogItem]
    ) -> None:
        """Test fetching with labels filter."""
        from specfact_cli.utils.yaml_utils import dump_yaml

        data = {"items": [item.model_dump() for item in sample_backlog_items]}
        dump_yaml(data, temp_backlog_file)

        adapter = LocalYAMLBacklogAdapter(backlog_file=temp_backlog_file)
        filters = BacklogFilters(labels=["feature"])
        items = adapter.fetch_backlog_items(filters)

        assert len(items) == 1
        assert items[0].id == "1"
        assert "feature" in items[0].tags

    @beartype
    def test_fetch_backlog_items_with_search_filter(
        self, temp_backlog_file: Path, sample_backlog_items: list[BacklogItem]
    ) -> None:
        """Test fetching with search filter."""
        from specfact_cli.utils.yaml_utils import dump_yaml

        data = {"items": [item.model_dump() for item in sample_backlog_items]}
        dump_yaml(data, temp_backlog_file)

        adapter = LocalYAMLBacklogAdapter(backlog_file=temp_backlog_file)
        filters = BacklogFilters(search="bug")
        items = adapter.fetch_backlog_items(filters)

        assert len(items) == 1
        assert "bug" in items[0].title.lower() or "bug" in items[0].body_markdown.lower()

    @beartype
    def test_update_backlog_item_new_item(self, temp_backlog_file: Path) -> None:
        """Test updating a new item (creates it)."""
        adapter = LocalYAMLBacklogAdapter(backlog_file=temp_backlog_file)
        new_item = BacklogItem(id="1", provider="local_yaml", url="", title="New Item", state="open")

        result = adapter.update_backlog_item(new_item)

        assert result.id == "1"
        assert temp_backlog_file.exists()

        # Verify item was saved
        items = adapter.fetch_backlog_items(BacklogFilters())
        assert len(items) == 1
        assert items[0].id == "1"

    @beartype
    def test_update_backlog_item_existing_item(
        self, temp_backlog_file: Path, sample_backlog_items: list[BacklogItem]
    ) -> None:
        """Test updating an existing item."""
        from specfact_cli.utils.yaml_utils import dump_yaml

        data = {"items": [item.model_dump() for item in sample_backlog_items]}
        dump_yaml(data, temp_backlog_file)

        adapter = LocalYAMLBacklogAdapter(backlog_file=temp_backlog_file)
        updated_item = BacklogItem(
            id="1",
            provider="local_yaml",
            url="",
            title="Updated Title",
            body_markdown="Updated body",
            state="closed",
        )

        result = adapter.update_backlog_item(updated_item, update_fields=None)

        assert result.title == "Updated Title"
        assert result.body_markdown == "Updated body"
        assert result.state == "closed"

    @beartype
    def test_update_backlog_item_selective_fields(
        self, temp_backlog_file: Path, sample_backlog_items: list[BacklogItem]
    ) -> None:
        """Test updating only selected fields."""
        from specfact_cli.utils.yaml_utils import dump_yaml

        data = {"items": [item.model_dump() for item in sample_backlog_items]}
        dump_yaml(data, temp_backlog_file)

        adapter = LocalYAMLBacklogAdapter(backlog_file=temp_backlog_file)
        updated_item = BacklogItem(
            id="1",
            provider="local_yaml",
            url="",
            title="Updated Title",
            body_markdown="Original body",
            state="open",
        )

        result = adapter.update_backlog_item(updated_item, update_fields=["title"])

        assert result.title == "Updated Title"
        # Other fields should remain unchanged (from original item in file)
