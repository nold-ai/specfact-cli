"""
Integration tests for complete SDD (Spec-Driven Development) workflow.

Tests end-to-end workflow: OpenSpec change proposal → Spec-Kit spec → SpecFact validation → GitHub issue.
This tests the complete chain of adapters working together.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from unittest.mock import MagicMock, patch

import pytest
from beartype import beartype

from specfact_cli.adapters.github import GitHubAdapter
from specfact_cli.models.bridge import BridgeConfig
from specfact_cli.models.change import ChangeProposal, ChangeTracking, ChangeType, FeatureDelta
from specfact_cli.models.plan import Feature
from specfact_cli.validators.change_proposal_integration import (
    load_active_change_proposals,
    merge_specs_with_change_proposals,
    report_validation_results_to_backlog,
    update_validation_status,
)


@pytest.fixture
def openspec_repo(tmp_path: Path) -> Path:
    """Create test OpenSpec repository structure."""
    openspec_dir = tmp_path / "openspec"
    openspec_dir.mkdir(exist_ok=True)

    # Create project.md
    (openspec_dir / "project.md").write_text(
        dedent(
            """# Test Project

## Purpose

This is a test project for SDD workflow integration.

## Context

- End-to-end workflow testing
- Multi-adapter integration
"""
        )
    )

    # Create change proposal
    changes_dir = openspec_dir / "changes" / "add-feature-x"
    changes_dir.mkdir(parents=True, exist_ok=True)

    proposal_md = dedent(
        """# Add Feature X

## Why

This feature is needed to improve user experience.

## What Changes

- Add new feature X
- Implement API endpoints
- Add frontend components

## Impact

- Affects API layer
- Requires database migration
"""
    )
    (changes_dir / "proposal.md").write_text(proposal_md)

    # Create spec.md with feature delta
    spec_md = dedent(
        """# Feature X Specification

## Overview

Feature X provides new capabilities.

## User Scenarios & Testing

### User Story 1 - Use Feature X (Priority: P1)
As a user, I want to use feature X so that I can accomplish my goal.

**Acceptance Scenarios**:
1. Given feature X is available, When I use it, Then it works correctly
"""
    )
    (changes_dir / "spec.md").write_text(spec_md)

    return tmp_path


@pytest.fixture
def speckit_repo(tmp_path: Path) -> Path:
    """Create test Spec-Kit repository structure."""
    specify_dir = tmp_path / ".specify"
    specify_dir.mkdir(exist_ok=True)

    specs_dir = tmp_path / "specs" / "feature-x"
    specs_dir.mkdir(parents=True, exist_ok=True)

    spec_md = dedent(
        """# Feature X Specification

## User Scenarios & Testing

### User Story 1 - Use Feature X (Priority: P1)
As a user, I want to use feature X so that I can accomplish my goal.

