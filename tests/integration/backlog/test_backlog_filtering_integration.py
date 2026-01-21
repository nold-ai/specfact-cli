"""
Integration tests for backlog filtering with GitHub issues.

Tests the complete filtering workflow with realistic GitHub issue data,
including open and closed issues with various labels, assignees, and milestones.
"""

from __future__ import annotations

from typing import Any

import pytest
from beartype import beartype

from specfact_cli.backlog.converter import convert_github_issue_to_backlog_item
from specfact_cli.commands.backlog_commands import _apply_filters
from specfact_cli.models.backlog_item import BacklogItem


@pytest.fixture
def realistic_github_issues() -> list[dict[str, Any]]:
    """Create realistic GitHub issues for integration testing."""
    return [
        # Open issues
        {
            "number": 101,
            "html_url": "https://github.com/org/repo/issues/101",
            "title": "Add user authentication feature",
            "body": "We need to implement user login and registration",
            "state": "open",
            "assignees": [{"login": "alice"}],
            "labels": [{"name": "feature"}, {"name": "enhancement"}, {"name": "priority-high"}],
            "milestone": {"title": "Sprint 2025-01"},
            "created_at": "2025-01-15T10:00:00Z",
            "updated_at": "2025-01-20T14:30:00Z",
        },
        {
            "number": 102,
            "html_url": "https://github.com/org/repo/issues/102",
            "title": "Fix login button not responding",
            "body": "The login button doesn't work on mobile devices",
            "state": "open",
            "assignees": [{"login": "bob"}],
            "labels": [{"name": "bug"}, {"name": "priority-high"}],
            "milestone": None,
            "created_at": "2025-01-16T09:00:00Z",
            "updated_at": "2025-01-20T15:00:00Z",
        },
        {
            "number": 103,
            "html_url": "https://github.com/org/repo/issues/103",
            "title": "Research OAuth integration options",
            "body": "We need to evaluate OAuth providers for SSO",
            "state": "open",
            "assignees": [{"login": "charlie"}],
            "labels": [{"name": "spike"}, {"name": "research"}],
            "milestone": {"title": "Sprint 2025-01"},
            "created_at": "2025-01-17T11:00:00Z",
            "updated_at": "2025-01-19T16:00:00Z",
        },
        # Closed issues
        {
            "number": 201,
            "html_url": "https://github.com/org/repo/issues/201",
            "title": "Add password reset functionality",
            "body": "Users need to be able to reset their passwords",
            "state": "closed",
            "assignees": [{"login": "alice"}],
            "labels": [{"name": "feature"}, {"name": "enhancement"}],
            "milestone": {"title": "v1.2.0"},
            "created_at": "2024-12-10T08:00:00Z",
            "updated_at": "2024-12-20T17:00:00Z",
            "closed_at": "2024-12-20T17:00:00Z",
        },
        {
            "number": 202,
            "html_url": "https://github.com/org/repo/issues/202",
            "title": "Fix memory leak in authentication service",
            "body": "Memory usage increases over time in auth service",
            "state": "closed",
            "assignees": [{"login": "bob"}],
            "labels": [{"name": "bug"}, {"name": "performance"}],
            "milestone": {"title": "v1.2.0"},
            "created_at": "2024-12-12T10:00:00Z",
            "updated_at": "2024-12-18T14:00:00Z",
            "closed_at": "2024-12-18T14:00:00Z",
        },
        {
            "number": 203,
            "html_url": "https://github.com/org/repo/issues/203",
            "title": "Update authentication documentation",
            "body": "Documentation needs to be updated for new auth flow",
            "state": "closed",
            "assignees": [{"login": "charlie"}],
            "labels": [{"name": "documentation"}],
            "milestone": None,
            "created_at": "2024-12-15T09:00:00Z",
            "updated_at": "2024-12-19T11:00:00Z",
            "closed_at": "2024-12-19T11:00:00Z",
        },
    ]


