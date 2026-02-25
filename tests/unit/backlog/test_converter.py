"""
Unit tests for backlog item converters.

Tests conversion of arbitrary DevOps backlog input (GitHub issues, ADO work items) to BacklogItem.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from beartype import beartype
from icontract.errors import ViolationError

from specfact_cli.backlog.converter import convert_ado_work_item_to_backlog_item, convert_github_issue_to_backlog_item


class TestGitHubIssueConverter:
    """Test GitHub issue to BacklogItem conversion."""

    @beartype
    def test_convert_minimal_github_issue(self) -> None:
        """Test converting minimal GitHub issue."""
        issue_data = {
            "number": 123,
            "html_url": "https://github.com/test/repo/issues/123",
            "title": "Test Issue",
            "body": "Issue body",
            "state": "open",
        }

        item = convert_github_issue_to_backlog_item(issue_data)

        assert item.id == "123"
        assert item.provider == "github"
        assert item.url == "https://github.com/test/repo/issues/123"
        assert item.title == "Test Issue"
        assert item.body_markdown == "Issue body"
        assert item.state == "open"

    @beartype
    def test_convert_github_issue_with_assignees(self) -> None:
        """Test converting GitHub issue with assignees."""
        issue_data = {
            "number": 123,
            "html_url": "https://github.com/test/repo/issues/123",
            "title": "Test Issue",
            "body": "",
            "state": "open",
            "assignees": [{"login": "user1"}, {"login": "user2"}],
        }

        item = convert_github_issue_to_backlog_item(issue_data)

        assert item.assignees == ["user1", "user2"]

    @beartype
    def test_convert_github_issue_with_labels(self) -> None:
        """Test converting GitHub issue with labels."""
        issue_data = {
            "number": 123,
            "html_url": "https://github.com/test/repo/issues/123",
            "title": "Test Issue",
            "body": "",
            "state": "open",
            "labels": [{"name": "bug"}, {"name": "priority"}],
        }

        item = convert_github_issue_to_backlog_item(issue_data)

        assert item.tags == ["bug", "priority"]

    @beartype
    def test_convert_arbitrary_github_issue(self) -> None:
        """Test converting arbitrary GitHub issue (typical DevOps input)."""
        # Simulate arbitrary input that DevOps team might create
        issue_data = {
            "number": 456,
            "html_url": "https://github.com/test/repo/issues/456",
            "title": "Need to fix the thing",
            "body": """Hey team,
We need to fix this issue. It's been reported by users.
Can someone look into it?