**Acceptance Scenarios**:
1. Given feature X is available, When I use it, Then it works correctly
"""
    )
    (specs_dir / "spec.md").write_text(spec_md)

    return tmp_path


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


class TestCompleteSDDWorkflow:
    """Integration tests for complete SDD workflow."""

    @beartype
    @patch("specfact_cli.validators.change_proposal_integration.AdapterRegistry")
    @patch("specfact_cli.adapters.github.requests.post")
    def test_complete_workflow_openspec_to_github(
        self,
        mock_post: MagicMock,
        mock_registry: MagicMock,
        openspec_repo: Path,
        github_adapter: GitHubAdapter,
        bridge_config: BridgeConfig,
    ) -> None:
        """Test complete workflow: OpenSpec change proposal → Spec-Kit spec → SpecFact validation → GitHub issue."""
        # Step 1: Load change proposal from OpenSpec

        feature_delta = FeatureDelta(
            feature_key="feature-x",
            change_type=ChangeType.ADDED,
            original_feature=None,
            proposed_feature=Feature(key="feature-x", title="Feature X", outcomes=["Outcome 1"]),
            change_rationale=None,
            change_date=None,
            validation_status=None,
            validation_results=None,
            source_tracking=None,
        )

        change_tracking = ChangeTracking(
            proposals={
                "add-feature-x": ChangeProposal(
                    name="add-feature-x",
                    title="Add Feature X",
                    description="Implement feature X",
                    rationale="Needed for user workflow",
                    status="proposed",
                    created_at="2025-01-01T10:00:00Z",
                    timeline=None,
                    owner=None,
                    applied_at=None,
                    archived_at=None,
                    source_tracking=None,
                )
            },
            feature_deltas={"add-feature-x": [feature_delta]},
        )

        mock_adapter = MagicMock()
        mock_adapter.detect.return_value = True
        mock_adapter.load_change_tracking.return_value = change_tracking
        mock_registry.get_adapter.return_value = mock_adapter

        active_tracking = load_active_change_proposals(openspec_repo)
        assert active_tracking is not None
        assert "add-feature-x" in active_tracking.proposals

        # Step 2: Merge specs (current Spec-Kit + proposed OpenSpec changes)
        current_specs = {
            "feature-1": {"key": "feature-1", "title": "Feature 1", "outcomes": ["Outcome 1"]},
        }

        merged_specs = merge_specs_with_change_proposals(current_specs, active_tracking)
        assert "feature-x" in merged_specs  # ADDED feature included
        assert "feature-1" in merged_specs  # Existing feature preserved

        # Step 3: Simulate validation (would normally run actual validation)
        validation_results = {
            "feature-x": {"success": True, "contracts_validated": 3, "deviations": []},
        }

        # Step 4: Update validation status
        update_validation_status(active_tracking, validation_results, openspec_repo)
        assert feature_delta.validation_status == "passed"
        assert feature_delta.validation_results == validation_results["feature-x"]

        # Step 5: Export to GitHub Issues
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

        export_result = github_adapter.export_artifact(
            artifact_key="change_proposal",
            artifact_data=proposal_data,
            bridge_config=bridge_config,
        )

        assert export_result["issue_number"] == 123
        assert export_result["issue_url"] == "https://github.com/test-owner/test-repo/issues/123"
        mock_post.assert_called_once()

    @beartype
    @patch("specfact_cli.validators.change_proposal_integration.AdapterRegistry")
    @patch("specfact_cli.validators.change_proposal_integration.requests")
    def test_workflow_with_validation_reporting(
        self,
        mock_requests: MagicMock,
        mock_registry: MagicMock,
        openspec_repo: Path,
        github_adapter: GitHubAdapter,
    ) -> None:
        """Test workflow with validation result reporting to GitHub."""
        from specfact_cli.models.source_tracking import SourceTracking

        # Setup change proposal with GitHub source tracking
        feature_delta = FeatureDelta(
            feature_key="feature-x",
            change_type=ChangeType.ADDED,
            original_feature=None,
            proposed_feature=Feature(key="feature-x", title="Feature X", outcomes=[]),
            change_rationale=None,
            change_date=None,
            validation_status=None,
            validation_results=None,
            source_tracking=None,
        )

        proposal = ChangeProposal(
            name="add-feature-x",
            title="Add Feature X",
            description="Test",
            rationale="Test",
            created_at="2025-01-01T10:00:00Z",
            timeline=None,
            owner=None,
            applied_at=None,
            archived_at=None,
            source_tracking=SourceTracking(
                tool="github",
                source_metadata={
                    "source_id": "123",
                    "source_url": "https://github.com/test-owner/test-repo/issues/123",
                },
            ),
        )

        change_tracking = ChangeTracking(
            proposals={"add-feature-x": proposal},
            feature_deltas={"add-feature-x": [feature_delta]},
        )

        validation_results = {
            "feature-x": {"success": False, "error": "Contract violation detected"},
        }

        # Mock adapter registry
        mock_adapter = MagicMock()
        mock_adapter.base_url = "https://api.github.com"
        mock_adapter.api_token = "test-token"
        mock_adapter._add_issue_comment = MagicMock()
        mock_registry.get_adapter.return_value = mock_adapter

        # Mock GitHub API responses
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "number": 123,
            "labels": [{"name": "openspec"}],
        }
        mock_get_response.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_get_response

        mock_patch_response = MagicMock()
        mock_patch_response.raise_for_status = MagicMock()
        mock_requests.patch.return_value = mock_patch_response

        # Report validation results
        report_validation_results_to_backlog(change_tracking, validation_results)

        # Verify comment was added
        mock_adapter._add_issue_comment.assert_called_once()
        call_args = mock_adapter._add_issue_comment.call_args
        assert "Validation Results" in call_args[0][3]  # comment_text is 4th arg
        assert "FAILED" in call_args[0][3]

    @beartype
    @patch("specfact_cli.validators.change_proposal_integration.AdapterRegistry")
    def test_workflow_error_handling_missing_proposal(
        self,
        mock_registry: MagicMock,
        openspec_repo: Path,
    ) -> None:
        """Test error handling when change proposal is missing."""
        # Setup adapter that returns None (no proposals found)
        mock_adapter_class = MagicMock()
        mock_adapter = MagicMock()
        mock_adapter.detect.return_value = True
        mock_adapter.load_change_tracking.return_value = None
        mock_adapter_class.return_value = mock_adapter
        mock_registry.get.return_value = mock_adapter_class

        # Should handle gracefully
        active_tracking = load_active_change_proposals(openspec_repo)
        assert active_tracking is None  # No proposals found

        # Should not crash when merging with empty ChangeTracking
        current_specs = {"feature-1": {"key": "feature-1", "title": "Feature 1"}}
        empty_tracking = ChangeTracking(proposals={}, feature_deltas={})
        merged = merge_specs_with_change_proposals(current_specs, empty_tracking)
        assert merged == current_specs  # Returns current specs unchanged

    @beartype
    @patch("specfact_cli.validators.change_proposal_integration.AdapterRegistry")
    def test_workflow_error_handling_validation_failure(
        self,
        mock_registry: MagicMock,
        openspec_repo: Path,
    ) -> None:
        """Test error handling when validation fails."""
        openspec_path = openspec_repo / "openspec"
        openspec_path.mkdir(exist_ok=True)

        feature_delta = FeatureDelta(
            feature_key="feature-x",
            change_type=ChangeType.ADDED,
            original_feature=None,
            proposed_feature=Feature(key="feature-x", title="Feature X", outcomes=[]),
            change_rationale=None,
            change_date=None,
            validation_status=None,
            validation_results=None,
            source_tracking=None,
        )

        change_tracking = ChangeTracking(
            proposals={
                "add-feature-x": ChangeProposal(
                    name="add-feature-x",
                    title="Add Feature X",
                    description="Test",
                    rationale="Test",
                    created_at="2025-01-01T10:00:00Z",
                    timeline=None,
                    owner=None,
                    applied_at=None,
                    archived_at=None,
                    source_tracking=None,
                )
            },
            feature_deltas={"add-feature-x": [feature_delta]},
        )

        validation_results = {
            "feature-x": {"success": False, "error": "Contract violation: missing required field"},
        }

        mock_adapter = MagicMock()
        mock_registry.get_adapter.return_value = mock_adapter

        # Update validation status (should mark as failed)
        update_validation_status(change_tracking, validation_results, openspec_repo)

        assert feature_delta.validation_status == "failed"
        assert feature_delta.validation_results == validation_results["feature-x"]
        assert feature_delta.validation_results is not None
        assert "error" in feature_delta.validation_results

    @beartype
    @patch("specfact_cli.adapters.github.requests.post")
    def test_workflow_error_handling_github_export_failure(
        self,
        mock_post: MagicMock,
        github_adapter: GitHubAdapter,
        bridge_config: BridgeConfig,
    ) -> None:
        """Test error handling when GitHub export fails."""
        # Mock GitHub API failure
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("GitHub API error")
        mock_post.return_value = mock_response

        proposal_data = {
            "change_id": "add-feature-x",
            "title": "Add Feature X",
            "description": "Implement feature X",
            "rationale": "Needed for user workflow",
            "status": "proposed",
        }

        # Should raise exception
        with pytest.raises(Exception, match="GitHub API error"):
            github_adapter.export_artifact(
                artifact_key="change_proposal",
                artifact_data=proposal_data,
                bridge_config=bridge_config,
            )
