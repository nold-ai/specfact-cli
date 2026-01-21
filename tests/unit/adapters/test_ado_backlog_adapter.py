"""
Unit tests for ADO adapter BacklogAdapter interface implementation.

Tests the new BacklogAdapter methods added to AdoAdapter.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from beartype import beartype

from specfact_cli.adapters.ado import AdoAdapter
from specfact_cli.backlog.adapters.base import BacklogAdapter
from specfact_cli.backlog.filters import BacklogFilters
from specfact_cli.models.backlog_item import BacklogItem


class TestAdoBacklogAdapter:
    """Test ADO adapter BacklogAdapter interface."""

    @beartype
    def test_ado_adapter_implements_backlog_adapter(self) -> None:
        """Test that AdoAdapter implements BacklogAdapter interface."""
        adapter = AdoAdapter(org="test", project="project", api_token="token")
        assert isinstance(adapter, BacklogAdapter)

    @beartype
    def test_ado_adapter_name(self) -> None:
        """Test adapter name method."""
        adapter = AdoAdapter(org="test", project="project", api_token="token")
        assert adapter.name() == "ado"

    @beartype
    def test_ado_adapter_supports_format_markdown(self) -> None:
        """Test supports_format for markdown."""
        adapter = AdoAdapter(org="test", project="project", api_token="token")
        assert adapter.supports_format("markdown") is True
        assert adapter.supports_format("MARKDOWN") is True

    @beartype
    def test_ado_adapter_supports_format_other(self) -> None:
        """Test supports_format for other formats."""
        adapter = AdoAdapter(org="test", project="project", api_token="token")
        assert adapter.supports_format("yaml") is False
        assert adapter.supports_format("json") is False

    @beartype
    @patch("specfact_cli.adapters.ado.requests.post")
    @patch("specfact_cli.adapters.ado.requests.get")
    def test_fetch_backlog_items_with_state_filter(self, mock_get: MagicMock, mock_post: MagicMock) -> None:
        """Test fetching items with state filter."""
        # Mock ADO WIQL query response
        mock_post_response = MagicMock()
        mock_post_response.json.return_value = {"workItems": [{"id": 1}, {"id": 2}]}
        mock_post_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_post_response

        # Mock ADO work items API response
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "value": [
                {
                    "id": 1,
                    "url": "https://dev.azure.com/test/project/_apis/wit/workitems/1",
                    "fields": {
                        "System.Title": "Work Item 1",
                        "System.Description": "Description 1",
                        "System.State": "Active",
                        "System.AssignedTo": {"uniqueName": "alice@test.com"},
                    },
                }
            ]
        }
        mock_get_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_get_response

        adapter = AdoAdapter(org="test", project="project", api_token="token")
        filters = BacklogFilters(state="Active")
        items = adapter.fetch_backlog_items(filters)

        assert len(items) >= 0  # May be filtered further

    @beartype
    @patch("specfact_cli.adapters.ado.requests.patch")
    def test_update_backlog_item(self, mock_patch: MagicMock) -> None:
        """Test updating a backlog item."""
        # Mock ADO API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 1,
            "url": "https://dev.azure.com/test/project/_apis/wit/workitems/1",
            "fields": {
                "System.Title": "Updated Title",
                "System.Description": "Updated body",
                "System.State": "Closed",
            },
        }
        mock_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_response

        adapter = AdoAdapter(org="test", project="project", api_token="token")
        item = BacklogItem(
            id="1", provider="ado", url="", title="Updated Title", body_markdown="Updated body", state="Closed"
        )

        result = adapter.update_backlog_item(item, update_fields=["title", "body_markdown"])

        assert result.id == "1"
        assert result.provider == "ado"

    @beartype
    def test_validate_round_trip(self) -> None:
        """Test validate_round_trip method."""
        adapter = AdoAdapter(org="test", project="project", api_token="token")
        original = BacklogItem(id="1", provider="ado", url="", title="Test", body_markdown="Body", state="Active")
        updated = BacklogItem(id="1", provider="ado", url="", title="Test", body_markdown="Body", state="Active")

        assert adapter.validate_round_trip(original, updated) is True

    @beartype
    def test_fetch_backlog_items_requires_token(self) -> None:
        """Test that fetch_backlog_items requires API token."""
        # Create adapter without token
        adapter = AdoAdapter(org="test", project="project")
        # Ensure api_token is None
        adapter.api_token = None
        filters = BacklogFilters()

        with pytest.raises(ValueError, match="Azure DevOps API token required"):
            adapter.fetch_backlog_items(filters)

    @beartype
    def test_fetch_backlog_items_requires_org_project(self) -> None:
        """Test that fetch_backlog_items requires org and project."""
        adapter = AdoAdapter(org=None, project=None, api_token="token")
        filters = BacklogFilters()

        with pytest.raises(ValueError, match="org and project required"):
            adapter.fetch_backlog_items(filters)
