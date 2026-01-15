"""
Integration tests for change proposal validation integration.

Tests validation with active change proposals, spec merging, and validation
result reporting to backlog.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from beartype import beartype

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
    return tmp_path


class TestChangeProposalValidationIntegration:
    """Integration tests for change proposal validation."""

    @beartype
    @patch("specfact_cli.validators.change_proposal_integration.AdapterRegistry")
    def test_validation_with_active_proposals(self, mock_registry: MagicMock, openspec_repo: Path) -> None:
        """Test validation workflow with active change proposals."""
        # Setup OpenSpec with active proposal
        openspec_path = openspec_repo / "openspec"
        changes_dir = openspec_path / "changes" / "add-feature-x"
        changes_dir.mkdir(parents=True)

        feature_delta = FeatureDelta(
            feature_key="feature-1",
            change_type=ChangeType.ADDED,
            original_feature=None,
            proposed_feature=Feature(key="feature-1", title="Feature 1", outcomes=["Outcome 1"]),
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

        mock_adapter_class = MagicMock()
        mock_adapter = MagicMock()
        mock_adapter.detect.return_value = True
        mock_adapter.load_change_tracking.return_value = change_tracking
        mock_adapter_class.return_value = mock_adapter
        mock_registry.get.return_value = mock_adapter_class

        # Load active proposals
        active_tracking = load_active_change_proposals(openspec_repo)

        assert active_tracking is not None
        assert "add-feature-x" in active_tracking.proposals

    @beartype
    def test_spec_merging_for_validation(self) -> None:
        """Test spec merging for validation with multiple change types."""
        current_specs = {
            "feature-1": {"key": "feature-1", "title": "Feature 1", "outcomes": ["Old outcome"]},
            "feature-2": {"key": "feature-2", "title": "Feature 2"},
        }

        # Create change tracking with ADDED, MODIFIED, and REMOVED
        feature_delta_added = FeatureDelta(
            feature_key="feature-3",
            change_type=ChangeType.ADDED,
            original_feature=None,
            proposed_feature=Feature(key="feature-3", title="Feature 3", outcomes=["New feature"]),
            change_rationale=None,
            change_date=None,
            validation_status=None,
            validation_results=None,
            source_tracking=None,
        )

        feature_delta_modified = FeatureDelta(
            feature_key="feature-1",
            change_type=ChangeType.MODIFIED,
            original_feature=Feature(key="feature-1", title="Feature 1", outcomes=["Old outcome"]),
            proposed_feature=Feature(key="feature-1", title="Feature 1", outcomes=["New outcome"]),
            change_rationale=None,
            change_date=None,
            validation_status=None,
            validation_results=None,
            source_tracking=None,
        )

        feature_delta_removed = FeatureDelta(
            feature_key="feature-2",
            change_type=ChangeType.REMOVED,
            original_feature=Feature(key="feature-2", title="Feature 2", outcomes=[]),
            proposed_feature=None,
            change_rationale=None,
            change_date=None,
            validation_status=None,
            validation_results=None,
            source_tracking=None,
        )

        change_tracking = ChangeTracking(
            proposals={
                "change-1": ChangeProposal(
                    name="change-1",
                    title="Change 1",
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
            feature_deltas={"change-1": [feature_delta_added, feature_delta_modified, feature_delta_removed]},
        )

        merged = merge_specs_with_change_proposals(current_specs, change_tracking)

        # Verify ADDED: feature-3 included
        assert "feature-3" in merged

        # Verify MODIFIED: feature-1 updated
        assert merged["feature-1"]["outcomes"] == ["New outcome"]

        # Verify REMOVED: feature-2 excluded
        assert "feature-2" not in merged

    @beartype
    @patch("specfact_cli.validators.change_proposal_integration.AdapterRegistry")
    def test_validation_status_updates(self, mock_registry: MagicMock, openspec_repo: Path) -> None:
        """Test validation status updates in change proposals."""
        openspec_path = openspec_repo / "openspec"
        openspec_path.mkdir(exist_ok=True)

        feature_delta = FeatureDelta(
            feature_key="feature-1",
            change_type=ChangeType.ADDED,
            original_feature=None,
            proposed_feature=Feature(key="feature-1", title="Feature 1", outcomes=[]),
            change_rationale=None,
            change_date=None,
            validation_status=None,
            validation_results=None,
            source_tracking=None,
        )

        change_tracking = ChangeTracking(
            proposals={
                "change-1": ChangeProposal(
                    name="change-1",
                    title="Add Feature 1",
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
            feature_deltas={"change-1": [feature_delta]},
        )

        validation_results = {
            "feature-1": {"success": True, "contracts_validated": 5, "deviations": []},
        }

        mock_adapter_class = MagicMock()
        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter
        mock_registry.get.return_value = mock_adapter_class

        update_validation_status(change_tracking, validation_results, openspec_repo)

        assert feature_delta.validation_status == "passed"
        assert feature_delta.validation_results == validation_results["feature-1"]
        mock_adapter.save_change_tracking.assert_called_once()

    @beartype
    @patch("specfact_cli.validators.change_proposal_integration.AdapterRegistry")
    @patch("specfact_cli.validators.change_proposal_integration.requests")
    def test_validation_result_reporting_to_github(self, mock_requests: MagicMock, mock_registry: MagicMock) -> None:
        """Test reporting validation results to GitHub Issues."""
        from specfact_cli.models.source_tracking import SourceTracking

        feature_delta = FeatureDelta(
            feature_key="feature-1",
            change_type=ChangeType.ADDED,
            original_feature=None,
            proposed_feature=Feature(key="feature-1", title="Feature 1", outcomes=[]),
            change_rationale=None,
            change_date=None,
            validation_status=None,
            validation_results=None,
            source_tracking=None,
        )

        proposal = ChangeProposal(
            name="change-1",
            title="Add Feature 1",
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
            proposals={"change-1": proposal},
            feature_deltas={"change-1": [feature_delta]},
        )

        validation_results = {
            "feature-1": {"success": False, "error": "Contract violation detected"},
        }

        mock_adapter_class = MagicMock()
        mock_adapter = MagicMock()
        mock_adapter.base_url = "https://api.github.com"
        mock_adapter.api_token = "test-token"
        mock_adapter._add_issue_comment = MagicMock()
        mock_adapter_class.return_value = mock_adapter
        mock_registry.get.return_value = mock_adapter_class

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

        report_validation_results_to_backlog(change_tracking, validation_results)

        # Verify comment was added
        mock_adapter._add_issue_comment.assert_called_once()
        call_args = mock_adapter._add_issue_comment.call_args
        assert "Validation Results" in call_args[0][3]  # comment_text is 4th arg
        assert "FAILED" in call_args[0][3]

        # Verify label was updated
        mock_requests.patch.assert_called_once()
