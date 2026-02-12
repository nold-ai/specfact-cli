"""
Unit tests for GitHub adapter BacklogAdapter interface implementation.

Tests the new BacklogAdapter methods added to GitHubAdapter.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from beartype import beartype

from specfact_cli.adapters.github import GitHubAdapter
from specfact_cli.backlog.adapters.base import BacklogAdapter
from specfact_cli.backlog.filters import BacklogFilters
from specfact_cli.models.backlog_item import BacklogItem


class TestGitHubBacklogAdapter:
    """Test GitHub adapter BacklogAdapter interface."""

    @beartype
    def test_github_adapter_implements_backlog_adapter(self) -> None:
        """Test that GitHubAdapter implements BacklogAdapter interface."""
        adapter = GitHubAdapter(repo_owner="test", repo_name="repo", api_token="token")
        assert isinstance(adapter, BacklogAdapter)

    @beartype
    def test_github_adapter_name(self) -> None:
        """Test adapter name method."""
        adapter = GitHubAdapter(repo_owner="test", repo_name="repo", api_token="token")
        assert adapter.name() == "github"

    @beartype
    def test_github_adapter_supports_format_markdown(self) -> None:
        """Test supports_format for markdown."""
        adapter = GitHubAdapter(repo_owner="test", repo_name="repo", api_token="token")
        assert adapter.supports_format("markdown") is True
        assert adapter.supports_format("MARKDOWN") is True

    @beartype
    def test_github_adapter_supports_format_other(self) -> None:
        """Test supports_format for other formats."""
        adapter = GitHubAdapter(repo_owner="test", repo_name="repo", api_token="token")
        assert adapter.supports_format("yaml") is False
        assert adapter.supports_format("json") is False

    @beartype
    @patch("specfact_cli.adapters.github.requests.get")
    def test_fetch_backlog_items_with_state_filter(self, mock_get: MagicMock) -> None:
        """Test fetching items with state filter."""
        # Mock GitHub Search API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                {
                    "number": 1,
                    "html_url": "https://github.com/test/repo/issues/1",
                    "title": "Open issue",
                    "body": "Issue body",
                    "state": "open",
                    "assignees": [{"login": "alice"}],
                    "labels": [{"name": "feature"}],
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        adapter = GitHubAdapter(repo_owner="test", repo_name="repo", api_token="token")
        filters = BacklogFilters(state="open")
        items = adapter.fetch_backlog_items(filters)

        assert len(items) == 1
        assert items[0].id == "1"
        assert items[0].state == "open"
        assert items[0].provider == "github"

    @beartype
    @patch("specfact_cli.adapters.github.requests.get")
    def test_fetch_backlog_items_with_assignee_filter(self, mock_get: MagicMock) -> None:
        """Test fetching items with assignee filter."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": []}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        adapter = GitHubAdapter(repo_owner="test", repo_name="repo", api_token="token")
        filters = BacklogFilters(assignee="alice")
        adapter.fetch_backlog_items(filters)

        # Verify search query includes assignee
        call_args = mock_get.call_args
        assert "assignee:alice" in call_args[1]["params"]["q"]

    @beartype
    @patch("specfact_cli.adapters.github.requests.get")
    def test_fetch_backlog_items_with_me_assignee_uses_at_me_query(self, mock_get: MagicMock) -> None:
        """`me` assignee maps to GitHub provider-relative `@me` search qualifier."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                {
                    "number": 1,
                    "html_url": "https://github.com/test/repo/issues/1",
                    "title": "Issue assigned to current user",
                    "body": "Issue body",
                    "state": "open",
                    "assignees": [{"login": "actual-login"}],
                    "labels": [],
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        adapter = GitHubAdapter(repo_owner="test", repo_name="repo", api_token="token")
        filters = BacklogFilters(assignee="me")
        items = adapter.fetch_backlog_items(filters)

        call_args = mock_get.call_args
        assert "assignee:@me" in call_args[1]["params"]["q"]
        assert len(items) == 1

    @beartype
    @patch("specfact_cli.adapters.github.requests.patch")
    def test_update_backlog_item(self, mock_patch: MagicMock) -> None:
        """Test updating a backlog item."""
        # Mock GitHub API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "number": 1,
            "html_url": "https://github.com/test/repo/issues/1",
            "title": "Updated Title",
            "body": "Updated body",
            "state": "closed",
            "assignees": [],
            "labels": [],
        }
        mock_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_response

        adapter = GitHubAdapter(repo_owner="test", repo_name="repo", api_token="token")
        item = BacklogItem(
            id="1", provider="github", url="", title="Updated Title", body_markdown="Updated body", state="closed"
        )

        result = adapter.update_backlog_item(item, update_fields=["title", "body_markdown"])

        assert result.id == "1"
        assert result.title == "Updated Title"
        assert result.body_markdown == "Updated body"
        assert result.state == "closed"

    @beartype
    @patch("specfact_cli.adapters.github.requests.patch")
    def test_update_backlog_item_uses_item_fields_when_structured_body_lacks_core_sections(
        self, mock_patch: MagicMock
    ) -> None:
        """Structured body with non-core headings still writes canonical fields."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "number": 1,
            "html_url": "https://github.com/test/repo/issues/1",
            "title": "Updated Title",
            "body": "Updated body",
            "state": "open",
            "assignees": [],
            "labels": [],
        }
        mock_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_response

        adapter = GitHubAdapter(repo_owner="test", repo_name="repo", api_token="token")
        item = BacklogItem(
            id="1",
            provider="github",
            url="",
            title="Updated Title",
            body_markdown="Refined description\n\n## Notes\n\nextra context",
            state="open",
            acceptance_criteria="- must split fields",
            story_points=5,
            business_value=8,
            priority=2,
        )

        adapter.update_backlog_item(item, update_fields=["body_markdown"])

        payload = mock_patch.call_args[1]["json"]
        body = payload["body"]
        assert "## Acceptance Criteria" in body
        assert "- must split fields" in body
        assert "## Story Points" in body
        assert "## Business Value" in body
        assert "## Priority" in body

    @beartype
    def test_validate_round_trip(self) -> None:
        """Test validate_round_trip method."""
        adapter = GitHubAdapter(repo_owner="test", repo_name="repo", api_token="token")
        original = BacklogItem(id="1", provider="github", url="", title="Test", body_markdown="Body", state="open")
        updated = BacklogItem(id="1", provider="github", url="", title="Test", body_markdown="Body", state="open")

        assert adapter.validate_round_trip(original, updated) is True

    @beartype
    def test_fetch_backlog_items_requires_token(self) -> None:
        """Test that fetch_backlog_items requires API token."""
        # Create adapter without token
        adapter = GitHubAdapter(repo_owner="test", repo_name="repo")
        # Ensure api_token is None
        adapter.api_token = None
        filters = BacklogFilters()

        with pytest.raises(ValueError, match="GitHub API token required"):
            adapter.fetch_backlog_items(filters)

    @beartype
    def test_fetch_backlog_items_requires_repo(self) -> None:
        """Test that fetch_backlog_items requires repo_owner and repo_name."""
        adapter = GitHubAdapter(repo_owner=None, repo_name=None, api_token="token")
        filters = BacklogFilters()

        with pytest.raises(ValueError, match="repo_owner and repo_name required"):
            adapter.fetch_backlog_items(filters)
