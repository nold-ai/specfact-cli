"""
Unit tests for backlog filtering functionality.

Tests the _apply_filters function with various filter combinations,
including open/closed GitHub issues.
"""

from __future__ import annotations

from typing import Any

import pytest
from beartype import beartype

from specfact_cli.backlog.converter import convert_github_issue_to_backlog_item
from specfact_cli.commands.backlog_commands import _apply_filters
from specfact_cli.models.backlog_item import BacklogItem


@pytest.fixture
def sample_github_issues() -> list[dict[str, Any]]:
    """Create sample GitHub issues for testing."""
    return [
        {
            "number": 1,
            "html_url": "https://github.com/test/repo/issues/1",
            "title": "Open issue with feature label",
            "body": "This is an open issue",
            "state": "open",
            "assignees": [{"login": "dev1"}],
            "labels": [{"name": "feature"}, {"name": "enhancement"}],
            "milestone": None,
        },
        {
            "number": 2,
            "html_url": "https://github.com/test/repo/issues/2",
            "title": "Closed issue with bug label",
            "body": "This is a closed issue",
            "state": "closed",
            "assignees": [{"login": "dev2"}],
            "labels": [{"name": "bug"}],
            "milestone": None,
        },
        {
            "number": 3,
            "html_url": "https://github.com/test/repo/issues/3",
            "title": "Open issue assigned to dev1",
            "body": "Another open issue",
            "state": "open",
            "assignees": [{"login": "dev1"}],
            "labels": [{"name": "task"}],
            "milestone": None,
        },
        {
            "number": 4,
            "html_url": "https://github.com/test/repo/issues/4",
            "title": "Closed issue with feature label",
            "body": "Closed feature issue",
            "state": "closed",
            "assignees": [{"login": "dev2"}],
            "labels": [{"name": "feature"}],
            "milestone": None,
        },
        {
            "number": 5,
            "html_url": "https://github.com/test/repo/issues/5",
            "title": "Open issue with sprint milestone",
            "body": "Issue in sprint",
            "state": "open",
            "assignees": [],
            "labels": [{"name": "enhancement"}],
            "milestone": {"title": "Sprint 1"},
        },
        {
            "number": 6,
            "html_url": "https://github.com/test/repo/issues/6",
            "title": "Closed issue with release milestone",
            "body": "Issue in release",
            "state": "closed",
            "assignees": [],
            "labels": [{"name": "bug"}],
            "milestone": {"title": "v1.0.0"},
        },
    ]


@pytest.fixture
def backlog_items(sample_github_issues: list[dict[str, Any]]) -> list[BacklogItem]:
    """Convert GitHub issues to BacklogItem instances."""
    return [convert_github_issue_to_backlog_item(issue) for issue in sample_github_issues]


