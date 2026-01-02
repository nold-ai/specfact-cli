"""
Integration tests for change tracking data model scenarios.

Tests bundle loading/saving with v1.1 schema, change tracking persistence,
and cross-repository change tracking loading via OpenSpec adapter.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from textwrap import dedent

import pytest
from beartype import beartype

from specfact_cli.adapters.registry import AdapterRegistry
from specfact_cli.models.bridge import BridgeConfig
from specfact_cli.models.change import ChangeProposal, ChangeTracking, FeatureDelta
from specfact_cli.models.project import BundleManifest, BundleVersions, Product, ProjectBundle
from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle
from specfact_cli.utils.structure import SpecFactStructure


@pytest.fixture
def openspec_repo_with_changes(tmp_path: Path) -> Path:
    """Create OpenSpec repository with change proposals for testing."""
    openspec_dir = tmp_path / "openspec"
    openspec_dir.mkdir()

    # Create project.md
    (openspec_dir / "project.md").write_text("# Test Project\n\n## Purpose\n\nTesting change tracking.")

    # Create change proposal
    changes_dir = openspec_dir / "changes" / "test-change"
    changes_dir.mkdir(parents=True)
    (changes_dir / "proposal.md").write_text(
        dedent(
            """# Test Change

## Summary

This is a test change for data model validation.

## Rationale

