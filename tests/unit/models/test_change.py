"""
Unit tests for change tracking data models - Contract-First approach.

Tests for tool-agnostic change tracking models including ChangeType,
FeatureDelta, ChangeProposal, ChangeTracking, and ChangeArchive.
"""

from datetime import UTC, datetime

import pytest

from specfact_cli.models.change import (
    ChangeArchive,
    ChangeProposal,
    ChangeTracking,
    ChangeType,
    FeatureDelta,
)
from specfact_cli.models.plan import Feature
from specfact_cli.models.source_tracking import SourceTracking


class TestChangeType:
    """Tests for ChangeType enum."""

    def test_enum_values(self):
        """Test ChangeType enum has correct values."""
        assert ChangeType.ADDED == "added"
        assert ChangeType.MODIFIED == "modified"
        assert ChangeType.REMOVED == "removed"

    def test_enum_membership(self):
        """Test ChangeType enum membership."""
        assert isinstance(ChangeType.ADDED, ChangeType)
        assert ChangeType.ADDED in ChangeType


class TestFeatureDelta:
    """Tests for FeatureDelta model."""

    def test_added_feature_delta(self):
        """Test FeatureDelta for ADDED change type."""
        proposed_feature = Feature(
            key="FEATURE-001",
            title="New Feature",
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        delta = FeatureDelta(
            feature_key="FEATURE-001",
            change_type=ChangeType.ADDED,
            original_feature=None,
            proposed_feature=proposed_feature,
            change_rationale=None,
            change_date=None,
            validation_status=None,
            validation_results=None,
            source_tracking=None,
        )
        assert delta.feature_key == "FEATURE-001"
        assert delta.change_type == ChangeType.ADDED
        assert delta.proposed_feature == proposed_feature
        assert delta.original_feature is None

    def test_modified_feature_delta(self):
        """Test FeatureDelta for MODIFIED change type."""
        original_feature = Feature(
            key="FEATURE-001",
            title="Original Feature",
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        proposed_feature = Feature(
            key="FEATURE-001",
            title="Modified Feature",
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        delta = FeatureDelta(
            feature_key="FEATURE-001",
            change_type=ChangeType.MODIFIED,
            original_feature=original_feature,
            proposed_feature=proposed_feature,
            change_rationale=None,
            change_date=None,
            validation_status=None,
            validation_results=None,
            source_tracking=None,
        )
        assert delta.change_type == ChangeType.MODIFIED
        assert delta.original_feature == original_feature
        assert delta.proposed_feature == proposed_feature

    def test_removed_feature_delta(self):
        """Test FeatureDelta for REMOVED change type."""
        original_feature = Feature(
            key="FEATURE-001",
            title="Removed Feature",
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        delta = FeatureDelta(
            feature_key="FEATURE-001",
            change_type=ChangeType.REMOVED,
            original_feature=original_feature,
            proposed_feature=None,
            change_rationale=None,
            change_date=None,
            validation_status=None,
            validation_results=None,
            source_tracking=None,
        )
        assert delta.change_type == ChangeType.REMOVED
        assert delta.original_feature == original_feature
        assert delta.proposed_feature is None

    def test_feature_delta_with_validation(self):
        """Test FeatureDelta with validation status and results."""
        proposed_feature = Feature(
            key="FEATURE-001",
            title="New Feature",
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        delta = FeatureDelta(
            feature_key="FEATURE-001",
            change_type=ChangeType.ADDED,
            original_feature=None,
            proposed_feature=proposed_feature,
            change_rationale=None,
            change_date=None,
            validation_status="passed",
            validation_results={"contracts_valid": True, "tests_passing": True},
            source_tracking=None,
        )
        assert delta.validation_status == "passed"
        assert delta.validation_results == {"contracts_valid": True, "tests_passing": True}

    def test_feature_delta_with_source_tracking(self):
        """Test FeatureDelta with source tracking metadata."""
        proposed_feature = Feature(
            key="FEATURE-001",
            title="New Feature",
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        # SourceTracking currently tracks implementation/test files, not tool metadata
        # Tool-specific metadata would be stored differently (future enhancement)
        source_tracking = SourceTracking(implementation_files=["src/feature.py"])
        delta = FeatureDelta(
            feature_key="FEATURE-001",
            change_type=ChangeType.ADDED,
            original_feature=None,
            proposed_feature=proposed_feature,
            change_rationale=None,
            change_date=None,
            validation_status=None,
            validation_results=None,
            source_tracking=source_tracking,
        )
        assert delta.source_tracking is not None
        assert "src/feature.py" in delta.source_tracking.implementation_files

    def test_feature_delta_validation_requires_original_for_modified(self):
        """Test that MODIFIED change type requires original_feature."""
        from pydantic import ValidationError

        proposed_feature = Feature(
            key="FEATURE-001",
            title="Modified Feature",
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        # This should raise a validation error
        with pytest.raises(ValidationError):  # Pydantic validation error
            FeatureDelta(
                feature_key="FEATURE-001",
                change_type=ChangeType.MODIFIED,
                original_feature=None,  # Missing - should cause validation error
                proposed_feature=proposed_feature,
                change_rationale=None,
                change_date=None,
                validation_status=None,
                validation_results=None,
                source_tracking=None,
            )

    def test_feature_delta_validation_requires_proposed_for_added(self):
        """Test that ADDED change type requires proposed_feature."""
        from pydantic import ValidationError

        # This should raise a validation error
        with pytest.raises(ValidationError):  # Pydantic validation error
            FeatureDelta(
                feature_key="FEATURE-001",
                change_type=ChangeType.ADDED,
                original_feature=None,
                proposed_feature=None,  # Missing - should cause validation error
                change_rationale=None,
                change_date=None,
                validation_status=None,
                validation_results=None,
                source_tracking=None,
            )


class TestChangeProposal:
    """Tests for ChangeProposal model."""

    def test_create_change_proposal(self):
        """Test creating a ChangeProposal."""
        proposal = ChangeProposal(
            name="add-user-feedback",
            title="Add User Feedback Feature",
            description="Add user feedback collection functionality",
            rationale="Users need to provide feedback on features",
            timeline=None,
            owner=None,
            stakeholders=[],
            dependencies=[],
            status="proposed",
            created_at=datetime.now(UTC).isoformat(),
            applied_at=None,
            archived_at=None,
            source_tracking=None,
        )
        assert proposal.name == "add-user-feedback"
        assert proposal.title == "Add User Feedback Feature"
        assert proposal.status == "proposed"  # Default status
        assert proposal.applied_at is None
        assert proposal.archived_at is None

    def test_change_proposal_with_timeline(self):
        """Test ChangeProposal with timeline and owner."""
        proposal = ChangeProposal(
            name="add-user-feedback",
            title="Add User Feedback Feature",
            description="Add user feedback collection functionality",
            rationale="Users need to provide feedback on features",
            timeline="Q1 2025",
            owner="product-owner@example.com",
            stakeholders=["dev-team@example.com", "qa-team@example.com"],
            dependencies=[],
            status="proposed",
            created_at=datetime.now(UTC).isoformat(),
            applied_at=None,
            archived_at=None,
            source_tracking=None,
        )
        assert proposal.timeline == "Q1 2025"
        assert proposal.owner == "product-owner@example.com"
        assert len(proposal.stakeholders) == 2

    def test_change_proposal_status_transitions(self):
        """Test ChangeProposal status field."""
        proposal = ChangeProposal(
            name="add-user-feedback",
            title="Add User Feedback Feature",
            description="Add user feedback collection functionality",
            rationale="Users need to provide feedback on features",
            timeline=None,
            owner=None,
            stakeholders=[],
            dependencies=[],
            status="in-progress",
            created_at=datetime.now(UTC).isoformat(),
            applied_at=None,
            archived_at=None,
            source_tracking=None,
        )
        assert proposal.status == "in-progress"

        proposal.status = "applied"
        proposal.applied_at = datetime.now(UTC).isoformat()
        assert proposal.status == "applied"
        assert proposal.applied_at is not None

    def test_change_proposal_with_source_tracking(self):
        """Test ChangeProposal with source tracking metadata."""
        # SourceTracking currently tracks implementation/test files, not tool metadata
        # Tool-specific metadata would be stored differently (future enhancement)
        source_tracking = SourceTracking(implementation_files=["openspec/changes/add-user-feedback/proposal.md"])
        proposal = ChangeProposal(
            name="add-user-feedback",
            title="Add User Feedback Feature",
            description="Add user feedback collection functionality",
            rationale="Users need to provide feedback on features",
            timeline=None,
            owner=None,
            stakeholders=[],
            dependencies=[],
            status="proposed",
            created_at=datetime.now(UTC).isoformat(),
            applied_at=None,
            archived_at=None,
            source_tracking=source_tracking,
        )
        assert proposal.source_tracking is not None
        assert "openspec/changes/add-user-feedback/proposal.md" in proposal.source_tracking.implementation_files


class TestChangeTracking:
    """Tests for ChangeTracking model."""

    def test_create_change_tracking(self):
        """Test creating a ChangeTracking container."""
        tracking = ChangeTracking()
        assert tracking.proposals == {}
        assert tracking.feature_deltas == {}

    def test_change_tracking_with_proposals(self):
        """Test ChangeTracking with proposals."""
        proposal1 = ChangeProposal(
            name="add-user-feedback",
            title="Add User Feedback Feature",
            description="Add user feedback collection functionality",
            rationale="Users need to provide feedback on features",
            timeline=None,
            owner=None,
            stakeholders=[],
            dependencies=[],
            status="proposed",
            created_at=datetime.now(UTC).isoformat(),
            applied_at=None,
            archived_at=None,
            source_tracking=None,
        )
        proposal2 = ChangeProposal(
            name="update-auth",
            title="Update Authentication",
            description="Update authentication system",
            rationale="Security improvements needed",
            timeline=None,
            owner=None,
            stakeholders=[],
            dependencies=[],
            status="proposed",
            created_at=datetime.now(UTC).isoformat(),
            applied_at=None,
            archived_at=None,
            source_tracking=None,
        )
        tracking = ChangeTracking(
            proposals={
                "add-user-feedback": proposal1,
                "update-auth": proposal2,
            }
        )
        assert len(tracking.proposals) == 2
        assert "add-user-feedback" in tracking.proposals
        assert "update-auth" in tracking.proposals

    def test_change_tracking_with_feature_deltas(self):
        """Test ChangeTracking with feature deltas."""
        proposed_feature = Feature(
            key="FEATURE-001",
            title="New Feature",
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        delta = FeatureDelta(
            feature_key="FEATURE-001",
            change_type=ChangeType.ADDED,
            original_feature=None,
            proposed_feature=proposed_feature,
            change_rationale=None,
            change_date=None,
            validation_status=None,
            validation_results=None,
            source_tracking=None,
        )
        tracking = ChangeTracking(
            feature_deltas={
                "add-user-feedback": [delta],
            }
        )
        assert len(tracking.feature_deltas) == 1
        assert "add-user-feedback" in tracking.feature_deltas
        assert len(tracking.feature_deltas["add-user-feedback"]) == 1


class TestChangeArchive:
    """Tests for ChangeArchive model."""

    def test_create_change_archive(self):
        """Test creating a ChangeArchive entry."""
        proposed_feature = Feature(
            key="FEATURE-001",
            title="New Feature",
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        delta = FeatureDelta(
            feature_key="FEATURE-001",
            change_type=ChangeType.ADDED,
            original_feature=None,
            proposed_feature=proposed_feature,
            change_rationale=None,
            change_date=None,
            validation_status=None,
            validation_results=None,
            source_tracking=None,
        )
        archive = ChangeArchive(
            change_name="add-user-feedback",
            applied_at=datetime.now(UTC).isoformat(),
            applied_by="developer@example.com",
            pr_number="123",
            commit_hash="abc123",
            feature_deltas=[delta],
            validation_results=None,
            source_tracking=None,
        )
        assert archive.change_name == "add-user-feedback"
        assert archive.applied_by == "developer@example.com"
        assert archive.pr_number == "123"
        assert archive.commit_hash == "abc123"
        assert len(archive.feature_deltas) == 1

    def test_change_archive_with_validation_results(self):
        """Test ChangeArchive with validation results."""
        proposed_feature = Feature(
            key="FEATURE-001",
            title="New Feature",
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        delta = FeatureDelta(
            feature_key="FEATURE-001",
            change_type=ChangeType.ADDED,
            original_feature=None,
            proposed_feature=proposed_feature,
            change_rationale=None,
            change_date=None,
            validation_status=None,
            validation_results=None,
            source_tracking=None,
        )
        archive = ChangeArchive(
            change_name="add-user-feedback",
            applied_at=datetime.now(UTC).isoformat(),
            applied_by=None,
            pr_number=None,
            commit_hash=None,
            feature_deltas=[delta],
            validation_results={"contracts_valid": True, "tests_passing": True, "coverage": 85.5},
            source_tracking=None,
        )
        assert archive.validation_results is not None
        assert archive.validation_results["coverage"] == 85.5