Thanks!""",
            "state": "open",
            "assignees": [],
            "labels": [],
            "created_at": "2024-01-18T10:30:00Z",
            "updated_at": "2024-01-19T15:45:00Z",
        }

        item = convert_github_issue_to_backlog_item(issue_data)

        assert item.id == "456"
        assert item.title == "Need to fix the thing"
        assert "Hey team" in item.body_markdown
        assert isinstance(item.created_at, datetime)
        assert isinstance(item.updated_at, datetime)

    @beartype
    def test_convert_github_issue_with_sprint_milestone(self) -> None:
        """Test converting GitHub issue with sprint milestone."""
        issue_data = {
            "number": 789,
            "html_url": "https://github.com/test/repo/issues/789",
            "title": "Test Issue",
            "body": "",
            "state": "open",
            "milestone": {"title": "Sprint 1"},
        }

        item = convert_github_issue_to_backlog_item(issue_data)

        assert item.sprint == "Sprint 1"
        assert item.release is None

    @beartype
    def test_convert_github_issue_with_release_milestone(self) -> None:
        """Test converting GitHub issue with release milestone."""
        issue_data = {
            "number": 790,
            "html_url": "https://github.com/test/repo/issues/790",
            "title": "Test Issue",
            "body": "",
            "state": "open",
            "milestone": {"title": "Release 1.0"},
        }

        item = convert_github_issue_to_backlog_item(issue_data)

        assert item.release == "Release 1.0"
        assert item.sprint is None

    @beartype
    def test_convert_github_issue_with_v_release_milestone(self) -> None:
        """Test converting GitHub issue with v-prefixed release milestone."""
        issue_data = {
            "number": 791,
            "html_url": "https://github.com/test/repo/issues/791",
            "title": "Test Issue",
            "body": "",
            "state": "open",
            "milestone": {"title": "v1.0"},
        }

        item = convert_github_issue_to_backlog_item(issue_data)

        assert item.release == "v1.0"
        assert item.sprint is None

    @beartype
    def test_convert_github_issue_missing_required_fields_raises(self) -> None:
        """Test that conversion raises error for missing required fields."""
        issue_data = {
            "title": "Test Issue",
            # Missing number and url
        }

        with pytest.raises((ValueError, ViolationError), match=r"number|id"):
            convert_github_issue_to_backlog_item(issue_data)


class TestADOWorkItemConverter:
    """Test ADO work item to BacklogItem conversion."""

    @beartype
    def test_convert_minimal_ado_work_item(self) -> None:
        """Test converting minimal ADO work item."""
        work_item_data = {
            "id": 789,
            "url": "https://dev.azure.com/org/project/_apis/wit/workitems/789",
            "fields": {
                "System.Title": "Test Work Item",
                "System.Description": "Work item description",
                "System.State": "New",
            },
        }

        item = convert_ado_work_item_to_backlog_item(work_item_data)

        assert item.id == "789"
        assert item.provider == "ado"
        assert item.title == "Test Work Item"
        assert item.body_markdown == "Work item description"
        assert item.state == "new"
        assert item.canonical_url is None

    @beartype
    def test_convert_ado_work_item_converts_html_description_to_markdown(self) -> None:
        """ADO HTML description should be normalized to markdown-like text."""
        work_item_data = {
            "id": 790,
            "url": "https://dev.azure.com/org/project/_apis/wit/workitems/790",
            "fields": {
                "System.Title": "HTML Work Item",
                "System.Description": "<h2>Summary</h2><p>This is <strong>important</strong>.</p>",
                "System.State": "Active",
            },
        }

        item = convert_ado_work_item_to_backlog_item(work_item_data)

        assert "## Summary" in item.body_markdown
        assert "**important**" in item.body_markdown

    @beartype
    def test_convert_ado_work_item_with_assignee(self) -> None:
        """Test converting ADO work item with assignee."""
        work_item_data = {
            "id": 789,
            "url": "https://dev.azure.com/org/project/_apis/wit/workitems/789",
            "fields": {
                "System.Title": "Test Work Item",
                "System.Description": "",
                "System.State": "New",
                "System.AssignedTo": {"displayName": "John Doe", "uniqueName": "john@example.com"},
            },
        }

        item = convert_ado_work_item_to_backlog_item(work_item_data)

        assert item.assignees == ["John Doe", "john@example.com"]  # Both displayName and uniqueName extracted

    @beartype
    def test_convert_ado_work_item_with_assignee_displayname_only(self) -> None:
        """Test converting ADO work item with assignee having only displayName."""
        work_item_data = {
            "id": 790,
            "url": "https://dev.azure.com/org/project/_apis/wit/workitems/790",
            "fields": {
                "System.Title": "Test Work Item",
                "System.Description": "",
                "System.State": "New",
                "System.AssignedTo": {"displayName": "Jane Smith"},
            },
        }

        item = convert_ado_work_item_to_backlog_item(work_item_data)

        assert item.assignees == ["Jane Smith"]

    @beartype
    def test_convert_ado_work_item_with_assignee_unique_name_only(self) -> None:
        """Test converting ADO work item with assignee having only uniqueName."""
        work_item_data = {
            "id": 791,
            "url": "https://dev.azure.com/org/project/_apis/wit/workitems/791",
            "fields": {
                "System.Title": "Test Work Item",
                "System.Description": "",
                "System.State": "New",
                "System.AssignedTo": {"uniqueName": "user@example.com"},
            },
        }

        item = convert_ado_work_item_to_backlog_item(work_item_data)

        assert item.assignees == ["user@example.com"]

    @beartype
    def test_convert_ado_work_item_with_assignee_mail(self) -> None:
        """Test converting ADO work item with assignee having mail field."""
        work_item_data = {
            "id": 792,
            "url": "https://dev.azure.com/org/project/_apis/wit/workitems/792",
            "fields": {
                "System.Title": "Test Work Item",
                "System.Description": "",
                "System.State": "New",
                "System.AssignedTo": {
                    "displayName": "Bob Johnson",
                    "uniqueName": "bob@example.com",
                    "mail": "bob.johnson@example.com",
                },
            },
        }

        item = convert_ado_work_item_to_backlog_item(work_item_data)

        # Should extract all three: displayName, uniqueName, mail
        assert "Bob Johnson" in item.assignees
        assert "bob@example.com" in item.assignees
        assert "bob.johnson@example.com" in item.assignees
        assert len(item.assignees) == 3

    @beartype
    def test_convert_ado_work_item_with_unassigned(self) -> None:
        """Test converting ADO work item with no assignee."""
        work_item_data = {
            "id": 793,
            "url": "https://dev.azure.com/org/project/_apis/wit/workitems/793",
            "fields": {
                "System.Title": "Test Work Item",
                "System.Description": "",
                "System.State": "New",
                # No System.AssignedTo field
            },
        }

        item = convert_ado_work_item_to_backlog_item(work_item_data)

        assert item.assignees == []

    @beartype
    def test_convert_ado_work_item_with_empty_assignee_fields(self) -> None:
        """Test converting ADO work item with empty assignee fields (should filter out empty strings)."""
        work_item_data = {
            "id": 794,
            "url": "https://dev.azure.com/org/project/_apis/wit/workitems/794",
            "fields": {
                "System.Title": "Test Work Item",
                "System.Description": "",
                "System.State": "New",
                "System.AssignedTo": {"displayName": "", "uniqueName": "user@example.com"},  # Empty displayName
            },
        }

        item = convert_ado_work_item_to_backlog_item(work_item_data)

        # Should only include non-empty values (empty displayName is filtered out)
        assert len(item.assignees) == 1
        assert "user@example.com" in item.assignees
        assert "" not in item.assignees  # Empty strings should be filtered out

    @beartype
    def test_convert_arbitrary_ado_work_item(self) -> None:
        """Test converting arbitrary ADO work item (typical DevOps input)."""
        # Simulate arbitrary input that DevOps team might create
        work_item_data = {
            "id": 999,
            "url": "https://dev.azure.com/org/project/_apis/wit/workitems/999",
            "fields": {
                "System.Title": "Fix the bug",
                "System.Description": """This needs to be fixed ASAP.
