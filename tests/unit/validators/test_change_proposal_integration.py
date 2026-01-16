"""
Unit tests for change proposal validation integration.

Tests the integration between OpenSpec change proposals and SpecFact validation.
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


class TestLoadActiveChangeProposals:
    """Test loading active change proposals from OpenSpec."""

    @beartype
    @patch("specfact_cli.validators.change_proposal_integration.AdapterRegistry")
    def test_load_active_proposals_openspec_not_found(self, mock_registry: MagicMock, tmp_path: Path) -> None:
        """Test when OpenSpec repository is not found."""
        mock_registry.get_adapter.side_effect = ValueError("Adapter not registered")

        result = load_active_change_proposals(tmp_path)

        assert result is None

    @beartype
    @patch("specfact_cli.validators.change_proposal_integration.AdapterRegistry")
    def test_load_active_proposals_no_openspec_dir(self, mock_registry: MagicMock, tmp_path: Path) -> None:
        """Test when openspec directory doesn't exist."""
        mock_adapter = MagicMock()
        mock_adapter.detect.return_value = False
        mock_registry.get_adapter.return_value = mock_adapter

        result = load_active_change_proposals(tmp_path)

        assert result is None

    @beartype
    @patch("specfact_cli.validators.change_proposal_integration.AdapterRegistry")
    def test_load_active_proposals_filters_by_status(self, mock_registry: MagicMock, tmp_path: Path) -> None:
        """Test that only active proposals (proposed/in-progress) are loaded."""
        openspec_path = tmp_path / "openspec"
        openspec_path.mkdir()

        mock_adapter = MagicMock()
        mock_adapter.detect.return_value = True
        mock_adapter.load_change_tracking.return_value = ChangeTracking(
            proposals={
                "active-1": ChangeProposal(
                    name="active-1",
                    title="Active Proposal 1",
                    description="Test",
                    rationale="Test",
                    status="proposed",
                    created_at="2025-01-01T10:00:00Z",
                    timeline=None,
                    owner=None,
                    applied_at=None,
                    archived_at=None,
                    source_tracking=None,
                ),
                "active-2": ChangeProposal(
                    name="active-2",
                    title="Active Proposal 2",
                    description="Test",
                    rationale="Test",
                    status="in-progress",
                    created_at="2025-01-01T10:00:00Z",
                    timeline=None,
                    owner=None,
                    applied_at=None,
                    archived_at=None,
                    source_tracking=None,
                ),
                "archived": ChangeProposal(
                    name="archived",
                    title="Archived Proposal",
                    description="Test",
                    rationale="Test",
                    status="applied",
                    created_at="2025-01-01T10:00:00Z",
                    timeline=None,
                    owner=None,
                    applied_at=None,
                    archived_at=None,
                    source_tracking=None,
                ),
            }
        )
        mock_registry.get_adapter.return_value = mock_adapter

        result = load_active_change_proposals(tmp_path)

        assert result is not None
        assert "active-1" in result.proposals
        assert "active-2" in result.proposals
        assert "archived" not in result.proposals


