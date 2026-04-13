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

from specfact_cli.adapters.github import GitHubAdapter, _git_config_content_indicates_github
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
    def test_git_config_pushurl_only_does_not_indicate_github(self) -> None:
        """Only ``url =`` lines count; ``pushurl`` must not imply GitHub."""
        content = '[remote "origin"]\npushurl = git@github.com:owner/repo.git\n'
        assert _git_config_content_indicates_github(content) is False

    @beartype
    def test_detect_pushurl_only_remote_is_not_github(self, github_adapter: GitHubAdapter, tmp_path: Path) -> None:
        """``detect`` must not treat GitHub ``pushurl`` alone as a GitHub remote."""
        git_config = tmp_path / ".git" / "config"
        git_config.parent.mkdir(parents=True)
        git_config.write_text('[remote "origin"]\npushurl = git@github.com:owner/repo.git\n')
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

    @beartype
    @patch("specfact_cli.adapters.github.requests.post")
    def test_add_progress_comment(
        self,
        mock_post: MagicMock,
        github_adapter: GitHubAdapter,
        bridge_config: BridgeConfig,
    ) -> None:
        """Test adding progress comment to GitHub issue."""
        proposal_data = {
            "change_id": "test-change",
            "title": "Test Change",
            "source_tracking": {"source_id": "123", "source_repo": "test-owner/test-repo"},
            "progress_data": {
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
            },
        }

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 1,
            "html_url": "https://github.com/test-owner/test-repo/issues/123#issuecomment-1",
        }
        mock_post.return_value = mock_response

        result = github_adapter.export_artifact(
            artifact_key="code_change_progress",
            artifact_data=proposal_data,
            bridge_config=bridge_config,
        )

        assert result["comment_added"] is True
        assert result["issue_number"] == 123
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "comments" in call_args[0][0]
        assert call_args[1]["json"]["body"] is not None

    @beartype
    def test_add_progress_comment_no_progress_data(
        self, github_adapter: GitHubAdapter, bridge_config: BridgeConfig
    ) -> None:
        """Test adding progress comment when no progress data provided."""
        proposal_data = {
            "change_id": "test-change",
            "title": "Test Change",
            "source_tracking": {"source_id": "123", "source_repo": "test-owner/test-repo"},
        }

        result = github_adapter.export_artifact(
            artifact_key="code_change_progress",
            artifact_data=proposal_data,
            bridge_config=bridge_config,
        )

        assert result["comment_added"] is False
        assert result["issue_number"] == 123

    @beartype
    def test_add_progress_comment_missing_issue_number(
        self, github_adapter: GitHubAdapter, bridge_config: BridgeConfig
    ) -> None:
        """Test adding progress comment when issue number is missing."""
        proposal_data = {
            "change_id": "test-change",
            "title": "Test Change",
            "source_tracking": {},
            "progress_data": {"summary": "Test progress"},
        }

        with pytest.raises(ValueError, match="Issue number required for progress comment"):
            github_adapter.export_artifact(
                artifact_key="code_change_progress",
                artifact_data=proposal_data,
                bridge_config=bridge_config,
            )

    @beartype
    def test_missing_api_token(self, github_adapter: GitHubAdapter, bridge_config: BridgeConfig) -> None:
        """Test error when API token is missing."""
        from unittest.mock import patch

        with (
            patch("specfact_cli.adapters.github._get_github_token_from_gh_cli", return_value=None),
            patch("specfact_cli.adapters.github.get_token", return_value=None),
        ):
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

        with (
            patch("specfact_cli.adapters.github._get_github_token_from_gh_cli", return_value="gh_cli_token_12345"),
            patch("specfact_cli.adapters.github.get_token", return_value=None),
        ):
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

    @beartype
    def test_map_backlog_status_to_openspec(self, github_adapter: GitHubAdapter) -> None:
        """Test mapping GitHub labels to OpenSpec status."""
        assert github_adapter.map_backlog_status_to_openspec("enhancement") == "proposed"
        assert github_adapter.map_backlog_status_to_openspec("new") == "proposed"
        assert github_adapter.map_backlog_status_to_openspec("in-progress") == "in-progress"
        assert github_adapter.map_backlog_status_to_openspec("in progress") == "in-progress"
        assert github_adapter.map_backlog_status_to_openspec("active") == "in-progress"
        assert github_adapter.map_backlog_status_to_openspec("done") == "applied"
        assert github_adapter.map_backlog_status_to_openspec("completed") == "applied"
        assert github_adapter.map_backlog_status_to_openspec("closed") == "applied"
        assert github_adapter.map_backlog_status_to_openspec("deprecated") == "deprecated"
        assert github_adapter.map_backlog_status_to_openspec("wontfix") == "deprecated"
        assert github_adapter.map_backlog_status_to_openspec("discarded") == "discarded"
        assert github_adapter.map_backlog_status_to_openspec("unknown") == "proposed"  # Default

    @beartype
    def test_map_openspec_status_to_backlog(self, github_adapter: GitHubAdapter) -> None:
        """Test mapping OpenSpec status to GitHub labels."""
        labels = github_adapter.map_openspec_status_to_backlog("proposed")
        assert "openspec" in labels
        assert len(labels) == 1

        labels = github_adapter.map_openspec_status_to_backlog("in-progress")
        assert "openspec" in labels
        assert "in-progress" in labels

        labels = github_adapter.map_openspec_status_to_backlog("applied")
        assert "openspec" in labels
        assert "completed" in labels

        labels = github_adapter.map_openspec_status_to_backlog("deprecated")
        assert "openspec" in labels
        assert "deprecated" in labels

        labels = github_adapter.map_openspec_status_to_backlog("discarded")
        assert "openspec" in labels
        assert "wontfix" in labels

    @beartype
    def test_extract_change_proposal_data(self, github_adapter: GitHubAdapter) -> None:
        """Test extracting change proposal data from GitHub issue."""
        issue_data = {
            "number": 123,
            "title": "Add Feature X",
            "body": "## Why\n\nNeeded for user workflow\n\n## What Changes\n\nImplement feature X",
            "labels": [{"name": "enhancement"}, {"name": "openspec"}],
            "state": "open",
            "created_at": "2025-01-01T10:00:00Z",
            "assignees": [{"login": "user1"}],
            "html_url": "https://github.com/test-owner/test-repo/issues/123",
        }

        result = github_adapter.extract_change_proposal_data(issue_data)

        assert result["change_id"] == "123"
        assert result["title"] == "Add Feature X"
        assert result["rationale"] == "Needed for user workflow"
        assert result["description"] == "Implement feature X"
        assert result["status"] == "proposed"
        assert result["owner"] == "user1"
        assert "user1" in result["stakeholders"]

    @beartype
    def test_extract_change_proposal_data_with_openspec_metadata(self, github_adapter: GitHubAdapter) -> None:
        """Test extracting change proposal data with OpenSpec metadata footer."""
        issue_data = {
            "number": 456,
            "title": "Update Feature Y",
            "body": "## Why\n\nImprove performance\n\n## What Changes\n\nOptimize code\n\n---\n*OpenSpec Change Proposal: `update-feature-y`*",
            "labels": [{"name": "in-progress"}],
            "state": "open",
            "created_at": "2025-01-02T10:00:00Z",
        }

        result = github_adapter.extract_change_proposal_data(issue_data)

        assert result["change_id"] == "update-feature-y"
        assert result["status"] == "in-progress"

    @beartype
    def test_extract_change_proposal_data_missing_title(self, github_adapter: GitHubAdapter) -> None:
        """Test error when GitHub issue has no title."""
        issue_data = {
            "number": 123,
            "title": "",
            "body": "Test body",
            "labels": [],
            "state": "open",
        }

        with pytest.raises(ValueError, match="GitHub issue must have a title"):
            github_adapter.extract_change_proposal_data(issue_data)

    @beartype
    def test_extract_change_proposal_data_malformed_body(self, github_adapter: GitHubAdapter) -> None:
        """Test extracting data from issue with malformed body."""
        issue_data = {
            "number": 123,
            "title": "Test Issue",
            "body": "No sections here, just plain text",
            "labels": [{"name": "enhancement"}],
            "state": "open",
            "created_at": "2025-01-01T10:00:00Z",
        }

        result = github_adapter.extract_change_proposal_data(issue_data)

        assert result["title"] == "Test Issue"
        assert result["description"] == "No sections here, just plain text"
        assert result["rationale"] == ""

    @beartype
    def test_import_artifact_github_issue(self, github_adapter: GitHubAdapter, tmp_path: Path) -> None:
        """Test importing GitHub issue as change proposal."""
        from unittest.mock import MagicMock

        from specfact_cli.models.change import ChangeTracking

        # Create mock project bundle
        project_bundle = MagicMock()
        project_bundle.change_tracking = ChangeTracking()
        project_bundle.bundle_dir = tmp_path

        issue_data = {
            "number": 123,
            "title": "Add Feature X",
            "body": "## Why\n\nNeeded\n\n## What Changes\n\nImplement",
            "labels": [{"name": "enhancement"}],
            "state": "open",
            "created_at": "2025-01-01T10:00:00Z",
            "html_url": "https://github.com/test-owner/test-repo/issues/123",
        }

        github_adapter.import_artifact(
            artifact_key="github_issue",
            artifact_path=issue_data,
            project_bundle=project_bundle,
        )

        assert "add-feature-x" in project_bundle.change_tracking.proposals
        proposal = project_bundle.change_tracking.proposals["add-feature-x"]
        assert proposal.title == "Add Feature X"
        assert proposal.status == "proposed"
        assert proposal.source_tracking is not None
        assert proposal.source_tracking.tool == "github"

    @beartype
    def test_import_artifact_unsupported_key(self, github_adapter: GitHubAdapter) -> None:
        """Test error when importing unsupported artifact key."""
        with pytest.raises(NotImplementedError, match="Unsupported artifact key"):
            github_adapter.import_artifact(
                artifact_key="unsupported",
                artifact_path={},
                project_bundle=MagicMock(),
            )

    @beartype
    def test_import_artifact_invalid_path_type(self, github_adapter: GitHubAdapter) -> None:
        """Test error when artifact_path is not dict for GitHub issue."""
        with pytest.raises(ValueError, match="GitHub issue import requires dict"):
            github_adapter.import_artifact(
                artifact_key="github_issue",
                artifact_path=Path("/tmp/test"),
                project_bundle=MagicMock(),
            )

    @beartype
    @patch("specfact_cli.adapters.github.requests.get")
    @patch("specfact_cli.adapters.github.requests.patch")
    def test_sync_status_to_github(
        self,
        mock_patch: MagicMock,
        mock_get: MagicMock,
        github_adapter: GitHubAdapter,
    ) -> None:
        """Test syncing OpenSpec status to GitHub issue labels."""
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

        proposal = {
            "status": "in-progress",
            "source_tracking": {"source_id": "123"},
        }

        result = github_adapter.sync_status_to_github(
            proposal=proposal,
            repo_owner="test-owner",
            repo_name="test-repo",
        )

        assert result["issue_number"] == 123  # API returns int
        assert result["labels_updated"] is True
        assert "in-progress" in result["new_labels"]
        mock_patch.assert_called_once()

    @beartype
    def test_sync_status_to_github_missing_source_tracking(self, github_adapter: GitHubAdapter) -> None:
        """Test error when source_tracking is missing."""
        proposal = {"status": "in-progress"}

        with pytest.raises(ValueError, match="Source tracking required"):
            github_adapter.sync_status_to_github(
                proposal=proposal,
                repo_owner="test-owner",
                repo_name="test-repo",
            )

    @beartype
    def test_sync_status_from_github(self, github_adapter: GitHubAdapter) -> None:
        """Test syncing GitHub issue status to OpenSpec."""
        issue_data = {
            "labels": [{"name": "in-progress"}, {"name": "openspec"}],
        }

        proposal = {"status": "proposed"}

        resolved_status = github_adapter.sync_status_from_github(
            issue_data=issue_data,
            proposal=proposal,
            strategy="prefer_openspec",
        )

        # With prefer_openspec strategy, should keep OpenSpec status
        assert resolved_status == "proposed"

    @beartype
    def test_sync_status_from_github_prefer_backlog(self, github_adapter: GitHubAdapter) -> None:
        """Test syncing with prefer_backlog strategy."""
        issue_data = {
            "labels": [{"name": "in-progress"}],
        }

        proposal = {"status": "proposed"}

        resolved_status = github_adapter.sync_status_from_github(
            issue_data=issue_data,
            proposal=proposal,
            strategy="prefer_backlog",
        )

        # With prefer_backlog strategy, should use GitHub status
        assert resolved_status == "in-progress"

    @beartype
    def test_resolve_status_conflict(self, github_adapter: GitHubAdapter) -> None:
        """Test conflict resolution strategies."""
        # Test prefer_openspec (default)
        result = github_adapter.resolve_status_conflict("in-progress", "proposed", "prefer_openspec")
        assert result == "in-progress"

        # Test prefer_backlog
        result = github_adapter.resolve_status_conflict("proposed", "in-progress", "prefer_backlog")
        assert result == "in-progress"

        # Test merge (most advanced)
        result = github_adapter.resolve_status_conflict("proposed", "in-progress", "merge")
        assert result == "in-progress"  # in-progress is more advanced

        result = github_adapter.resolve_status_conflict("in-progress", "applied", "merge")
        assert result == "applied"  # applied is more advanced

    @beartype
    def test_create_source_tracking(self, github_adapter: GitHubAdapter) -> None:
        """Test creating source tracking from backlog item."""
        item_data = {
            "id": "123",
            "number": 123,
            "url": "https://api.github.com/repos/test-owner/test-repo/issues/123",
            "html_url": "https://github.com/test-owner/test-repo/issues/123",
            "state": "open",
            "assignees": [{"login": "user1"}],
        }

        source_tracking = github_adapter.create_source_tracking(item_data, "github")

        assert source_tracking.tool == "github"
        assert source_tracking.source_metadata["source_id"] == "123"
        # Prefer html_url over url (user-friendly URL)
        assert source_tracking.source_metadata["source_url"] == "https://github.com/test-owner/test-repo/issues/123"
        assert source_tracking.source_metadata["source_state"] == "open"
        assert len(source_tracking.source_metadata["assignees"]) == 1

    @beartype
    @patch("specfact_cli.adapters.github.requests.get")
    def test_fetch_backlog_item_preserves_native_issue_payload(  # pylint: disable=redefined-outer-name
        self,
        mock_get: MagicMock,
        github_adapter: GitHubAdapter,
    ) -> None:
        """Similar selective fetch path should keep the native GitHub issue payload."""
        issue_data = {
            "number": 123,
            "title": "Add Feature X",
            "body": "## Why\n\nNeeded\n\n## What Changes\n\nImplement",
            "state": "open",
            "html_url": "https://github.com/test-owner/test-repo/issues/123",
        }
        mock_response = MagicMock()
        mock_response.json.return_value = issue_data
        mock_response.raise_for_status = MagicMock()
        mock_response.ok = True
        mock_get.return_value = mock_response

        result = github_adapter.fetch_backlog_item("123")

        assert result == issue_data
        assert result["title"] == "Add Feature X"
        assert result["body"].startswith("## Why")