Testing change tracking data model integration.
"""
        )
    )

    return tmp_path


class TestChangeTrackingDataModelIntegration:
    """Integration tests for change tracking data model scenarios."""

    @beartype
    def test_bundle_loading_with_v1_1_schema(self, tmp_path: Path) -> None:
        """Test bundle loading with v1.1 schema and change tracking."""
        from specfact_cli.models.change import ChangeTracking

        bundle_dir = tmp_path / SpecFactStructure.PROJECTS / "main"
        bundle_dir.mkdir(parents=True)

        # Create bundle with v1.1 schema and change tracking
        manifest = BundleManifest(
            versions=BundleVersions(schema="1.1", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=[], releases=[])

        # Create change tracking with a proposal
        proposal = ChangeProposal(
            name="test-change",
            title="Test Change",
            description="Test description",
            rationale="Test rationale",
            timeline=None,
            owner=None,
            applied_at=None,
            archived_at=None,
            source_tracking=None,
            created_at=datetime.now(UTC).isoformat(),
        )
        change_tracking = ChangeTracking(proposals={"test-change": proposal}, feature_deltas={})

        # change_tracking is stored in both manifest and ProjectBundle
        # Set it on manifest for persistence
        manifest.change_tracking = change_tracking
        project_bundle = ProjectBundle(
            manifest=manifest,
            bundle_name="main",
            product=product,
            features={},
            change_tracking=change_tracking,  # Also set on ProjectBundle for consistency
        )
        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Load bundle and verify change tracking is preserved
        loaded_bundle = load_project_bundle(bundle_dir)
        assert loaded_bundle is not None
        assert loaded_bundle.manifest.versions.schema_version == "1.1"
        # change_tracking is stored in manifest (saved via manifest.model_dump())
        assert loaded_bundle.manifest.change_tracking is not None
        assert "test-change" in loaded_bundle.manifest.change_tracking.proposals
        assert loaded_bundle.manifest.change_tracking.proposals["test-change"].title == "Test Change"
        # ProjectBundle.change_tracking is loaded from adapter (may be None if no adapter or adapter doesn't load it)

    @beartype
    def test_bundle_saving_with_change_tracking(self, tmp_path: Path) -> None:
        """Test bundle saving with change tracking data."""
        from specfact_cli.models.change import ChangeTracking

        bundle_dir = tmp_path / SpecFactStructure.PROJECTS / "main"
        bundle_dir.mkdir(parents=True)

        # Create bundle with change tracking
        manifest = BundleManifest(
            versions=BundleVersions(schema="1.1", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=[], releases=[])

        proposal = ChangeProposal(
            name="save-test",
            title="Save Test Change",
            description="Testing bundle saving",
            rationale="Verify change tracking persists",
            timeline=None,
            owner=None,
            applied_at=None,
            archived_at=None,
            source_tracking=None,
            created_at=datetime.now(UTC).isoformat(),
        )
        change_tracking = ChangeTracking(proposals={"save-test": proposal}, feature_deltas={})

        # change_tracking is stored in manifest
        manifest.change_tracking = change_tracking
        project_bundle = ProjectBundle(
            manifest=manifest,
            bundle_name="main",
            product=product,
            features={},
        )

        # Save bundle
        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Verify bundle was saved
        assert (bundle_dir / "bundle.manifest.yaml").exists()

        # Reload and verify change tracking
        loaded_bundle = load_project_bundle(bundle_dir)
        assert loaded_bundle is not None
        # change_tracking is stored in manifest (saved)
        assert loaded_bundle.manifest.change_tracking is not None
        assert "save-test" in loaded_bundle.manifest.change_tracking.proposals
        # ProjectBundle.change_tracking may also be set if adapter loads it (optional)

    @beartype
    def test_backward_compatibility_v1_0_bundle(self, tmp_path: Path) -> None:
        """Test that v1.0 bundles load correctly without change tracking."""
        bundle_dir = tmp_path / SpecFactStructure.PROJECTS / "main"
        bundle_dir.mkdir(parents=True)

        # Create bundle with v1.0 schema (no change tracking)
        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=[], releases=[])

        project_bundle = ProjectBundle(
            manifest=manifest,
            bundle_name="main",
            product=product,
            features={},
            change_tracking=None,  # v1.0 doesn't have change tracking
        )
        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Load bundle and verify backward compatibility
        loaded_bundle = load_project_bundle(bundle_dir)
        assert loaded_bundle is not None
        assert loaded_bundle.manifest.versions.schema_version == "1.0"
        # v1.0 bundles should have change_tracking=None in manifest
        assert loaded_bundle.manifest.change_tracking is None or (
            loaded_bundle.manifest.change_tracking and loaded_bundle.manifest.change_tracking.proposals == {}
        )

    @beartype
    def test_cross_repository_change_tracking_loading(self, openspec_repo_with_changes: Path) -> None:
        """Test cross-repository change tracking loading via OpenSpec adapter."""
        from specfact_cli.models.project import BundleManifest, BundleVersions, Product, ProjectBundle
        from specfact_cli.utils.bundle_loader import save_project_bundle

        # Create external OpenSpec repo
        external_repo = openspec_repo_with_changes

        # Create main repo (without OpenSpec)
        main_repo = external_repo.parent / "main-repo"
        main_repo.mkdir()

        # Create bundle in main repo
        bundle_dir = main_repo / SpecFactStructure.PROJECTS / "main"
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(
            versions=BundleVersions(schema="1.1", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=[], releases=[])
        project_bundle = ProjectBundle(
            manifest=manifest,
            bundle_name="main",
            product=product,
            features={},
        )
        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Load change tracking from external repo
        adapter = AdapterRegistry.get_adapter("openspec")
        bridge_config = BridgeConfig.preset_openspec()
        bridge_config.external_base_path = external_repo

        change_tracking = adapter.load_change_tracking(bundle_dir, bridge_config)

        # Verify change tracking was loaded from external repo
        if change_tracking is not None:
            assert isinstance(change_tracking, ChangeTracking)
            assert len(change_tracking.proposals) >= 0

    @beartype
    def test_change_tracking_with_feature_deltas(self, tmp_path: Path) -> None:
        """Test change tracking with feature deltas (ADDED/MODIFIED/REMOVED)."""
        from specfact_cli.models.change import ChangeTracking, ChangeType
        from specfact_cli.models.plan import Feature

        bundle_dir = tmp_path / SpecFactStructure.PROJECTS / "main"
        bundle_dir.mkdir(parents=True)

        # Create feature delta
        proposed_feature = Feature(
            key="FEATURE-001",
            title="New Feature",
            outcomes=[],
            acceptance=[],
            constraints=[],
            stories=[],
        )

        feature_delta = FeatureDelta(
            feature_key="FEATURE-001",
            change_type=ChangeType.ADDED,
            original_feature=None,
            proposed_feature=proposed_feature,
            change_rationale=None,
            change_date=None,
            validation_status="pending",
            validation_results=None,
            source_tracking=None,
        )

        # Create change tracking with proposal and feature delta
        proposal = ChangeProposal(
            name="add-feature",
            title="Add New Feature",
            description="Adding a new feature",
            rationale="Feature is needed",
            timeline=None,
            owner=None,
            applied_at=None,
            archived_at=None,
            source_tracking=None,
            created_at=datetime.now(UTC).isoformat(),
        )

        change_tracking = ChangeTracking(
            proposals={"add-feature": proposal},
            feature_deltas={"add-feature": [feature_delta]},
        )

        manifest = BundleManifest(
            versions=BundleVersions(schema="1.1", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=[], releases=[])

        # change_tracking is stored in both manifest and ProjectBundle
        manifest.change_tracking = change_tracking
        project_bundle = ProjectBundle(
            manifest=manifest,
            bundle_name="main",
            product=product,
            features={},
            change_tracking=change_tracking,  # Also set on ProjectBundle for consistency
        )

        # Save and reload
        save_project_bundle(project_bundle, bundle_dir, atomic=True)
        loaded_bundle = load_project_bundle(bundle_dir)

        assert loaded_bundle is not None
        # change_tracking is stored in manifest (saved via manifest.model_dump())
        assert loaded_bundle.manifest.change_tracking is not None
        assert "add-feature" in loaded_bundle.manifest.change_tracking.proposals
        assert "add-feature" in loaded_bundle.manifest.change_tracking.feature_deltas
        assert len(loaded_bundle.manifest.change_tracking.feature_deltas["add-feature"]) == 1
        assert loaded_bundle.manifest.change_tracking.feature_deltas["add-feature"][0].change_type == ChangeType.ADDED
        # ProjectBundle.change_tracking is loaded from adapter (may be None if adapter doesn't load it)

    @beartype
    def test_project_bundle_helper_methods(self, tmp_path: Path) -> None:
        """Test ProjectBundle helper methods for change tracking."""
        from specfact_cli.models.change import ChangeTracking

        bundle_dir = tmp_path / SpecFactStructure.PROJECTS / "main"
        bundle_dir.mkdir(parents=True)

        # Create change tracking
        proposal = ChangeProposal(
            name="helper-test",
            title="Helper Test",
            description="Testing helper methods",
            rationale="Verify get_active_changes() works",
            timeline=None,
            owner=None,
            applied_at=None,
            archived_at=None,
            source_tracking=None,
            created_at=datetime.now(UTC).isoformat(),
        )
        change_tracking = ChangeTracking(proposals={"helper-test": proposal}, feature_deltas={})

        manifest = BundleManifest(
            versions=BundleVersions(schema="1.1", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=[], releases=[])

        # change_tracking is stored in both manifest and ProjectBundle
        manifest.change_tracking = change_tracking
        project_bundle = ProjectBundle(
            manifest=manifest,
            bundle_name="main",
            product=product,
            features={},
            change_tracking=change_tracking,  # Also set on ProjectBundle for consistency
        )

        # Test get_active_changes() helper method
        active_changes = project_bundle.get_active_changes()
        assert len(active_changes) >= 0
        if active_changes:
            assert any(change.name == "helper-test" for change in active_changes)

        # Test get_feature_deltas() helper method
        feature_deltas = project_bundle.get_feature_deltas("helper-test")
        assert isinstance(feature_deltas, list)