Users are complaining.
Please prioritize.""",
                "System.State": "Active",
                "System.Tags": "bug;priority;urgent",
                "System.IterationPath": "Project\\Release 1\\Sprint 1",
                "System.AreaPath": "Backend",
                "System.CreatedDate": "2024-01-18T10:30:00Z",
                "System.ChangedDate": "2024-01-19T15:45:00Z",
            },
        }

        item = convert_ado_work_item_to_backlog_item(work_item_data)

        assert item.id == "999"
        assert item.title == "Fix the bug"
        assert "This needs to be fixed" in item.body_markdown
        assert item.tags == ["bug", "priority", "urgent"]
        assert item.iteration == "Project\\Release 1\\Sprint 1"
        assert item.sprint == "Sprint 1"
        assert item.release == "Release 1"
        assert item.area == "Backend"

    @beartype
    def test_convert_ado_work_item_with_sprint_only(self) -> None:
        """Test converting ADO work item with sprint-only iteration path."""
        work_item_data = {
            "id": 1000,
            "url": "https://dev.azure.com/org/project/_apis/wit/workitems/1000",
            "fields": {
                "System.Title": "Test Work Item",
                "System.Description": "",
                "System.State": "New",
                "System.IterationPath": "Project\\Sprint 2",
            },
        }

        item = convert_ado_work_item_to_backlog_item(work_item_data)

        assert item.sprint == "Sprint 2"
        assert item.release is None
        assert item.iteration == "Project\\Sprint 2"

    @beartype
    def test_convert_ado_work_item_missing_required_fields_raises(self) -> None:
        """Test that conversion raises error for missing required fields."""
        work_item_data = {
            "id": 789,
            # Missing url and fields
        }

        with pytest.raises((ValueError, ViolationError), match="url"):
            convert_ado_work_item_to_backlog_item(work_item_data)

    @beartype
    def test_convert_ado_work_item_sets_canonical_url_when_base_org_project_provided(self) -> None:
        """Test that canonical URL is set when base_url, org, and project_name are provided."""
        work_item_data = {
            "id": 42,
            "url": "https://dev.azure.com/myorg/abc123-def456/_apis/wit/workItems/42",
            "fields": {
                "System.Title": "User Story",
                "System.Description": "",
                "System.State": "New",
            },
        }
        item = convert_ado_work_item_to_backlog_item(
            work_item_data,
            base_url="https://dev.azure.com",
            org="myorg",
            project_name="My Project",
        )
        assert item.url == "https://dev.azure.com/myorg/abc123-def456/_apis/wit/workItems/42"
        assert item.canonical_url == "https://dev.azure.com/myorg/My%20Project/_workitems/edit/42"

    @beartype
    def test_convert_ado_work_item_canonical_url_project_name_url_encoded(self) -> None:
        """Test that project name with special characters is URL-encoded in canonical URL."""
        work_item_data = {
            "id": 99,
            "url": "https://dev.azure.com/org/guid/_apis/wit/workItems/99",
            "fields": {"System.Title": "Task", "System.Description": "", "System.State": "Active"},
        }
        item = convert_ado_work_item_to_backlog_item(
            work_item_data,
            base_url="https://dev.azure.com",
            org="myorg",
            project_name="Project/With-Special",
        )
        assert item.canonical_url == "https://dev.azure.com/myorg/Project%2FWith-Special/_workitems/edit/99"
