"""
Unit tests for GitHub bridge adapter.

Tests GitHub adapter functionality with mocked API responses.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests
from beartype import beartype

from specfact_cli.adapters.github import GitHubAdapter
from specfact_cli.models.bridge import AdapterType, BridgeConfig


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
    """Create bridge config for testing."""
    return BridgeConfig.preset_github()


class TestGitHubAdapter:
    """Test GitHub adapter implementation."""

    @beartype
    def test_detect_github_repo(self, github_adapter: GitHubAdapter, tmp_path: Path) -> None:
        """Test GitHub repository detection."""
        # Create .git/config with GitHub remote
        git_config = tmp_path / ".git" / "config"
        git_config.parent.mkdir(parents=True)
        git_config.write_text('[remote "origin"]\nurl = https://github.com/test-owner/test-repo.git\n')

        assert github_adapter.detect(tmp_path) is True

    @beartype
    def test_detect_non_github_repo(self, github_adapter: GitHubAdapter, tmp_path: Path) -> None:
        """Test detection returns False for non-GitHub repository."""
        # Create .git/config with non-GitHub remote
        git_config = tmp_path / ".git" / "config"
        git_config.parent.mkdir(parents=True)
        git_config.write_text('[remote "origin"]\nurl = https://gitlab.com/test-owner/test-repo.git\n')

        assert github_adapter.detect(tmp_path) is False

    @beartype
    def test_detect_with_bridge_config(
        self, github_adapter: GitHubAdapter, tmp_path: Path, bridge_config: BridgeConfig
    ) -> None:
        """Test detection with bridge config."""
        bridge_config.adapter = AdapterType.GITHUB
        assert github_adapter.detect(tmp_path, bridge_config=bridge_config) is True

    @beartype
    @patch("specfact_cli.adapters.github.requests.post")
    def test_create_issue_from_proposal(
        self,
        mock_post: MagicMock,
        github_adapter: GitHubAdapter,
        bridge_config: BridgeConfig,
    ) -> None:
        """Test creating GitHub issue from change proposal."""
        # Mock API response
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
        assert result["state"] == "open"
        mock_post.assert_called_once()

    @beartype
    @patch("specfact_cli.adapters.github.requests.patch")
    @patch("specfact_cli.adapters.github.requests.post")
    def test_update_issue_status(
        self,
        mock_post: MagicMock,  # For comment
        mock_patch: MagicMock,  # For issue update
        github_adapter: GitHubAdapter,
        bridge_config: BridgeConfig,
    ) -> None:
        """Test updating GitHub issue status."""
        # Mock issue update response
        mock_patch_response = MagicMock()
        mock_patch_response.json.return_value = {
            "number": 123,
            "html_url": "https://github.com/test-owner/test-repo/issues/123",
            "state": "closed",
        }
        mock_patch_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_patch_response

        # Mock comment response
        mock_post_response = MagicMock()
        mock_post_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_post_response

        proposal_data = {
            "change_id": "add-feature-x",
            "title": "Add Feature X",
            "status": "applied",
            "source_tracking": {
                "source_id": "123",
                "source_url": "https://github.com/test-owner/test-repo/issues/123",
                "source_type": "github",
            },
        }

        result = github_adapter.export_artifact(
            artifact_key="change_status",
            artifact_data=proposal_data,
            bridge_config=bridge_config,
        )

        assert result["issue_number"] == 123
        assert result["state"] == "closed"
        mock_patch.assert_called_once()
        mock_post.assert_called_once()  # Comment added

    @beartype
    def test_missing_api_token(self, github_adapter: GitHubAdapter, bridge_config: BridgeConfig) -> None:
        """Test error when API token is missing."""
        from unittest.mock import patch

        with patch("specfact_cli.adapters.github._get_github_token_from_gh_cli", return_value=None):
            adapter = GitHubAdapter(repo_owner="test-owner", repo_name="test-repo", api_token=None, use_gh_cli=False)
            os.environ.pop("GITHUB_TOKEN", None)  # Ensure env var is not set

            proposal_data = {"change_id": "test", "title": "Test"}

            with pytest.raises(ValueError, match="GitHub API token required"):
                adapter.export_artifact(
                    artifact_key="change_proposal",
                    artifact_data=proposal_data,
                    bridge_config=bridge_config,
                )

    @beartype
    def test_use_gh_cli_token(self, bridge_config: BridgeConfig) -> None:
        """Test using GitHub CLI token when available."""
        from unittest.mock import patch

        with patch("specfact_cli.adapters.github._get_github_token_from_gh_cli", return_value="gh_cli_token_12345"):
            adapter = GitHubAdapter(repo_owner="test-owner", repo_name="test-repo", api_token=None, use_gh_cli=True)
            os.environ.pop("GITHUB_TOKEN", None)  # Ensure env var is not set

            assert adapter.api_token == "gh_cli_token_12345"

    @beartype
    def test_explicit_token_overrides_gh_cli(self, bridge_config: BridgeConfig) -> None:
        """Test that explicit token takes precedence over gh CLI."""
        from unittest.mock import patch

        with patch("specfact_cli.adapters.github._get_github_token_from_gh_cli", return_value="gh_cli_token_12345"):
            adapter = GitHubAdapter(
                repo_owner="test-owner", repo_name="test-repo", api_token="explicit_token", use_gh_cli=True
            )

            assert adapter.api_token == "explicit_token"

    @beartype
    def test_missing_repo_config(self, github_adapter: GitHubAdapter, bridge_config: BridgeConfig) -> None:
        """Test error when repository config is missing."""
        adapter = GitHubAdapter(repo_owner=None, repo_name=None, api_token="test-token")

        proposal_data = {"change_id": "test", "title": "Test"}

        with pytest.raises(ValueError, match="GitHub repository owner and name required"):
            adapter.export_artifact(
                artifact_key="change_proposal",
                artifact_data=proposal_data,
                bridge_config=bridge_config,
            )

    @beartype
    @patch("specfact_cli.adapters.github.requests.post")
    def test_api_error_handling(
        self,
        mock_post: MagicMock,
        github_adapter: GitHubAdapter,
        bridge_config: BridgeConfig,
    ) -> None:
        """Test error handling for API failures."""
        # Mock API error
        mock_post.side_effect = requests.RequestException("API rate limit exceeded")

        proposal_data = {
            "change_id": "test",
            "title": "Test",
            "description": "Test description",
            "status": "proposed",
        }

        with pytest.raises(requests.RequestException):
            github_adapter.export_artifact(
                artifact_key="change_proposal",
                artifact_data=proposal_data,
                bridge_config=bridge_config,
            )

    @beartype
    def test_generate_bridge_config(self, github_adapter: GitHubAdapter, tmp_path: Path) -> None:
        """Test bridge config generation."""
        config = github_adapter.generate_bridge_config(tmp_path)
        assert config.adapter == AdapterType.GITHUB
        assert "change_proposal" in config.artifacts
        assert "change_status" in config.artifacts

    @beartype
    def test_get_labels_for_status(self, github_adapter: GitHubAdapter) -> None:
        """Test label generation for different statuses."""
        assert "openspec" in github_adapter._get_labels_for_status("proposed")
        assert "in-progress" in github_adapter._get_labels_for_status("in-progress")
        assert "completed" in github_adapter._get_labels_for_status("applied")
        assert "deprecated" in github_adapter._get_labels_for_status("deprecated")
        assert "wontfix" in github_adapter._get_labels_for_status("discarded")

    @beartype
    def test_get_status_comment(self, github_adapter: GitHubAdapter) -> None:
        """Test comment generation for status changes."""
        comment = github_adapter._get_status_comment("applied", "Test Feature")
        assert "Change applied" in comment
        assert "Test Feature" in comment

        comment = github_adapter._get_status_comment("deprecated", "Test Feature")
        assert "Change deprecated" in comment

        comment = github_adapter._get_status_comment("discarded", "Test Feature")
        assert "Change discarded" in comment

        comment = github_adapter._get_status_comment("proposed", "Test Feature")
        assert comment == ""

    @beartype
    @patch("specfact_cli.adapters.github.requests.patch")
    @patch("specfact_cli.adapters.github.requests.post")
    def test_update_issue_body(
        self,
        mock_post: MagicMock,  # For optional comment
        mock_patch: MagicMock,  # For issue body update
        github_adapter: GitHubAdapter,
        bridge_config: BridgeConfig,
    ) -> None:
        """Test updating GitHub issue body from change proposal."""
        # Mock issue update response
        mock_patch_response = MagicMock()
        mock_patch_response.json.return_value = {
            "number": 123,
            "html_url": "https://github.com/test-owner/test-repo/issues/123",
            "state": "open",
        }
        mock_patch_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_patch_response

        # Mock comment response (not called for non-significant changes)
        mock_post_response = MagicMock()
        mock_post_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_post_response

        proposal_data = {
            "change_id": "add-feature-x",
            "title": "Add Feature X",
            "description": "Implement feature X with new capabilities",
            "rationale": "Needed for user workflow improvements",
            "status": "proposed",
        }

        result = github_adapter._update_issue_body(
            proposal_data=proposal_data,
            repo_owner="test-owner",
            repo_name="test-repo",
            issue_number=123,
        )

        assert result["issue_number"] == 123
        assert result["issue_url"] == "https://github.com/test-owner/test-repo/issues/123"
        assert result["state"] == "open"
        mock_patch.assert_called_once()
        # Verify body format includes Why and What Changes sections
        call_args = mock_patch.call_args
        assert call_args is not None
        payload = call_args[1]["json"]
        assert "## Why" in payload["body"]
        assert "## What Changes" in payload["body"]
        assert "add-feature-x" in payload["body"]
        # No comment for non-significant changes
        mock_post.assert_not_called()

    @beartype
    @patch("specfact_cli.adapters.github.requests.patch")
    @patch("specfact_cli.adapters.github.requests.post")
    def test_update_issue_body_with_significant_change(
        self,
        mock_post: MagicMock,  # For significant change comment
        mock_patch: MagicMock,  # For issue body update
        github_adapter: GitHubAdapter,
        bridge_config: BridgeConfig,
    ) -> None:
        """Test updating issue body with significant change (triggers comment)."""
        # Mock issue update response
        mock_patch_response = MagicMock()
        mock_patch_response.json.return_value = {
            "number": 123,
            "html_url": "https://github.com/test-owner/test-repo/issues/123",
            "state": "open",
        }
        mock_patch_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_patch_response

        # Mock comment response
        mock_post_response = MagicMock()
        mock_post_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_post_response

        proposal_data = {
            "change_id": "BREAKING-change",
            "title": "BREAKING: Major API Changes",
            "description": "This is a major scope change affecting all users",
            "rationale": "Breaking changes required for security",
            "status": "proposed",
        }

        result = github_adapter._update_issue_body(
            proposal_data=proposal_data,
            repo_owner="test-owner",
            repo_name="test-repo",
            issue_number=123,
        )

        assert result["issue_number"] == 123
        mock_patch.assert_called_once()
        # Verify comment was added for significant change
        mock_post.assert_called_once()

    @beartype
    @patch("specfact_cli.adapters.github.requests.patch")
    def test_update_issue_body_api_error(
        self,
        mock_patch: MagicMock,
        github_adapter: GitHubAdapter,
        bridge_config: BridgeConfig,
    ) -> None:
        """Test error handling when updating issue body fails."""
        # Mock API error
        mock_patch.side_effect = requests.RequestException("API rate limit exceeded")

        proposal_data = {
            "change_id": "test",
            "title": "Test",
            "description": "Test description",
            "rationale": "Test rationale",
            "status": "proposed",
        }

        with pytest.raises(requests.RequestException):
            github_adapter._update_issue_body(
                proposal_data=proposal_data,
                repo_owner="test-owner",
                repo_name="test-repo",
                issue_number=123,
            )

    @beartype
    @patch("specfact_cli.adapters.github.requests.patch")
    def test_update_issue_body_missing_issue(
        self,
        mock_patch: MagicMock,
        github_adapter: GitHubAdapter,
        bridge_config: BridgeConfig,
    ) -> None:
        """Test error handling when issue doesn't exist."""
        # Mock 404 response
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_patch.return_value = mock_response

        proposal_data = {
            "change_id": "test",
            "title": "Test",
            "description": "Test description",
            "status": "proposed",
        }

        with pytest.raises(requests.HTTPError):
            github_adapter._update_issue_body(
                proposal_data=proposal_data,
                repo_owner="test-owner",
                repo_name="test-repo",
                issue_number=999,  # Non-existent issue
            )