class TestMergeSpecsWithChangeProposals:
    """Test merging specs with change proposals."""

    @beartype
    def test_merge_added_requirement(self) -> None:
        """Test merging ADDED requirement into validation set."""
        current_specs = {"feature-1": {"key": "feature-1", "title": "Feature 1"}}

        feature_delta = FeatureDelta(
            feature_key="feature-2",
            change_type=ChangeType.ADDED,
            original_feature=None,
            proposed_feature=Feature(key="feature-2", title="Feature 2", outcomes=["Outcome 2"]),
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
                    title="Add Feature 2",
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

        merged = merge_specs_with_change_proposals(current_specs, change_tracking)

        assert "feature-1" in merged
        assert "feature-2" in merged
        assert merged["feature-2"]["key"] == "feature-2"

    @beartype
    def test_merge_modified_requirement(self) -> None:
        """Test merging MODIFIED requirement replaces existing."""
        current_specs = {"feature-1": {"key": "feature-1", "title": "Feature 1", "outcomes": ["Old outcome"]}}

        feature_delta = FeatureDelta(
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

        change_tracking = ChangeTracking(
            proposals={
                "change-1": ChangeProposal(
                    name="change-1",
                    title="Modify Feature 1",
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

        merged = merge_specs_with_change_proposals(current_specs, change_tracking)

        assert "feature-1" in merged
        assert merged["feature-1"]["outcomes"] == ["New outcome"]

    @beartype
    def test_merge_removed_requirement(self) -> None:
        """Test merging REMOVED requirement excludes from validation set."""
        current_specs = {
            "feature-1": {"key": "feature-1", "title": "Feature 1"},
            "feature-2": {"key": "feature-2", "title": "Feature 2"},
        }

        feature_delta = FeatureDelta(
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
                    title="Remove Feature 2",
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

        merged = merge_specs_with_change_proposals(current_specs, change_tracking)

        assert "feature-1" in merged
        assert "feature-2" not in merged

    @beartype
    def test_merge_conflict_detection(self) -> None:
        """Test conflict detection when same requirement modified in multiple proposals."""
        current_specs = {"feature-1": {"key": "feature-1", "title": "Feature 1"}}

        feature_delta_1 = FeatureDelta(
            feature_key="feature-1",
            change_type=ChangeType.MODIFIED,
            original_feature=Feature(key="feature-1", title="Feature 1", outcomes=[]),
            proposed_feature=Feature(key="feature-1", title="Feature 1", outcomes=["Change 1"]),
            change_rationale=None,
            change_date=None,
            validation_status=None,
            validation_results=None,
            source_tracking=None,
        )

        feature_delta_2 = FeatureDelta(
            feature_key="feature-1",
            change_type=ChangeType.MODIFIED,
            original_feature=Feature(key="feature-1", title="Feature 1", outcomes=[]),
            proposed_feature=Feature(key="feature-1", title="Feature 1", outcomes=["Change 2"]),
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
                    title="Modify Feature 1 (v1)",
                    description="Test",
                    rationale="Test",
                    created_at="2025-01-01T10:00:00Z",
                    timeline=None,
                    owner=None,
                    applied_at=None,
                    archived_at=None,
                    source_tracking=None,
                ),
                "change-2": ChangeProposal(
                    name="change-2",
                    title="Modify Feature 1 (v2)",
                    description="Test",
                    rationale="Test",
                    created_at="2025-01-01T10:00:00Z",
                    timeline=None,
                    owner=None,
                    applied_at=None,
                    archived_at=None,
                    source_tracking=None,
                ),
            },
            feature_deltas={"change-1": [feature_delta_1], "change-2": [feature_delta_2]},
        )

        with pytest.raises(ValueError, match="Spec merging conflicts detected"):
            merge_specs_with_change_proposals(current_specs, change_tracking)


class TestUpdateValidationStatus:
    """Test updating validation status in change proposals."""

    @beartype
    @patch("specfact_cli.validators.change_proposal_integration.AdapterRegistry")
    def test_update_validation_status_success(self, mock_registry: MagicMock, tmp_path: Path) -> None:
        """Test updating validation status for successful validation."""
        openspec_path = tmp_path / "openspec"
        openspec_path.mkdir()

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
            "feature-1": {"success": True, "details": "Validation passed"},
        }

        mock_adapter = MagicMock()
        mock_registry.get_adapter.return_value = mock_adapter

        update_validation_status(change_tracking, validation_results, tmp_path)

        assert feature_delta.validation_status == "passed"
        assert feature_delta.validation_results == {"success": True, "details": "Validation passed"}
        mock_adapter.save_change_tracking.assert_called_once()

    @beartype
    @patch("specfact_cli.validators.change_proposal_integration.AdapterRegistry")
    def test_update_validation_status_failure(self, mock_registry: MagicMock, tmp_path: Path) -> None:
        """Test updating validation status for failed validation."""
        openspec_path = tmp_path / "openspec"
        openspec_path.mkdir()

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
            "feature-1": {"success": False, "error": "Validation failed"},
        }

        mock_adapter_class = MagicMock()
        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter
        mock_registry.get.return_value = mock_adapter_class

        update_validation_status(change_tracking, validation_results, tmp_path)

        assert feature_delta.validation_status == "failed"
        assert feature_delta.validation_results == {"success": False, "error": "Validation failed"}

    @beartype
    @patch("specfact_cli.validators.change_proposal_integration.AdapterRegistry")
    def test_update_validation_status_boolean_false(self, mock_registry: MagicMock, tmp_path: Path) -> None:
        """Test updating validation status with boolean False (should be treated as failed, not pending)."""
        openspec_path = tmp_path / "openspec"
        openspec_path.mkdir()

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

        # Test with boolean False - should be treated as failed, not pending
        validation_results = {
            "feature-1": False,
        }

        mock_adapter = MagicMock()
        mock_registry.get_adapter.return_value = mock_adapter

        update_validation_status(change_tracking, validation_results, tmp_path)

        assert feature_delta.validation_status == "failed"
        assert feature_delta.validation_results == {"success": False}
        mock_adapter.save_change_tracking.assert_called_once()

    @beartype
    @patch("specfact_cli.validators.change_proposal_integration.AdapterRegistry")
    def test_update_validation_status_empty_dict(self, mock_registry: MagicMock, tmp_path: Path) -> None:
        """Test updating validation status with empty dict (should be treated as failed, not pending)."""
        openspec_path = tmp_path / "openspec"
        openspec_path.mkdir()

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

        # Test with empty dict - should be treated as failed (success defaults to False)
        validation_results = {
            "feature-1": {},
        }

        mock_adapter = MagicMock()
        mock_registry.get_adapter.return_value = mock_adapter

        update_validation_status(change_tracking, validation_results, tmp_path)

        assert feature_delta.validation_status == "failed"
        assert feature_delta.validation_results == {}
        mock_adapter.save_change_tracking.assert_called_once()


class TestReportValidationResultsToBacklog:
    """Test reporting validation results to backlog."""

    @beartype
    @patch("specfact_cli.validators.change_proposal_integration.AdapterRegistry")
    @patch("specfact_cli.validators.change_proposal_integration.requests")
    def test_report_to_github_success(self, mock_requests: MagicMock, mock_registry: MagicMock) -> None:
        """Test reporting validation results to GitHub issue."""
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
            "feature-1": {"success": True},
        }

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

        report_validation_results_to_backlog(change_tracking, validation_results)

        # Verify comment was added
        mock_adapter._add_issue_comment.assert_called_once()

    @beartype
    @patch("specfact_cli.validators.change_proposal_integration.AdapterRegistry")
    @patch("specfact_cli.validators.change_proposal_integration.requests")
    def test_report_to_github_boolean_false(self, mock_requests: MagicMock, mock_registry: MagicMock) -> None:
        """Test reporting boolean False validation results to GitHub issue (should show FAILED, not PENDING)."""
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

        # Test with boolean False - should trigger failed status and label update
        validation_results = {
            "feature-1": False,
        }

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

        report_validation_results_to_backlog(change_tracking, validation_results)

        # Verify comment was added with FAILED status
        mock_adapter._add_issue_comment.assert_called_once()
        call_args = mock_adapter._add_issue_comment.call_args
        comment_text = call_args[0][3]
        assert "Validation Results" in comment_text
        assert "FAILED" in comment_text

    @beartype
    @patch("specfact_cli.validators.change_proposal_integration.AdapterRegistry")
    def test_report_no_github_adapter(self, mock_registry: MagicMock) -> None:
        """Test graceful handling when GitHub adapter is not available."""
        mock_registry.get.return_value = None

        change_tracking = ChangeTracking()
        validation_results = {}

        # Should not raise error
        report_validation_results_to_backlog(change_tracking, validation_results)