class TestBacklogFiltering:
    """Test backlog filtering functionality."""

    @beartype
    def test_filter_by_state_open(self, backlog_items: list[BacklogItem]) -> None:
        """Test filtering by open state."""
        filtered = _apply_filters(backlog_items, state="open")

        assert len(filtered) == 3
        assert all(item.state.lower() == "open" for item in filtered)
        assert all(item.id in ["1", "3", "5"] for item in filtered)

    @beartype
    def test_filter_by_state_closed(self, backlog_items: list[BacklogItem]) -> None:
        """Test filtering by closed state."""
        filtered = _apply_filters(backlog_items, state="closed")

        assert len(filtered) == 3
        assert all(item.state.lower() == "closed" for item in filtered)
        assert all(item.id in ["2", "4", "6"] for item in filtered)

    @beartype
    def test_filter_by_labels_single(self, backlog_items: list[BacklogItem]) -> None:
        """Test filtering by single label."""
        filtered = _apply_filters(backlog_items, labels=["feature"])

        assert len(filtered) == 2
        assert all("feature" in [tag.lower() for tag in item.tags] for item in filtered)
        assert all(item.id in ["1", "4"] for item in filtered)

    @beartype
    def test_filter_by_labels_multiple(self, backlog_items: list[BacklogItem]) -> None:
        """Test filtering by multiple labels (OR logic - any label matches)."""
        filtered = _apply_filters(backlog_items, labels=["feature", "bug"])

        assert len(filtered) == 4
        assert all(
            any(label in [tag.lower() for tag in item.tags] for label in ["feature", "bug"]) for item in filtered
        )
        assert all(item.id in ["1", "2", "4", "6"] for item in filtered)

    @beartype
    def test_filter_by_assignee(self, backlog_items: list[BacklogItem]) -> None:
        """Test filtering by assignee."""
        filtered = _apply_filters(backlog_items, assignee="dev1")

        assert len(filtered) == 2
        assert all("dev1" in [a.lower() for a in item.assignees] for item in filtered)
        assert all(item.id in ["1", "3"] for item in filtered)

    @beartype
    def test_filter_by_assignee_ado_displayname(self) -> None:
        """Test filtering ADO items by displayName."""
        from specfact_cli.backlog.converter import convert_ado_work_item_to_backlog_item

        # Create ADO items with different assignee identifiers
        ado_items = [
            convert_ado_work_item_to_backlog_item(
                {
                    "id": 1,
                    "url": "https://dev.azure.com/org/project/_apis/wit/workitems/1",
                    "fields": {
                        "System.Title": "Item 1",
                        "System.Description": "",
                        "System.State": "New",
                        "System.AssignedTo": {"displayName": "John Doe", "uniqueName": "john@example.com"},
                    },
                }
            ),
            convert_ado_work_item_to_backlog_item(
                {
                    "id": 2,
                    "url": "https://dev.azure.com/org/project/_apis/wit/workitems/2",
                    "fields": {
                        "System.Title": "Item 2",
                        "System.Description": "",
                        "System.State": "New",
                        "System.AssignedTo": {"displayName": "Jane Smith", "uniqueName": "jane@example.com"},
                    },
                }
            ),
        ]

        # Filter by displayName
        filtered = _apply_filters(ado_items, assignee="John Doe")
        assert len(filtered) == 1
        assert filtered[0].id == "1"

    @beartype
    def test_filter_by_assignee_ado_unique_name(self) -> None:
        """Test filtering ADO items by uniqueName."""
        from specfact_cli.backlog.converter import convert_ado_work_item_to_backlog_item

        ado_items = [
            convert_ado_work_item_to_backlog_item(
                {
                    "id": 1,
                    "url": "https://dev.azure.com/org/project/_apis/wit/workitems/1",
                    "fields": {
                        "System.Title": "Item 1",
                        "System.Description": "",
                        "System.State": "New",
                        "System.AssignedTo": {"displayName": "John Doe", "uniqueName": "john@example.com"},
                    },
                }
            ),
        ]

        # Filter by uniqueName (should match even though displayName is different)
        filtered = _apply_filters(ado_items, assignee="john@example.com")
        assert len(filtered) == 1
        assert filtered[0].id == "1"

    @beartype
    def test_filter_by_assignee_ado_mail(self) -> None:
        """Test filtering ADO items by mail field."""
        from specfact_cli.backlog.converter import convert_ado_work_item_to_backlog_item

        ado_items = [
            convert_ado_work_item_to_backlog_item(
                {
                    "id": 1,
                    "url": "https://dev.azure.com/org/project/_apis/wit/workitems/1",
                    "fields": {
                        "System.Title": "Item 1",
                        "System.Description": "",
                        "System.State": "New",
                        "System.AssignedTo": {
                            "displayName": "Bob Johnson",
                            "uniqueName": "bob@example.com",
                            "mail": "bob.johnson@example.com",
                        },
                    },
                }
            ),
        ]

        # Filter by mail field
        filtered = _apply_filters(ado_items, assignee="bob.johnson@example.com")
        assert len(filtered) == 1
        assert filtered[0].id == "1"

    @beartype
    def test_filter_by_assignee_case_insensitive(self) -> None:
        """Test that assignee filtering is case-insensitive."""
        from specfact_cli.backlog.converter import convert_ado_work_item_to_backlog_item

        ado_items = [
            convert_ado_work_item_to_backlog_item(
                {
                    "id": 1,
                    "url": "https://dev.azure.com/org/project/_apis/wit/workitems/1",
                    "fields": {
                        "System.Title": "Item 1",
                        "System.Description": "",
                        "System.State": "New",
                        "System.AssignedTo": {"displayName": "John Doe", "uniqueName": "john@example.com"},
                    },
                }
            ),
        ]

        # Filter with different case
        filtered = _apply_filters(ado_items, assignee="JOHN DOE")
        assert len(filtered) == 1
        assert filtered[0].id == "1"

    @beartype
    def test_filter_by_assignee_unassigned(self) -> None:
        """Test filtering for unassigned items."""
        from specfact_cli.backlog.converter import convert_ado_work_item_to_backlog_item

        ado_items = [
            convert_ado_work_item_to_backlog_item(
                {
                    "id": 1,
                    "url": "https://dev.azure.com/org/project/_apis/wit/workitems/1",
                    "fields": {
                        "System.Title": "Item 1",
                        "System.Description": "",
                        "System.State": "New",
                        # No System.AssignedTo field
                    },
                }
            ),
            convert_ado_work_item_to_backlog_item(
                {
                    "id": 2,
                    "url": "https://dev.azure.com/org/project/_apis/wit/workitems/2",
                    "fields": {
                        "System.Title": "Item 2",
                        "System.Description": "",
                        "System.State": "New",
                        "System.AssignedTo": {"displayName": "John Doe"},
                    },
                }
            ),
        ]

        # Filter by assignee should only return assigned items
        filtered = _apply_filters(ado_items, assignee="John Doe")
        assert len(filtered) == 1
        assert filtered[0].id == "2"

    @beartype
    def test_filter_by_sprint(self, backlog_items: list[BacklogItem]) -> None:
        """Test filtering by sprint."""
        filtered = _apply_filters(backlog_items, sprint="Sprint 1")

        assert len(filtered) == 1
        assert filtered[0].id == "5"
        assert filtered[0].sprint == "Sprint 1"

    @beartype
    def test_filter_by_release(self, backlog_items: list[BacklogItem]) -> None:
        """Test filtering by release."""
        filtered = _apply_filters(backlog_items, release="v1.0.0")

        assert len(filtered) == 1
        assert filtered[0].id == "6"
        assert filtered[0].release == "v1.0.0"

    @beartype
    def test_filter_combined_state_and_labels(self, backlog_items: list[BacklogItem]) -> None:
        """Test filtering by state AND labels."""
        filtered = _apply_filters(backlog_items, state="open", labels=["feature"])

        assert len(filtered) == 1
        assert filtered[0].id == "1"
        assert filtered[0].state.lower() == "open"
        assert "feature" in [tag.lower() for tag in filtered[0].tags]

    @beartype
    def test_filter_combined_state_and_assignee(self, backlog_items: list[BacklogItem]) -> None:
        """Test filtering by state AND assignee."""
        filtered = _apply_filters(backlog_items, state="closed", assignee="dev2")

        assert len(filtered) == 2
        assert all(item.state.lower() == "closed" for item in filtered)
        assert all("dev2" in [a.lower() for a in item.assignees] for item in filtered)
        assert all(item.id in ["2", "4"] for item in filtered)

    @beartype
    def test_filter_combined_all_filters(self, backlog_items: list[BacklogItem]) -> None:
        """Test filtering with all filters combined."""
        filtered = _apply_filters(
            backlog_items, state="open", labels=["enhancement"], assignee="dev1", sprint="Sprint 1"
        )

        # No item matches all criteria simultaneously
        assert len(filtered) == 0

    @beartype
    def test_filter_case_insensitive_state(self, backlog_items: list[BacklogItem]) -> None:
        """Test that state filtering is case-insensitive."""
        filtered_upper = _apply_filters(backlog_items, state="OPEN")
        filtered_lower = _apply_filters(backlog_items, state="open")
        filtered_mixed = _apply_filters(backlog_items, state="OpEn")

        assert len(filtered_upper) == len(filtered_lower) == len(filtered_mixed) == 3

    @beartype
    def test_filter_case_insensitive_labels(self, backlog_items: list[BacklogItem]) -> None:
        """Test that label filtering is case-insensitive."""
        filtered_upper = _apply_filters(backlog_items, labels=["FEATURE"])
        filtered_lower = _apply_filters(backlog_items, labels=["feature"])
        filtered_mixed = _apply_filters(backlog_items, labels=["FeAtUrE"])

        assert len(filtered_upper) == len(filtered_lower) == len(filtered_mixed) == 2

    @beartype
    def test_filter_case_insensitive_assignee(self, backlog_items: list[BacklogItem]) -> None:
        """Test that assignee filtering is case-insensitive."""
        filtered_upper = _apply_filters(backlog_items, assignee="DEV1")
        filtered_lower = _apply_filters(backlog_items, assignee="dev1")
        filtered_mixed = _apply_filters(backlog_items, assignee="DeV1")

        assert len(filtered_upper) == len(filtered_lower) == len(filtered_mixed) == 2

    @beartype
    def test_filter_no_filters_returns_all(self, backlog_items: list[BacklogItem]) -> None:
        """Test that no filters returns all items."""
        filtered = _apply_filters(backlog_items)

        assert len(filtered) == len(backlog_items) == 6

    @beartype
    def test_filter_empty_list(self) -> None:
        """Test filtering empty list."""
        filtered = _apply_filters([], state="open", labels=["feature"])

        assert len(filtered) == 0

    @beartype
    def test_filter_nonexistent_label(self, backlog_items: list[BacklogItem]) -> None:
        """Test filtering by non-existent label."""
        filtered = _apply_filters(backlog_items, labels=["nonexistent"])

        assert len(filtered) == 0

    @beartype
    def test_filter_nonexistent_assignee(self, backlog_items: list[BacklogItem]) -> None:
        """Test filtering by non-existent assignee."""
        filtered = _apply_filters(backlog_items, assignee="nonexistent")

        assert len(filtered) == 0

    @beartype
    def test_filter_nonexistent_state(self, backlog_items: list[BacklogItem]) -> None:
        """Test filtering by non-existent state."""
        filtered = _apply_filters(backlog_items, state="nonexistent")

        assert len(filtered) == 0

    @beartype
    def test_filter_open_issues_with_feature_label(self, backlog_items: list[BacklogItem]) -> None:
        """Test filtering open issues with feature label (real-world scenario)."""
        filtered = _apply_filters(backlog_items, state="open", labels=["feature"])

        assert len(filtered) == 1
        assert filtered[0].id == "1"
        assert filtered[0].state.lower() == "open"
        assert "feature" in [tag.lower() for tag in filtered[0].tags]

    @beartype
    def test_filter_closed_issues_with_bug_label(self, backlog_items: list[BacklogItem]) -> None:
        """Test filtering closed issues with bug label (real-world scenario)."""
        filtered = _apply_filters(backlog_items, state="closed", labels=["bug"])

        assert len(filtered) == 2
        assert all(item.state.lower() == "closed" for item in filtered)
        assert all("bug" in [tag.lower() for tag in item.tags] for item in filtered)
        assert all(item.id in ["2", "6"] for item in filtered)
