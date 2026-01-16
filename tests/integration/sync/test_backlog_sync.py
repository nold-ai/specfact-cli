"""
Integration tests for bidirectional backlog sync (GitHub, extensible for future adapters).

Tests end-to-end sync between OpenSpec change proposals and GitHub Issues,
including bidirectional status synchronization.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from beartype import beartype

from specfact_cli.adapters.github import GitHubAdapter
from specfact_cli.models.bridge import BridgeConfig
from specfact_cli.models.change import ChangeTracking


@pytest.fixture
def github_adapter() -> GitHubAdapter:
    """Create GitHub adapter instance for testing."""
    return GitHubAdapter(
        repo_owner="test-owner",
        repo_name="test-repo",
        api_token="test-token",
    )


@pytest.fixture
def bridge_config() -> BridgeConfig:
    """Create GitHub bridge config for testing."""
    return BridgeConfig.preset_github()


class TestBidirectionalBacklogSync:
    """Integration tests for bidirectional backlog sync."""

    @beartype
    @patch("specfact_cli.adapters.github.requests.post")
    def test_openspec_to_github_export(
        self,
        mock_post: MagicMock,
        github_adapter: GitHubAdapter,
        bridge_config: BridgeConfig,
    ) -> None:
        """Test OpenSpec → GitHub export (change proposal → GitHub issue)."""
        # Mock GitHub API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "number": 123,
            "html_url": "https://github.com/test-owner/test-repo/issues/123",
            "state": "open",
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        proposal_data = {
            "change_id": "add-feature-x",
            "title": "Add Feature X",
            "description": "Implement feature X",
            "rationale": "Needed for user workflow",
            "status": "proposed",
        }

        result = github_adapter.export_artifact(
            artifact_key="change_proposal",
            artifact_data=proposal_data,
            bridge_config=bridge_config,
        )

        assert result["issue_number"] == 123
        assert result["issue_url"] == "https://github.com/test-owner/test-repo/issues/123"
        mock_post.assert_called_once()

    @beartype
    def test_github_to_openspec_import(self, github_adapter: GitHubAdapter, tmp_path: Path) -> None:
        """Test GitHub → OpenSpec import (GitHub issue → change proposal)."""
        from unittest.mock import MagicMock

        # Create mock project bundle
        project_bundle = MagicMock()
        project_bundle.change_tracking = ChangeTracking()
        project_bundle.bundle_dir = tmp_path

        issue_data = {
            "number": 123,
            "title": "Add Feature X",
            "body": "## Why\n\nNeeded for user workflow\n\n## What Changes\n\nImplement feature X",
            "labels": [{"name": "enhancement"}, {"name": "openspec"}],
            "state": "open",
            "created_at": "2025-01-01T10:00:00Z",
            "html_url": "https://github.com/test-owner/test-repo/issues/123",
        }

        github_adapter.import_artifact(
            artifact_key="github_issue",
            artifact_path=issue_data,
            project_bundle=project_bundle,
        )

        assert "123" in project_bundle.change_tracking.proposals
        proposal = project_bundle.change_tracking.proposals["123"]
        assert proposal.title == "Add Feature X"
        assert proposal.status == "proposed"
        assert proposal.source_tracking is not None
        assert proposal.source_tracking.tool == "github"

    @beartype
    @patch("specfact_cli.adapters.github.requests.get")
    @patch("specfact_cli.adapters.github.requests.patch")
    def test_bidirectional_status_sync(
        self,
        mock_patch: MagicMock,
        mock_get: MagicMock,
        github_adapter: GitHubAdapter,
    ) -> None:
        """Test bidirectional status sync (OpenSpec status ↔ GitHub labels)."""
        # Mock get current issue
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "number": 123,
            "html_url": "https://github.com/test-owner/test-repo/issues/123",
            "labels": [{"name": "openspec"}, {"name": "enhancement"}],
        }
        mock_get_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_get_response

        # Mock patch labels
        mock_patch_response = MagicMock()
        mock_patch_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_patch_response

        # Sync OpenSpec status to GitHub
        proposal = {
            "status": "in-progress",
            "source_tracking": {"source_id": "123"},
        }

        result = github_adapter.sync_status_to_github(
            proposal=proposal,
            repo_owner="test-owner",
            repo_name="test-repo",
        )

        assert result["labels_updated"] is True
        assert "in-progress" in result["new_labels"]
        mock_patch.assert_called_once()

        # Sync GitHub status to OpenSpec
        issue_data = {
            "labels": [{"name": "in-progress"}, {"name": "openspec"}],
        }

        proposal_dict = {"status": "proposed"}

        resolved_status = github_adapter.sync_status_from_github(
            issue_data=issue_data,
            proposal=proposal_dict,
            strategy="prefer_backlog",
        )

        assert resolved_status == "in-progress"

    @beartype
    def test_status_conflict_resolution(self, github_adapter: GitHubAdapter) -> None:
        """Test conflict resolution when status differs."""
        issue_data = {
            "labels": [{"name": "in-progress"}],
        }

        proposal = {"status": "proposed"}

        # Test prefer_openspec strategy
        resolved = github_adapter.sync_status_from_github(
            issue_data=issue_data,
            proposal=proposal,
            strategy="prefer_openspec",
        )
        assert resolved == "proposed"

        # Test prefer_backlog strategy
        resolved = github_adapter.sync_status_from_github(
            issue_data=issue_data,
            proposal=proposal,
            strategy="prefer_backlog",
        )
        assert resolved == "in-progress"

        # Test merge strategy (most advanced)
        resolved = github_adapter.sync_status_from_github(
            issue_data=issue_data,
            proposal=proposal,
            strategy="merge",
        )
        assert resolved == "in-progress"  # in-progress is more advanced than proposed

    @beartype
    @patch("specfact_cli.adapters.github.requests.post")
    def test_round_trip_sync(
        self,
        mock_post: MagicMock,
        github_adapter: GitHubAdapter,
        tmp_path: Path,
    ) -> None:
        """Test round-trip sync: export → import maintains data integrity."""
        from unittest.mock import MagicMock

        # Mock GitHub API response for export
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "number": 123,
            "html_url": "https://github.com/test-owner/test-repo/issues/123",
            "state": "open",
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        # Export proposal to GitHub
        original_proposal = {
            "change_id": "add-feature-x",
            "title": "Add Feature X",
            "description": "Implement feature X",
            "rationale": "Needed for user workflow",
            "status": "proposed",
        }

        export_result = github_adapter.export_artifact(
            artifact_key="change_proposal",
            artifact_data=original_proposal,
        )

        # Simulate GitHub issue data (what we'd get from API)
        issue_data = {
            "number": export_result["issue_number"],
            "title": original_proposal["title"],
            "body": f"## Why\n\n{original_proposal['rationale']}\n\n## What Changes\n\n{original_proposal['description']}\n\n---\n*OpenSpec Change Proposal: `{original_proposal['change_id']}`*",
            "labels": [{"name": "enhancement"}, {"name": "openspec"}],
            "state": "open",
            "created_at": "2025-01-01T10:00:00Z",
            "html_url": export_result["issue_url"],
        }

        # Import back from GitHub
        project_bundle = MagicMock()
        project_bundle.change_tracking = ChangeTracking()
        project_bundle.bundle_dir = tmp_path

        github_adapter.import_artifact(
            artifact_key="github_issue",
            artifact_path=issue_data,
            project_bundle=project_bundle,
        )

        # Verify imported proposal matches original
        # Import uses change_id from OpenSpec metadata footer, or issue number as fallback
        imported_key = original_proposal["change_id"]  # Should be "add-feature-x"
        if imported_key not in project_bundle.change_tracking.proposals:
            # Fallback: try issue number if change_id not found
            imported_key = str(export_result["issue_number"])

        assert imported_key in project_bundle.change_tracking.proposals
        imported_proposal = project_bundle.change_tracking.proposals[imported_key]
        assert imported_proposal.title == original_proposal["title"]
        assert imported_proposal.description == original_proposal["description"]
        assert imported_proposal.rationale == original_proposal["rationale"]
        assert imported_proposal.status == original_proposal["status"]
