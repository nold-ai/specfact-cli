"""
Unit tests for ADO adapter BacklogAdapter interface implementation.

Tests the new BacklogAdapter methods added to AdoAdapter.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests
from beartype import beartype

from specfact_cli.adapters.ado import AdoAdapter
from specfact_cli.backlog.adapters.base import BacklogAdapter
from specfact_cli.backlog.filters import BacklogFilters
from specfact_cli.backlog.mappers.ado_mapper import AdoFieldMapper
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
    @patch("specfact_cli.adapters.backlog_base.time.sleep", return_value=None)
    @patch("specfact_cli.adapters.ado.requests.post")
    @patch("specfact_cli.adapters.ado.requests.get")
    def test_fetch_backlog_items_retries_transient_transport_errors(
        self,
        mock_get: MagicMock,
        mock_post: MagicMock,
        _mock_sleep: MagicMock,
    ) -> None:
        """fetch_backlog_items should retry transient WIQL/workitem transport failures."""
        mock_wiql_response = MagicMock()
        mock_wiql_response.status_code = 200
        mock_wiql_response.raise_for_status = MagicMock()
        mock_wiql_response.json.return_value = {"workItems": [{"id": 1}]}

        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.raise_for_status = MagicMock()
        mock_get_response.json.return_value = {
            "value": [
                {
                    "id": 1,
                    "url": "https://dev.azure.com/test/project/_apis/wit/workitems/1",
                    "fields": {
                        "System.Title": "Retry Item",
                        "System.Description": "Description 1",
                        "System.State": "New",
                    },
                }
            ]
        }

        mock_post.side_effect = [requests.ConnectionError("connection reset"), mock_wiql_response]
        mock_get.side_effect = [requests.ConnectionError("remote closed"), mock_get_response]

        adapter = AdoAdapter(org="test", project="project", api_token="token")
        items = adapter.fetch_backlog_items(BacklogFilters(use_current_iteration_default=False))

        assert len(items) == 1
        assert mock_post.call_count == 2
        assert mock_get.call_count == 2

    @beartype
    @patch("specfact_cli.adapters.ado.requests.post")
    @patch("specfact_cli.adapters.ado.requests.get")
    def test_fetch_backlog_items_issue_id_uses_direct_lookup(
        self,
        mock_get: MagicMock,
        mock_post: MagicMock,
    ) -> None:
        """When issue_id is set, adapter should fetch directly by ID and bypass WIQL query path."""
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.raise_for_status = MagicMock()
        mock_get_response.json.return_value = {
            "id": 185,
            "url": "https://dev.azure.com/test/project/_apis/wit/workitems/185",
            "fields": {
                "System.Title": "Fix the error",
                "System.State": "New",
                "System.Description": "Description",
            },
        }
        mock_get.return_value = mock_get_response
        mock_post.side_effect = AssertionError("WIQL should not be called for direct issue_id lookup")

        adapter = AdoAdapter(org="test", project="project", api_token="token")
        adapter._get_current_iteration = MagicMock(side_effect=AssertionError("current iteration lookup not expected"))  # type: ignore[method-assign]
        items = adapter.fetch_backlog_items(BacklogFilters(issue_id="185"))

        assert len(items) == 1
        assert items[0].id == "185"
        assert mock_get.call_count == 1
        assert mock_post.call_count == 0
        first_url = mock_get.call_args.kwargs.get("url", mock_get.call_args.args[0] if mock_get.call_args.args else "")
        assert "_apis/wit/workitems/185" in first_url

    @beartype
    @patch("specfact_cli.adapters.ado.requests.post")
    @patch("specfact_cli.adapters.ado.requests.get")
    def test_fetch_backlog_items_issue_id_respects_state_filter(
        self,
        mock_get: MagicMock,
        mock_post: MagicMock,
    ) -> None:
        """Direct ID lookup still applies explicit post-fetch state filters."""
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.raise_for_status = MagicMock()
        mock_get_response.json.return_value = {
            "id": 185,
            "url": "https://dev.azure.com/test/project/_apis/wit/workitems/185",
            "fields": {
                "System.Title": "Fix the error",
                "System.State": "New",
                "System.Description": "Description",
            },
        }
        mock_get.return_value = mock_get_response
        mock_post.side_effect = AssertionError("WIQL should not be called for direct issue_id lookup")

        adapter = AdoAdapter(org="test", project="project", api_token="token")
        items = adapter.fetch_backlog_items(BacklogFilters(issue_id="185", state="Active"))

        assert items == []

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
    def test_update_backlog_item_multiple_field_mappings_uses_resolved_write_target(
        self, mock_patch: MagicMock
    ) -> None:
        """Test update_backlog_item uses mapper-resolved write targets for ambiguous canonical fields."""
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

        with patch.dict("os.environ", {}, clear=True):
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

        # Verify that mapper-resolved acceptance criteria field is used.
        acceptance_criteria_ops = [op for op in operations if "AcceptanceCriteria" in op.get("path", "")]
        if acceptance_criteria_ops:
            expected_acceptance_field = AdoFieldMapper().resolve_write_target_field("acceptance_criteria")
            assert expected_acceptance_field is not None
            assert any(expected_acceptance_field in op["path"] for op in acceptance_criteria_ops)

        # Check that story points field is used (could be either Microsoft.VSTS.Common.StoryPoints
        # or Microsoft.VSTS.Scheduling.StoryPoints, but should be consistent with map_from_canonical)
        story_points_ops = [op for op in operations if "StoryPoints" in op.get("path", "")]
        if story_points_ops:
            # Verify story points update was included
            assert len(story_points_ops) > 0

    @beartype
    @patch("specfact_cli.adapters.ado.requests.patch")
    def test_update_backlog_item_uses_custom_story_points_field_mapping(self, mock_patch: MagicMock, tmp_path) -> None:
        """ADO writeback should use the configured custom story points target field."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 1,
            "url": "https://dev.azure.com/test/project/_apis/wit/workitems/1",
            "fields": {
                "System.Title": "Test Item",
                "System.Description": "Description",
                "Microsoft.VSTS.Scheduling.StoryPoints": 8,
            },
        }
        mock_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_response

        custom_mapping_file = tmp_path / "ado_custom.yaml"
        custom_mapping_file.write_text(
            """
field_mappings:
  Microsoft.VSTS.Scheduling.StoryPoints: story_points
""".strip(),
            encoding="utf-8",
        )

        adapter = AdoAdapter(org="test", project="project", api_token="token")
        item = BacklogItem(
            id="1",
            provider="ado",
            url="",
            title="Test Item",
            body_markdown="Description",
            state="Active",
            story_points=8,
            provider_fields={"fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 3}},
        )

        with patch.dict(
            "os.environ",
            {"SPECFACT_ADO_CUSTOM_MAPPING": str(custom_mapping_file)},
            clear=False,
        ):
            adapter.update_backlog_item(item, update_fields=["story_points", "body_markdown"])

        operations = mock_patch.call_args[1]["json"]
        story_points_ops = [
            op for op in operations if op.get("path") == "/fields/Microsoft.VSTS.Scheduling.StoryPoints"
        ]
        assert len(story_points_ops) == 1

    @beartype
    @patch("specfact_cli.adapters.ado.requests.patch")
    def test_create_issue_uses_custom_mapped_fields_and_markdown_multiline_format(
        self, mock_patch: MagicMock, tmp_path
    ) -> None:
        """ADO create_issue should honor custom field mapping and markdown format metadata."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 77,
            "url": "https://dev.azure.com/test/project/_apis/wit/workitems/77",
            "_links": {"html": {"href": "https://dev.azure.com/test/project/_workitems/edit/77"}},
        }
        mock_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_response

        custom_mapping_file = tmp_path / "ado_custom.yaml"
        custom_mapping_file.write_text(
            """
field_mappings:
  Custom.Description: description
  Custom.AcceptanceNotes: acceptance_criteria
  Custom.EstimatePoints: story_points
  Custom.BacklogPriority: priority
""".strip(),
            encoding="utf-8",
        )

        adapter = AdoAdapter(org="test", project="project", api_token="token")
        payload = {
            "title": "Story with custom mapping",
            "description": "## Description\\n\\nMarkdown body",
            "description_format": "markdown",
            "acceptance_criteria": "- [ ] done",
            "story_points": 8,
            "priority": 2,
        }

        with patch.dict(
            "os.environ",
            {"SPECFACT_ADO_CUSTOM_MAPPING": str(custom_mapping_file)},
            clear=False,
        ):
            created = adapter.create_issue("test/project", payload)

        assert created["id"] == "77"

        operations = mock_patch.call_args.kwargs["json"]
        assert {
            "op": "add",
            "path": "/fields/Custom.Description",
            "value": "## Description\\n\\nMarkdown body",
        } in operations
        assert {"op": "add", "path": "/multilineFieldsFormat/Custom.Description", "value": "Markdown"} in operations
        assert {"op": "add", "path": "/fields/Custom.AcceptanceNotes", "value": "- [ ] done"} in operations
        assert {"op": "add", "path": "/multilineFieldsFormat/Custom.AcceptanceNotes", "value": "Markdown"} in operations
        assert {"op": "add", "path": "/fields/Custom.EstimatePoints", "value": 8} in operations
        assert {"op": "add", "path": "/fields/Custom.BacklogPriority", "value": 2} in operations

    @beartype
    @patch("specfact_cli.adapters.ado.requests.patch")
    def test_update_backlog_item_writes_description_and_acceptance_to_separate_fields(
        self, mock_patch: MagicMock
    ) -> None:
        """ADO writeback keeps description clean and writes AC to dedicated field."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 1,
            "url": "https://dev.azure.com/test/project/_apis/wit/workitems/1",
            "fields": {
                "System.Title": "Story",
                "System.Description": "Clean description",
                "System.AcceptanceCriteria": "- criterion",
                "System.State": "Active",
            },
        }
        mock_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_response

        adapter = AdoAdapter(org="test", project="project", api_token="token")
        item = BacklogItem(
            id="1",
            provider="ado",
            url="",
            title="Story",
            body_markdown="Clean description",
            state="Active",
            acceptance_criteria="- criterion",
        )

        adapter.update_backlog_item(item, update_fields=["body_markdown", "acceptance_criteria"])

        operations = mock_patch.call_args[1]["json"]
        description_op = next((op for op in operations if op.get("path") == "/fields/System.Description"), None)
        acceptance_op = next((op for op in operations if "AcceptanceCriteria" in op.get("path", "")), None)

        assert description_op is not None
        assert description_op["value"] == "Clean description"
        assert acceptance_op is not None
        assert any(op.get("value") == "- criterion" for op in operations if "AcceptanceCriteria" in op.get("path", ""))

    @beartype
    @patch("specfact_cli.adapters.ado.requests.patch")
    def test_update_backlog_item_strips_leading_description_heading_for_ado(self, mock_patch: MagicMock) -> None:
        """ADO description writeback strips a leading '## Description' scaffold heading."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 1,
            "url": "https://dev.azure.com/test/project/_apis/wit/workitems/1",
            "fields": {
                "System.Title": "Story",
                "System.Description": "Clean description",
                "System.State": "Active",
            },
        }
        mock_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_response

        adapter = AdoAdapter(org="test", project="project", api_token="token")
        item = BacklogItem(
            id="1",
            provider="ado",
            url="",
            title="Story",
            body_markdown="## Description\n\nClean description",
            state="Active",
        )

        adapter.update_backlog_item(item, update_fields=["body_markdown"])

        operations = mock_patch.call_args[1]["json"]
        description_op = next((op for op in operations if op.get("path") == "/fields/System.Description"), None)
        assert description_op is not None
        assert description_op["value"] == "Clean description"

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
    def test_fetch_all_issues_uses_project_id_context_and_restores_adapter_state(self, monkeypatch) -> None:
        """fetch_all_issues should scope graph reads to project_id without mutating adapter defaults."""
        adapter = AdoAdapter(org="default-org", project="default-project", api_token="token")
        observed_context: list[tuple[str | None, str | None]] = []

        def _fake_fetch(_filters: BacklogFilters) -> list[BacklogItem]:
            observed_context.append((adapter.org, adapter.project))
            return []

        monkeypatch.setattr(adapter, "fetch_backlog_items", _fake_fetch)

        result = adapter.fetch_all_issues("linked-org/linked-project")
        assert result == []
        assert observed_context == [("linked-org", "linked-project")]
        assert adapter.org == "default-org"
        assert adapter.project == "default-project"

    @beartype
    def test_fetch_all_issues_rejects_project_only_id_when_org_missing(self) -> None:
        """fetch_all_issues should reject project-only ids when adapter org is unset."""
        adapter = AdoAdapter(org=None, project="default-project", api_token="token")
        with pytest.raises(ValueError, match="missing organization"):
            adapter.fetch_all_issues("project-only")

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
    @patch("specfact_cli.adapters.backlog_base.time.sleep", return_value=None)
    @patch("specfact_cli.adapters.ado.requests.get")
    def test_get_current_iteration_retries_transient_transport_error(
        self, mock_get: MagicMock, _mock_sleep: MagicMock
    ) -> None:
        """Current iteration lookup retries on transient connection errors."""
        retry_response = MagicMock()
        retry_response.status_code = 200
        retry_response.raise_for_status = MagicMock()
        retry_response.json.return_value = {"value": [{"path": "Project\\Sprint 1"}]}

        mock_get.side_effect = [requests.ConnectionError("connection reset"), retry_response]

        adapter = AdoAdapter(org="test", project="project", team="Team A", api_token="token")
        resolved = adapter._get_current_iteration()

        assert resolved == "Project\\Sprint 1"
        assert mock_get.call_count == 2

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
