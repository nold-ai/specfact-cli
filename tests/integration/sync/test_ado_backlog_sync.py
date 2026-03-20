"""
Integration tests for bidirectional backlog sync with Azure DevOps.

Tests end-to-end sync between OpenSpec change proposals and ADO work items,
including bidirectional status synchronization.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from beartype import beartype

from specfact_cli.adapters.ado import AdoAdapter
from specfact_cli.models.bridge import BridgeConfig
from specfact_cli.models.change import ChangeTracking


@pytest.fixture
def ado_adapter() -> AdoAdapter:
    """Create Azure DevOps adapter instance for testing."""
    return AdoAdapter(
        org="test-org",
        project="test-project",
        api_token="test-token",
    )


@pytest.fixture
def bridge_config() -> BridgeConfig:
    """Create Azure DevOps bridge config for testing."""
    return BridgeConfig.preset_ado()


class TestBidirectionalAdoBacklogSync:
    """Integration tests for bidirectional backlog sync with Azure DevOps."""

    @beartype
    @patch("specfact_cli.adapters.ado.requests.get")
    @patch("specfact_cli.adapters.ado.requests.patch")
    def test_openspec_to_ado_export(
        self,
        mock_patch: MagicMock,
        mock_get: MagicMock,
        ado_adapter: AdoAdapter,
        bridge_config: BridgeConfig,
    ) -> None:
        """Test OpenSpec → ADO export (change proposal → ADO work item)."""
        # Mock project API response (for work item type derivation)
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "processTemplate": {
                "templateTypeId": "adcc42ab-9882-485e-a3e4-38fb9b8c5e4e",  # Agile template
            },
        }
        mock_get_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_get_response

        # Mock Azure DevOps API response for work item creation
        mock_patch_response = MagicMock()
        mock_patch_response.json.return_value = {
            "id": 123,
            "_links": {
                "html": {"href": "https://dev.azure.com/test-org/test-project/_workitems/edit/123"},
            },
        }
        mock_patch_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_patch_response

        proposal_data = {
            "change_id": "add-feature-x",
            "title": "Add Feature X",
            "description": "Implement feature X",
            "rationale": "Needed for user workflow",
            "status": "proposed",
        }

        result = ado_adapter.export_artifact(
            artifact_key="change_proposal",
            artifact_data=proposal_data,
            bridge_config=bridge_config,
        )

        assert result["work_item_id"] == 123
        assert result["work_item_url"] == "https://dev.azure.com/test-org/test-project/_workitems/edit/123"
        mock_patch.assert_called_once()

    @beartype
    @patch.object(AdoAdapter, "_get_work_item_comments", return_value=[])
    def test_ado_to_openspec_import(
        self,
        mock_get_comments: MagicMock,
        ado_adapter: AdoAdapter,
        tmp_path: Path,
    ) -> None:
        """Test ADO → OpenSpec import (ADO work item → change proposal)."""
        from unittest.mock import MagicMock

        # Create mock project bundle
        project_bundle = MagicMock()
        project_bundle.change_tracking = ChangeTracking()
        project_bundle.bundle_dir = tmp_path

        work_item_data = {
            "id": 123,
            "fields": {
                "System.Title": "Add Feature X",
                "System.Description": "## Why\n\nNeeded for user workflow\n\n## What Changes\n\nImplement feature X",
                "System.State": "New",
                "System.CreatedDate": "2025-01-01T10:00:00Z",
                "System.WorkItemType": "User Story",
            },
            "_links": {
                "html": {"href": "https://dev.azure.com/test-org/test-project/_workitems/edit/123"},
            },
        }

        ado_adapter.import_artifact(
            artifact_key="ado_work_item",
            artifact_path=work_item_data,
            project_bundle=project_bundle,
        )

        assert "add-feature-x" in project_bundle.change_tracking.proposals
        proposal = project_bundle.change_tracking.proposals["add-feature-x"]
        assert proposal.title == "Add Feature X"
        assert proposal.status == "proposed"
        assert proposal.source_tracking is not None
        assert proposal.source_tracking.tool == "ado"

    @beartype
    @patch("specfact_cli.adapters.ado.requests.patch")
    def test_bidirectional_status_sync(
        self,
        mock_patch: MagicMock,
        ado_adapter: AdoAdapter,
    ) -> None:
        """Test bidirectional status sync (OpenSpec status ↔ ADO state)."""
        # Mock API response for status update
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 123,
            "_links": {
                "html": {"href": "https://dev.azure.com/test-org/test-project/_workitems/edit/123"},
            },
        }
        mock_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_response

        # Sync OpenSpec status to ADO
        proposal_data = {
            "status": "in-progress",
            "source_tracking": {
                "source_id": "123",
                "source_repo": "test-org/test-project",
            },
        }

        result = ado_adapter.export_artifact(
            artifact_key="change_status",
            artifact_data=proposal_data,
        )

        assert result["state"] == "Active"
        mock_patch.assert_called_once()

        # Verify the patch document contains the correct state update
        call_args = mock_patch.call_args
        assert call_args is not None
        patch_document = call_args[1]["json"]
        assert isinstance(patch_document, list)
        state_update = next((op for op in patch_document if op.get("path") == "/fields/System.State"), None)
        assert state_update is not None
        assert state_update["op"] == "replace"
        assert state_update["value"] == "Active"

    @beartype
    def test_status_conflict_resolution(self, ado_adapter: AdoAdapter) -> None:
        """Test conflict resolution when status differs."""
        # Test prefer_openspec strategy
        resolved = ado_adapter.resolve_status_conflict(
            openspec_status="proposed",
            backlog_status="in-progress",
            strategy="prefer_openspec",
        )
        assert resolved == "proposed"

        # Test prefer_backlog strategy
        resolved = ado_adapter.resolve_status_conflict(
            openspec_status="proposed",
            backlog_status="in-progress",
            strategy="prefer_backlog",
        )
        assert resolved == "in-progress"

        # Test merge strategy (most advanced)
        resolved = ado_adapter.resolve_status_conflict(
            openspec_status="proposed",
            backlog_status="in-progress",
            strategy="merge",
        )
        assert resolved == "in-progress"  # in-progress is more advanced than proposed

    @beartype
    @patch("specfact_cli.adapters.ado.requests.get")
    @patch("specfact_cli.adapters.ado.requests.patch")
    def test_round_trip_sync(
        self,
        mock_patch: MagicMock,
        mock_get: MagicMock,
        ado_adapter: AdoAdapter,
        tmp_path: Path,
    ) -> None:
        """Test round-trip sync: export → import maintains data integrity."""
        from unittest.mock import MagicMock

        # Mock project API response (for work item type derivation)
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "processTemplate": {
                "templateTypeId": "adcc42ab-9882-485e-a3e4-38fb9b8c5e4e",  # Agile template
            },
        }
        mock_get_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_get_response

        # Mock Azure DevOps API response for work item creation
        mock_patch_response = MagicMock()
        mock_patch_response.json.return_value = {
            "id": 123,
            "_links": {
                "html": {"href": "https://dev.azure.com/test-org/test-project/_workitems/edit/123"},
            },
        }
        mock_patch_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_patch_response

        # Export proposal to ADO
        original_proposal = {
            "change_id": "add-feature-x",
            "title": "Add Feature X",
            "description": "Implement feature X",
            "rationale": "Needed for user workflow",
            "status": "proposed",
        }

        export_result = ado_adapter.export_artifact(
            artifact_key="change_proposal",
            artifact_data=original_proposal,
        )

        # Simulate ADO work item data (what we'd get from API)
        work_item_data = {
            "id": export_result["work_item_id"],
            "fields": {
                "System.Title": original_proposal["title"],
                "System.Description": f"## Why\n\n{original_proposal['rationale']}\n\n## What Changes\n\n{original_proposal['description']}\n\n---\n*OpenSpec Change Proposal: `{original_proposal['change_id']}`*",
                "System.State": "New",
                "System.CreatedDate": "2025-01-01T10:00:00Z",
                "System.WorkItemType": "User Story",
            },
            "_links": {
                "html": {"href": export_result["work_item_url"]},
            },
        }

        # Import back from ADO
        project_bundle = MagicMock()
        project_bundle.change_tracking = ChangeTracking()
        project_bundle.bundle_dir = tmp_path

        ado_adapter.import_artifact(
            artifact_key="ado_work_item",
            artifact_path=work_item_data,
            project_bundle=project_bundle,
        )

        # Verify imported proposal matches original
        # Import uses change_id from OpenSpec metadata footer, or work item ID as fallback
        imported_key = original_proposal["change_id"]  # Should be "add-feature-x"
        if imported_key not in project_bundle.change_tracking.proposals:
            # Fallback: try work item ID if change_id not found
            imported_key = str(export_result["work_item_id"])

        assert imported_key in project_bundle.change_tracking.proposals
        imported_proposal = project_bundle.change_tracking.proposals[imported_key]
        assert imported_proposal.title == original_proposal["title"]
        assert imported_proposal.description == original_proposal["description"]
        assert imported_proposal.rationale == original_proposal["rationale"]
        assert imported_proposal.status == original_proposal["status"]

    @beartype
    @patch("specfact_cli.adapters.ado.requests.get")
    @patch("specfact_cli.adapters.ado.requests.patch")
    def test_export_only_mode(
        self,
        mock_patch: MagicMock,
        mock_get: MagicMock,
        ado_adapter: AdoAdapter,
        bridge_config: BridgeConfig,
    ) -> None:
        """Test export-only mode with default work item type."""
        # Mock project API response (for work item type derivation)
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "processTemplate": {
                "templateTypeId": "adcc42ab-9882-485e-a3e4-38fb9b8c5e4e",  # Agile template
            },
        }
        mock_get_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_get_response

        # Mock API response for work item creation
        mock_patch_response = MagicMock()
        mock_patch_response.json.return_value = {
            "id": 123,
            "_links": {
                "html": {"href": "https://dev.azure.com/test-org/test-project/_workitems/edit/123"},
            },
        }
        mock_patch_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_patch_response

        proposal_data = {
            "change_id": "add-feature-x",
            "title": "Add Feature X",
            "description": "Implement feature X",
            "rationale": "Needed for user workflow",
            "status": "proposed",
        }

        # Export without explicit work item type (should use default)
        result = ado_adapter.export_artifact(
            artifact_key="change_proposal",
            artifact_data=proposal_data,
            bridge_config=bridge_config,
        )

        assert result["work_item_id"] == 123
        # Verify work item type is used in API call
        call_args = mock_patch.call_args
        assert call_args is not None
        url = call_args[0][0]
        assert "workitems" in url
        # Should use default work item type (User Story) if not explicitly set
        assert "$" in url or "User Story" in url or "Product Backlog Item" in url

    @beartype
    @patch("specfact_cli.adapters.ado.requests.post")
    @patch("specfact_cli.adapters.ado.requests.get")
    @patch("specfact_cli.adapters.ado.requests.patch")
    def test_status_comment_workflow(
        self,
        mock_patch: MagicMock,
        mock_get: MagicMock,
        mock_post: MagicMock,
        ado_adapter: AdoAdapter,
        bridge_config: BridgeConfig,
    ) -> None:
        """Test adding status comments to ADO work items."""
        # Mock work item creation (for initial export)
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "processTemplate": {"templateTypeId": "adcc42ab-9882-485e-a3e4-38fb9b8c5e4e"},  # Agile
        }
        mock_get_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_get_response

        mock_patch_response = MagicMock()
        mock_patch_response.json.return_value = {
            "id": 123,
            "_links": {"html": {"href": "https://dev.azure.com/test-org/test-project/_workitems/edit/123"}},
        }
        mock_patch_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_patch_response

        # Create work item first
        proposal_data: dict[str, Any] = {
            "change_id": "test-change",
            "title": "Test Change",
            "description": "Test description",
            "rationale": "Test rationale",
            "status": "proposed",
        }
        ado_adapter.export_artifact("change_proposal", proposal_data, bridge_config)

        # Mock comment response
        mock_post_response = MagicMock()
        mock_post_response.json.return_value = {"id": 456}
        mock_post_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_post_response

        # Add status comment
        proposal_data["status"] = "applied"
        proposal_data["source_tracking"] = {"source_id": "123", "source_repo": "test-org/test-project"}

        result = ado_adapter.export_artifact("change_proposal_comment", proposal_data, bridge_config)

        assert result["comment_added"] is True
        assert result["work_item_id"] == 123
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        comment_text = call_args[1]["json"]["text"]
        assert "Change applied" in comment_text
        assert "Test Change" in comment_text

    @beartype
    @patch("specfact_cli.adapters.ado.requests.post")
    @patch("specfact_cli.adapters.ado.requests.get")
    @patch("specfact_cli.adapters.ado.requests.patch")
    def test_progress_comment_workflow(
        self,
        mock_patch: MagicMock,
        mock_get: MagicMock,
        mock_post: MagicMock,
        ado_adapter: AdoAdapter,
        bridge_config: BridgeConfig,
    ) -> None:
        """Test adding progress comments to ADO work items."""
        # Mock work item creation
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "processTemplate": {"templateTypeId": "adcc42ab-9882-485e-a3e4-38fb9b8c5e4e"},  # Agile
        }
        mock_get_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_get_response

        mock_patch_response = MagicMock()
        mock_patch_response.json.return_value = {
            "id": 123,
            "_links": {"html": {"href": "https://dev.azure.com/test-org/test-project/_workitems/edit/123"}},
        }
        mock_patch_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_patch_response

        # Create work item first
        proposal_data: dict[str, Any] = {
            "change_id": "test-change",
            "title": "Test Change",
            "description": "Test description",
            "rationale": "Test rationale",
            "status": "proposed",
        }
        ado_adapter.export_artifact("change_proposal", proposal_data, bridge_config)

        # Mock comment response
        mock_post_response = MagicMock()
        mock_post_response.json.return_value = {"id": 789}
        mock_post_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_post_response

        # Add progress comment
        proposal_data["source_tracking"] = {"source_id": "123", "source_repo": "test-org/test-project"}
        proposal_data["progress_data"] = {
            "has_changes": True,
            "commits": [
                {
                    "hash": "abc123",
                    "message": "feat: implement feature",
                    "author": "Test Author",
                    "date": "2025-12-30 10:00:00 +0000",
                    "files": ["src/test.py"],
                }
            ],
            "files_changed": ["src/test.py"],
            "summary": "Detected 1 commit",
            "detection_timestamp": "2025-12-30T10:00:00Z",
        }

        result = ado_adapter.export_artifact("code_change_progress", proposal_data, bridge_config)

        assert result["comment_added"] is True
        assert result["work_item_id"] == 123
        mock_post.assert_called_once()

    @beartype
    @patch("specfact_cli.adapters.ado.requests.get")
    @patch("specfact_cli.adapters.ado.requests.patch")
    def test_sync_status_to_ado_integration(
        self,
        mock_patch: MagicMock,
        mock_get: MagicMock,
        ado_adapter: AdoAdapter,
    ) -> None:
        """Test bidirectional status sync (OpenSpec status ↔ ADO state) - integration test."""
        # Mock get current work item
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "id": 123,
            "fields": {"System.State": "New"},
            "_links": {"html": {"href": "https://dev.azure.com/test-org/test-project/_workitems/edit/123"}},
        }
        mock_get_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_get_response

        # Mock patch state update
        mock_patch_response = MagicMock()
        mock_patch_response.json.return_value = {
            "id": 123,
            "_links": {"html": {"href": "https://dev.azure.com/test-org/test-project/_workitems/edit/123"}},
        }
        mock_patch_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_patch_response

        # Sync OpenSpec status to ADO
        proposal = {
            "status": "in-progress",
            "source_tracking": {"source_id": "123", "source_repo": "test-org/test-project"},
        }

        result = ado_adapter.sync_status_to_ado(
            proposal=proposal,
            org="test-org",
            project="test-project",
        )

        assert result["state_updated"] is True
        assert result["new_state"] == "Active"
        mock_patch.assert_called_once()

        # Sync ADO state to OpenSpec
        work_item_data = {
            "fields": {"System.State": "Active"},
        }

        proposal_dict = {"status": "proposed"}

        resolved_status = ado_adapter.sync_status_from_ado(
            work_item_data=work_item_data,
            proposal=proposal_dict,
            strategy="prefer_backlog",
        )

        assert resolved_status == "in-progress"

    @beartype
    @patch("specfact_cli.adapters.ado.requests.post")
    @patch("specfact_cli.adapters.ado.requests.get")
    @patch("specfact_cli.adapters.ado.requests.patch")
    @patch("specfact_cli.adapters.github.requests.get")
    @patch("specfact_cli.adapters.github.requests.post")
    def test_github_to_openspec_to_ado_workflow(
        self,
        mock_gh_post: MagicMock,
        mock_gh_get: MagicMock,
        mock_ado_patch: MagicMock,
        mock_ado_get: MagicMock,
        mock_ado_post: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test end-to-end workflow: GitHub Issue → OpenSpec → ADO Work Item."""
        from specfact_cli.adapters.github import GitHubAdapter
        from specfact_cli.models.bridge import BridgeConfig
        from specfact_cli.models.change import ChangeTracking

        # Setup: Create OpenSpec repository structure
        openspec_dir = tmp_path / "openspec"
        openspec_dir.mkdir(exist_ok=True)
        (openspec_dir / "project.md").write_text("# Test Project\n\n## Purpose\n\nTest cross-adapter sync")

        # Step 1: Import GitHub Issue → OpenSpec Change Proposal
        github_adapter = GitHubAdapter(
            repo_owner="test-org",
            repo_name="test-repo",
            api_token="test-github-token",
        )

        # Mock GitHub API response for issue
        mock_gh_get_response = MagicMock()
        mock_gh_get_response.json.return_value = {
            "number": 111,
            "title": "Implement SSO Device Code Auth",
            "body": "## Why\n\nNeed SSO support for better security.\n\n## What Changes\n\n- Add device code flow\n- Update auth endpoints\n\n---\n\n*OpenSpec Change Proposal: `implement-sso-device-code-auth`*",
            "html_url": "https://github.com/test-org/test-repo/issues/111",
            "state": "open",
            "labels": [{"name": "enhancement"}, {"name": "openspec"}],
            "created_at": "2025-01-01T10:00:00Z",
            "user": {"login": "test-user"},
        }
        mock_gh_get_response.raise_for_status = MagicMock()
        mock_gh_get.return_value = mock_gh_get_response

        # Create project bundle for import
        project_bundle = MagicMock()
        project_bundle.change_tracking = ChangeTracking()
        project_bundle.bundle_dir = tmp_path

        # Import GitHub issue as OpenSpec change proposal
        issue_data = mock_gh_get_response.json.return_value
        github_adapter.import_artifact(
            artifact_key="github_issue",
            artifact_path=issue_data,
            project_bundle=project_bundle,
            bridge_config=BridgeConfig.preset_github(),
        )

        # Verify import
        assert "implement-sso-device-code-auth" in project_bundle.change_tracking.proposals
        proposal = project_bundle.change_tracking.proposals["implement-sso-device-code-auth"]
        assert proposal.title == "Implement SSO Device Code Auth"
        assert proposal.status == "proposed"
        assert proposal.source_tracking.tool == "github"
        # source_id is stored as string in source_metadata
        source_id = proposal.source_tracking.source_metadata.get("source_id")
        assert source_id == "111" or source_id == 111

        # Step 2: Export OpenSpec Change Proposal → ADO Work Item
        ado_adapter = AdoAdapter(
            org="test-org",
            project="test-project",
            api_token="test-ado-token",
        )

        # Mock ADO API responses
        # Mock project API response (for work item type derivation)
        mock_ado_get_response = MagicMock()
        mock_ado_get_response.json.return_value = {
            "processTemplate": {"templateTypeId": "adcc42ab-9882-485e-a3e4-38fb9b8c5e4e"},  # Agile
        }
        mock_ado_get_response.raise_for_status = MagicMock()
        mock_ado_get.return_value = mock_ado_get_response

        # Mock ADO work item creation
        mock_ado_patch_response = MagicMock()
        mock_ado_patch_response.json.return_value = {
            "id": 456,
            "_links": {"html": {"href": "https://dev.azure.com/test-org/test-project/_workitems/edit/456"}},
        }
        mock_ado_patch_response.raise_for_status = MagicMock()
        mock_ado_patch.return_value = mock_ado_patch_response

        # Convert proposal to dict for export
        proposal_dict = {
            "change_id": proposal.name,
            "title": proposal.title,
            "description": proposal.description,
            "rationale": proposal.rationale,
            "status": proposal.status,
            "source_tracking": {
                "tool": proposal.source_tracking.tool,
                "source_metadata": proposal.source_tracking.source_metadata,
            },
        }

        # Export to ADO
        result = ado_adapter.export_artifact(
            artifact_key="change_proposal",
            artifact_data=proposal_dict,
            bridge_config=BridgeConfig.preset_ado(),
        )

        # Verify export
        assert result["work_item_id"] == 456
        assert result["work_item_url"] == "https://dev.azure.com/test-org/test-project/_workitems/edit/456"
        mock_ado_patch.assert_called_once()

        # Verify the API call was made with correct data
        call_args = mock_ado_patch.call_args
        assert call_args is not None
        url = call_args[0][0]
        assert "test-org" in url
        assert "test-project" in url
        assert "workitems" in url

        # Verify JSON patch document contains proposal data
        patch_document = call_args[1]["json"]
        assert isinstance(patch_document, list)
        # Find title and description in patch document
        title_op = next((op for op in patch_document if op.get("path") == "/fields/System.Title"), None)
        desc_op = next((op for op in patch_document if op.get("path") == "/fields/System.Description"), None)
        assert title_op is not None
        assert title_op["value"] == "Implement SSO Device Code Auth"
        assert desc_op is not None
        assert "SSO support" in desc_op["value"] or "device code" in desc_op["value"].lower()

    @beartype
    @patch("specfact_cli.adapters.ado.requests.get")
    @patch("specfact_cli.adapters.ado.requests.patch")
    @patch("specfact_cli.adapters.github.requests.post")
    def test_openspec_to_github_to_ado_round_trip(
        self,
        mock_gh_post: MagicMock,
        mock_ado_patch: MagicMock,
        mock_ado_get: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test round-trip: OpenSpec → GitHub → ADO (with source tracking)."""
        from specfact_cli.adapters.github import GitHubAdapter
        from specfact_cli.models.bridge import BridgeConfig

        # Step 1: Create OpenSpec proposal and export to GitHub
        github_adapter = GitHubAdapter(
            repo_owner="test-org",
            repo_name="test-repo",
            api_token="test-github-token",
        )

        # Mock GitHub issue creation (POST request)
        mock_gh_post_response = MagicMock()
        mock_gh_post_response.json.return_value = {
            "number": 222,
            "html_url": "https://github.com/test-org/test-repo/issues/222",
            "state": "open",
        }
        mock_gh_post_response.raise_for_status = MagicMock()
        mock_gh_post.return_value = mock_gh_post_response

        proposal_data: dict[str, Any] = {
            "change_id": "test-round-trip",
            "title": "Test Round Trip",
            "description": "Test description",
            "rationale": "Test rationale",
            "status": "proposed",
        }

        # Export to GitHub
        github_result = github_adapter.export_artifact(
            artifact_key="change_proposal",
            artifact_data=proposal_data,
            bridge_config=BridgeConfig.preset_github(),
        )

        assert github_result["issue_number"] == 222

        # Step 2: Export same proposal to ADO (with GitHub source tracking)
        ado_adapter = AdoAdapter(
            org="test-org",
            project="test-project",
            api_token="test-ado-token",
        )

        # Mock ADO API responses
        mock_ado_get_response = MagicMock()
        mock_ado_get_response.json.return_value = {
            "processTemplate": {"templateTypeId": "adcc42ab-9882-485e-a3e4-38fb9b8c5e4e"},  # Agile
        }
        mock_ado_get_response.raise_for_status = MagicMock()
        mock_ado_get.return_value = mock_ado_get_response

        mock_ado_patch_response = MagicMock()
        mock_ado_patch_response.json.return_value = {
            "id": 789,
            "_links": {"html": {"href": "https://dev.azure.com/test-org/test-project/_workitems/edit/789"}},
        }
        mock_ado_patch_response.raise_for_status = MagicMock()
        mock_ado_patch.return_value = mock_ado_patch_response

        # Add GitHub source tracking to proposal
        proposal_data["source_tracking"] = [
            {
                "source_id": "222",
                "source_url": "https://github.com/test-org/test-repo/issues/222",
                "source_repo": "test-org/test-repo",
                "source_type": "github",
                "change_id": "test-round-trip",
            }
        ]

        # Export to ADO
        ado_result = ado_adapter.export_artifact(
            artifact_key="change_proposal",
            artifact_data=proposal_data,
            bridge_config=BridgeConfig.preset_ado(),
        )

        assert ado_result["work_item_id"] == 789

        # Verify both adapters were called
        mock_gh_post.assert_called_once()
        mock_ado_patch.assert_called_once()

        # Verify proposal can be tracked in both systems
        assert proposal_data["source_tracking"][0]["source_id"] == "222"  # GitHub
        # ADO source tracking would be added by bridge_sync, not directly by adapter