@pytest.fixture
def backlog_items_from_github(realistic_github_issues: list[dict[str, Any]]) -> list[BacklogItem]:
    """Convert realistic GitHub issues to BacklogItem instances."""
    return [convert_github_issue_to_backlog_item(issue) for issue in realistic_github_issues]


class TestBacklogFilteringIntegration:
    """Integration tests for backlog filtering with GitHub issues."""

    @beartype
    def test_filter_open_issues_only(self, backlog_items_from_github: list[BacklogItem]) -> None:
        """Test filtering to get only open GitHub issues."""
        filtered = _apply_filters(backlog_items_from_github, state="open")

        assert len(filtered) == 3
        assert all(item.state.lower() == "open" for item in filtered)
        assert all(item.id in ["101", "102", "103"] for item in filtered)

    @beartype
    def test_filter_closed_issues_only(self, backlog_items_from_github: list[BacklogItem]) -> None:
        """Test filtering to get only closed GitHub issues."""
        filtered = _apply_filters(backlog_items_from_github, state="closed")

        assert len(filtered) == 3
        assert all(item.state.lower() == "closed" for item in filtered)
        assert all(item.id in ["201", "202", "203"] for item in filtered)

    @beartype
    def test_filter_open_issues_with_feature_label(self, backlog_items_from_github: list[BacklogItem]) -> None:
        """Test filtering open issues with feature label (common workflow)."""
        filtered = _apply_filters(backlog_items_from_github, state="open", labels=["feature"])

        assert len(filtered) == 1
        assert filtered[0].id == "101"
        assert filtered[0].state.lower() == "open"
        assert "feature" in [tag.lower() for tag in filtered[0].tags]

    @beartype
    def test_filter_closed_issues_with_bug_label(self, backlog_items_from_github: list[BacklogItem]) -> None:
        """Test filtering closed issues with bug label (common workflow)."""
        filtered = _apply_filters(backlog_items_from_github, state="closed", labels=["bug"])

        assert len(filtered) == 1
        assert filtered[0].id == "202"
        assert filtered[0].state.lower() == "closed"
        assert "bug" in [tag.lower() for tag in filtered[0].tags]

    @beartype
    def test_filter_by_assignee_alice(self, backlog_items_from_github: list[BacklogItem]) -> None:
        """Test filtering by assignee (alice)."""
        filtered = _apply_filters(backlog_items_from_github, assignee="alice")

        assert len(filtered) == 2
        assert all("alice" in [a.lower() for a in item.assignees] for item in filtered)
        assert all(item.id in ["101", "201"] for item in filtered)

    @beartype
    def test_filter_open_issues_by_assignee(self, backlog_items_from_github: list[BacklogItem]) -> None:
        """Test filtering open issues assigned to specific person."""
        filtered = _apply_filters(backlog_items_from_github, state="open", assignee="bob")

        assert len(filtered) == 1
        assert filtered[0].id == "102"
        assert filtered[0].state.lower() == "open"
        assert "bob" in [a.lower() for a in filtered[0].assignees]

    @beartype
    def test_filter_by_sprint_milestone(self, backlog_items_from_github: list[BacklogItem]) -> None:
        """Test filtering by sprint milestone."""
        filtered = _apply_filters(backlog_items_from_github, sprint="Sprint 2025-01")

        assert len(filtered) == 2
        assert all(item.sprint == "Sprint 2025-01" for item in filtered)
        assert all(item.id in ["101", "103"] for item in filtered)

    @beartype
    def test_filter_by_release_milestone(self, backlog_items_from_github: list[BacklogItem]) -> None:
        """Test filtering by release milestone."""
        filtered = _apply_filters(backlog_items_from_github, release="v1.2.0")

        assert len(filtered) == 2
        assert all(item.release == "v1.2.0" for item in filtered)
        assert all(item.id in ["201", "202"] for item in filtered)

    @beartype
    def test_filter_open_issues_in_sprint(self, backlog_items_from_github: list[BacklogItem]) -> None:
        """Test filtering open issues in a specific sprint."""
        filtered = _apply_filters(backlog_items_from_github, state="open", sprint="Sprint 2025-01")

        assert len(filtered) == 2
        assert all(item.state.lower() == "open" for item in filtered)
        assert all(item.sprint == "Sprint 2025-01" for item in filtered)
        assert all(item.id in ["101", "103"] for item in filtered)

    @beartype
    def test_filter_closed_issues_in_release(self, backlog_items_from_github: list[BacklogItem]) -> None:
        """Test filtering closed issues in a specific release."""
        filtered = _apply_filters(backlog_items_from_github, state="closed", release="v1.2.0")

        assert len(filtered) == 2
        assert all(item.state.lower() == "closed" for item in filtered)
        assert all(item.release == "v1.2.0" for item in filtered)
        assert all(item.id in ["201", "202"] for item in filtered)

    @beartype
    def test_filter_multiple_labels(self, backlog_items_from_github: list[BacklogItem]) -> None:
        """Test filtering by multiple labels (OR logic)."""
        filtered = _apply_filters(backlog_items_from_github, labels=["feature", "bug"])

        assert len(filtered) == 4
        assert all(
            any(label in [tag.lower() for tag in item.tags] for label in ["feature", "bug"]) for item in filtered
        )
        assert all(item.id in ["101", "102", "201", "202"] for item in filtered)

    @beartype
    def test_filter_open_issues_with_priority_high(self, backlog_items_from_github: list[BacklogItem]) -> None:
        """Test filtering open issues with priority-high label."""
        filtered = _apply_filters(backlog_items_from_github, state="open", labels=["priority-high"])

        assert len(filtered) == 2
        assert all(item.state.lower() == "open" for item in filtered)
        assert all("priority-high" in [tag.lower() for tag in item.tags] for item in filtered)
        assert all(item.id in ["101", "102"] for item in filtered)

    @beartype
    def test_filter_complex_combination(self, backlog_items_from_github: list[BacklogItem]) -> None:
        """Test complex filter combination: open + feature + assigned to alice."""
        filtered = _apply_filters(backlog_items_from_github, state="open", labels=["feature"], assignee="alice")

        assert len(filtered) == 1
        assert filtered[0].id == "101"
        assert filtered[0].state.lower() == "open"
        assert "feature" in [tag.lower() for tag in filtered[0].tags]
        assert "alice" in [a.lower() for a in filtered[0].assignees]

    @beartype
    def test_filter_no_matches(self, backlog_items_from_github: list[BacklogItem]) -> None:
        """Test filter combination that matches no items."""
        filtered = _apply_filters(backlog_items_from_github, state="open", labels=["documentation"], assignee="alice")

        assert len(filtered) == 0

    @beartype
    def test_filter_case_insensitive_github_issues(self, backlog_items_from_github: list[BacklogItem]) -> None:
        """Test that filtering works case-insensitively with GitHub issues."""
        filtered_upper = _apply_filters(backlog_items_from_github, state="OPEN", labels=["FEATURE"])
        filtered_lower = _apply_filters(backlog_items_from_github, state="open", labels=["feature"])

        assert len(filtered_upper) == len(filtered_lower)
        assert len(filtered_upper) == 1  # One open issue with feature label (AND logic: state AND labels)

    @beartype
    def test_filter_preserves_all_item_fields(self, backlog_items_from_github: list[BacklogItem]) -> None:
        """Test that filtering preserves all BacklogItem fields."""
        original_item = backlog_items_from_github[0]
        filtered = _apply_filters([original_item], state="open")

        assert len(filtered) == 1
        filtered_item = filtered[0]

        # Verify all fields are preserved
        assert filtered_item.id == original_item.id
        assert filtered_item.provider == original_item.provider
        assert filtered_item.url == original_item.url
        assert filtered_item.title == original_item.title
        assert filtered_item.body_markdown == original_item.body_markdown
        assert filtered_item.state == original_item.state
        assert filtered_item.assignees == original_item.assignees
        assert filtered_item.tags == original_item.tags
        assert filtered_item.sprint == original_item.sprint
        assert filtered_item.release == original_item.release
