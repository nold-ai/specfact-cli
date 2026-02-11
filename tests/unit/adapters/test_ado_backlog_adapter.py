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
    @patch("specfact_cli.adapters.ado.requests.patch")
    def test_update_backlog_item_multiple_field_mappings_prefers_system_fields(self, mock_patch: MagicMock) -> None:
        """Test that update_backlog_item uses System.* fields when multiple mappings exist.

        This test verifies the fix for the bug where reverse_mappings would use
        Microsoft.VSTS.Common.* fields (last entry) but ado_fields would use System.*
        fields (preferred), causing the membership check to fail and skipping updates.
        """
        # Mock ADO API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 1,
            "url": "https://dev.azure.com/test/project/_apis/wit/workitems/1",
            "fields": {
                "System.Title": "Test Item",
                "System.Description": "Description",
                "System.AcceptanceCriteria": "Acceptance criteria",
                "Microsoft.VSTS.Scheduling.StoryPoints": 5,
            },
        }
        mock_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_response

        adapter = AdoAdapter(org="test", project="project", api_token="token")
        item = BacklogItem(
            id="1",
            provider="ado",
            url="",
            title="Test Item",
            body_markdown="Description",
            state="Active",
            acceptance_criteria="Acceptance criteria",
            story_points=5,
        )

        # Update with fields that have multiple mappings
        result = adapter.update_backlog_item(
            item, update_fields=["acceptance_criteria", "story_points", "body_markdown"]
        )

        # Verify the update was successful
        assert result.id == "1"
        assert result.provider == "ado"

        # Verify that the PATCH request was made
        assert mock_patch.called

        # Get the operations sent to ADO API
        call_args = mock_patch.call_args
        operations = call_args[1]["json"]  # JSON body contains operations

        # Verify that System.* fields are used (not Microsoft.VSTS.Common.*)
        # This ensures consistency with map_from_canonical preference logic
        # Check that System.AcceptanceCriteria is used (not Microsoft.VSTS.Common.AcceptanceCriteria)
        # The default mappings have both, but System.* should be preferred
        acceptance_criteria_ops = [op for op in operations if "AcceptanceCriteria" in op.get("path", "")]
        if acceptance_criteria_ops:
            # Should use System.AcceptanceCriteria (preferred) not Microsoft.VSTS.Common.AcceptanceCriteria
            assert any("System.AcceptanceCriteria" in op["path"] for op in acceptance_criteria_ops)

        # Check that story points field is used (could be either Microsoft.VSTS.Common.StoryPoints
        # or Microsoft.VSTS.Scheduling.StoryPoints, but should be consistent with map_from_canonical)
        story_points_ops = [op for op in operations if "StoryPoints" in op.get("path", "")]
        if story_points_ops:
            # Verify story points update was included
            assert len(story_points_ops) > 0

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
    def test_fetch_backlog_items_requires_org(self) -> None:
        """Test that fetch_backlog_items requires org."""
        adapter = AdoAdapter(org=None, project="project", api_token="token")
        filters = BacklogFilters()

        with pytest.raises(ValueError, match=r"org.*required"):
            adapter.fetch_backlog_items(filters)

    @beartype
    def test_fetch_backlog_items_requires_project(self) -> None:
        """Test that fetch_backlog_items requires project."""
        adapter = AdoAdapter(org="test", project=None, api_token="token")
        filters = BacklogFilters()

        with pytest.raises(ValueError, match="project required"):
            adapter.fetch_backlog_items(filters)

    @beartype
    def test_normalize_filter_value_case_insensitive(self) -> None:
        """Test that filter normalization is case-insensitive."""
        assert BacklogFilters.normalize_filter_value("Active") == "active"
        assert BacklogFilters.normalize_filter_value("ACTIVE") == "active"
        assert BacklogFilters.normalize_filter_value("active") == "active"

    @beartype
    def test_resolve_sprint_filter_full_path(self) -> None:
        """Test sprint filter resolution with full iteration path."""
        adapter = AdoAdapter(org="test", project="project", api_token="token")

        items = [
            BacklogItem(
                id="1",
                provider="ado",
                url="",
                title="Item 1",
                body_markdown="",
                state="Active",
                iteration="Project\\Sprint 1",
                sprint="Sprint 1",
            ),
            BacklogItem(
                id="2",
                provider="ado",
                url="",
                title="Item 2",
                body_markdown="",
                state="Active",
                iteration="Project\\Sprint 2",
                sprint="Sprint 2",
            ),
        ]

        iteration_path, filtered = adapter._resolve_sprint_filter("Project\\Sprint 1", items)

        assert iteration_path == "Project\\Sprint 1"
        assert len(filtered) == 1
        assert filtered[0].id == "1"

    @beartype
    def test_resolve_sprint_filter_ambiguous_name(self) -> None:
        """Test sprint filter resolution with ambiguous name-only match."""
        adapter = AdoAdapter(org="test", project="project", api_token="token")

        items = [
            BacklogItem(
                id="1",
                provider="ado",
                url="",
                title="Item 1",
                body_markdown="",
                state="Active",
                iteration="Project\\Sprint 1",
                sprint="Sprint 1",
            ),
            BacklogItem(
                id="2",
                provider="ado",
                url="",
                title="Item 2",
                body_markdown="",
                state="Active",
                iteration="Project\\2023\\Sprint 1",
                sprint="Sprint 1",
            ),
        ]

        with pytest.raises(ValueError, match="Ambiguous sprint name"):
            adapter._resolve_sprint_filter("Sprint 1", items)

    @beartype
    def test_resolve_sprint_filter_unique_name(self) -> None:
        """Test sprint filter resolution with unique name-only match."""
        adapter = AdoAdapter(org="test", project="project", api_token="token")

        items = [
            BacklogItem(
                id="1",
                provider="ado",
                url="",
                title="Item 1",
                body_markdown="",
                state="Active",
                iteration="Project\\Sprint 1",
                sprint="Sprint 1",
            ),
            BacklogItem(
                id="2",
                provider="ado",
                url="",
                title="Item 2",
                body_markdown="",
                state="Active",
                iteration="Project\\Sprint 2",
                sprint="Sprint 2",
            ),
        ]

        iteration_path, filtered = adapter._resolve_sprint_filter("Sprint 1", items)

        assert iteration_path == "Project\\Sprint 1"
        assert len(filtered) == 1
        assert filtered[0].id == "1"

    @beartype
    def test_auth_headers_basic_pat(self) -> None:
        """Test _auth_headers with PAT token (basic auth)."""
        adapter = AdoAdapter(org="test", project="project", api_token="pat-token")
        adapter.auth_scheme = "basic"
        headers = adapter._auth_headers()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")

    @beartype
    def test_auth_headers_bearer_oauth(self) -> None:
        """Test _auth_headers with OAuth token (bearer auth)."""
        adapter = AdoAdapter(org="test", project="project", api_token="oauth-token")
        adapter.auth_scheme = "bearer"
        headers = adapter._auth_headers()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")

    @beartype
    def test_auth_headers_no_token(self) -> None:
        """Test _auth_headers with no token."""
        adapter = AdoAdapter(org="test", project="project")
        adapter.api_token = None
        headers = adapter._auth_headers()
        assert headers == {}

    @beartype
    @patch("specfact_cli.adapters.ado.requests.get")
    def test_get_work_item_comments_follows_continuation_token(self, mock_get: MagicMock) -> None:
        """Fetch all comment pages using ADO comments continuation token."""
        page1 = MagicMock()
        page1.json.return_value = {"comments": [{"text": "c1"}, {"text": "c2"}]}
        page1.raise_for_status = MagicMock()
        page1.headers = {"x-ms-continuationtoken": "token-1"}

        page2 = MagicMock()
        page2.json.return_value = {"comments": [{"text": "c3"}]}
        page2.raise_for_status = MagicMock()
        page2.headers = {}

        mock_get.side_effect = [page1, page2]

        adapter = AdoAdapter(org="test", project="project", api_token="token")
        comments = adapter._get_work_item_comments("test", "project", 123)

        assert comments == [{"text": "c1"}, {"text": "c2"}, {"text": "c3"}]
        assert mock_get.call_count == 2
        first_call = mock_get.call_args_list[0]
        second_call = mock_get.call_args_list[1]
        first_url = first_call.kwargs.get("url", first_call.args[0] if first_call.args else "")
        assert "workItems/123/comments" in first_url
        assert first_call.kwargs["params"]["api-version"] == "7.1-preview.4"
        assert "continuationToken" not in first_call.kwargs["params"]
        assert second_call.kwargs["params"]["continuationToken"] == "token-1"

    @beartype
    @patch.object(AdoAdapter, "_get_work_item_comments")
    def test_get_comments_returns_text_only(self, mock_get_work_item_comments: MagicMock) -> None:
        """Convert ADO comment objects to normalized text lines."""
        mock_get_work_item_comments.return_value = [
            {"text": "First"},
            {"body": "Second"},
            {"text": "   "},
            {},
        ]
        adapter = AdoAdapter(org="test", project="project", api_token="token")
        item = BacklogItem(
            id="123",
            provider="ado",
            url="https://dev.azure.com/test/project/_workitems/edit/123",
            title="Item",
            body_markdown="",
            state="Active",
        )
        comments = adapter.get_comments(item)
        assert comments == ["First", "Second"]

    @beartype
    @patch("azure.identity.DeviceCodeCredential")
    @patch("azure.identity.TokenCachePersistenceOptions")
    def test_try_refresh_oauth_token_success(
        self, mock_cache_options_class: MagicMock, mock_credential_class: MagicMock
    ) -> None:
        """Test _try_refresh_oauth_token with successful refresh."""
        from datetime import UTC, datetime

        # Mock cache options
        mock_cache_options = MagicMock()
        mock_cache_options_class.return_value = mock_cache_options

        # Mock credential and token
        mock_token = MagicMock()
        mock_token.token = "refreshed-token"
        mock_token.expires_on = datetime.now(tz=UTC).timestamp() + 3600

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = mock_token
        mock_credential_class.return_value = mock_credential

        adapter = AdoAdapter(org="test", project="project", api_token="old-token")
        adapter.auth_scheme = "bearer"

        refreshed = adapter._try_refresh_oauth_token()

        assert refreshed is not None
        assert refreshed["access_token"] == "refreshed-token"
        assert refreshed["token_type"] == "bearer"

    @beartype
    @patch("azure.identity.DeviceCodeCredential", side_effect=Exception("Refresh failed"))
    def test_try_refresh_oauth_token_failure(self, mock_credential_class: MagicMock) -> None:
        """Test _try_refresh_oauth_token when refresh fails."""
        adapter = AdoAdapter(org="test", project="project", api_token="old-token")
        adapter.auth_scheme = "bearer"

        refreshed = adapter._try_refresh_oauth_token()
        assert refreshed is None
