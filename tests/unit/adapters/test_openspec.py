"""Unit tests for OpenSpec bridge adapter."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from specfact_cli.adapters.openspec import OpenSpecAdapter
from specfact_cli.adapters.registry import AdapterRegistry
from specfact_cli.models.bridge import AdapterType, BridgeConfig


@pytest.fixture
def openspec_adapter() -> OpenSpecAdapter:
    """Create OpenSpec adapter instance for testing."""
    return OpenSpecAdapter()


@pytest.fixture
def bridge_config() -> BridgeConfig:
    """Create bridge config for testing."""
    return BridgeConfig.preset_openspec()


@pytest.fixture
def openspec_repo(tmp_path: Path) -> Path:
    """Create a temporary OpenSpec repository structure."""
    openspec_dir = tmp_path / "openspec"
    openspec_dir.mkdir()
    (openspec_dir / "project.md").write_text(
        """# Project

## Purpose
Test project for OpenSpec integration.
"""
    )
    specs_dir = openspec_dir / "specs"
    specs_dir.mkdir()
    feature_dir = specs_dir / "001-auth"
    feature_dir.mkdir()
    (feature_dir / "spec.md").write_text(
        """# Authentication Feature

## Overview
User authentication system.
"""
    )
    changes_dir = openspec_dir / "changes"
    changes_dir.mkdir()
    change_dir = changes_dir / "add-feature-x"
    change_dir.mkdir()
    (change_dir / "proposal.md").write_text(
        """# Change Proposal: Add Feature X

## Summary
Add new feature X.
"""
    )
    return tmp_path


class TestOpenSpecAdapter:
    """Test OpenSpec adapter implementation."""

    def test_detect_same_repo(self, openspec_adapter: OpenSpecAdapter, openspec_repo: Path) -> None:
        """Test detecting OpenSpec in same repository."""
        assert openspec_adapter.detect(openspec_repo) is True

    def test_detect_cross_repo(self, openspec_adapter: OpenSpecAdapter, tmp_path: Path) -> None:
        """Test detecting OpenSpec in cross-repo scenario."""
        external_path = tmp_path / "external"
        openspec_dir = external_path / "openspec"
        openspec_dir.mkdir(parents=True)
        (openspec_dir / "project.md").write_text("# Project")

        bridge_config = BridgeConfig.preset_openspec()
        bridge_config.external_base_path = external_path

        assert openspec_adapter.detect(tmp_path, bridge_config) is True

    def test_detect_not_openspec(self, openspec_adapter: OpenSpecAdapter, tmp_path: Path) -> None:
        """Test detecting non-OpenSpec repository."""
        assert openspec_adapter.detect(tmp_path) is False

    def test_get_capabilities(self, openspec_adapter: OpenSpecAdapter, openspec_repo: Path) -> None:
        """Test getting adapter capabilities."""
        capabilities = openspec_adapter.get_capabilities(openspec_repo)

        assert capabilities.tool == "openspec"
        assert capabilities.version is None
        assert capabilities.layout == "openspec"
        assert capabilities.specs_dir == "openspec/specs"

    def test_get_capabilities_cross_repo(self, openspec_adapter: OpenSpecAdapter, tmp_path: Path) -> None:
        """Test getting capabilities with cross-repo configuration."""
        external_path = tmp_path / "external"
        openspec_dir = external_path / "openspec"
        openspec_dir.mkdir(parents=True)
        (openspec_dir / "project.md").write_text("# Project")

        bridge_config = BridgeConfig.preset_openspec()
        bridge_config.external_base_path = external_path

        capabilities = openspec_adapter.get_capabilities(tmp_path, bridge_config)

        assert capabilities.tool == "openspec"

    def test_generate_bridge_config(self, openspec_adapter: OpenSpecAdapter, tmp_path: Path) -> None:
        """Test generating bridge config."""
        bridge_config = openspec_adapter.generate_bridge_config(tmp_path)

        assert bridge_config.adapter == AdapterType.OPENSPEC
        assert "specification" in bridge_config.artifacts
        assert "project_context" in bridge_config.artifacts
        assert "change_proposal" in bridge_config.artifacts

    def test_import_artifact_specification(self, openspec_adapter: OpenSpecAdapter, openspec_repo: Path) -> None:
        """Test importing specification artifact."""

        from specfact_cli.models.plan import Product
        from specfact_cli.models.project import BundleManifest, BundleVersions, ProjectBundle

        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=[], releases=[])
        project_bundle = ProjectBundle(manifest=manifest, bundle_name="test", product=product, features={})
        spec_path = openspec_repo / "openspec" / "specs" / "001-auth" / "spec.md"

        bridge_config = BridgeConfig.preset_openspec()
        openspec_adapter.import_artifact("specification", spec_path, project_bundle, bridge_config)

        assert "001-auth" in project_bundle.features
        feature = project_bundle.features["001-auth"]
        assert feature.title == "Authentication Feature"

    def test_import_artifact_project_context(self, openspec_adapter: OpenSpecAdapter, openspec_repo: Path) -> None:
        """Test importing project context artifact."""
        from specfact_cli.models.plan import Product
        from specfact_cli.models.project import BundleManifest, BundleVersions, ProjectBundle

        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=[], releases=[])
        project_bundle = ProjectBundle(manifest=manifest, bundle_name="test", product=product, features={})
        project_path = openspec_repo / "openspec" / "project.md"

        bridge_config = BridgeConfig.preset_openspec()
        openspec_adapter.import_artifact("project_context", project_path, project_bundle, bridge_config)

        assert project_bundle.idea is not None
        assert "Test project" in project_bundle.idea.narrative or "OpenSpec integration" in str(
            project_bundle.idea.narrative
        )

    def test_import_artifact_change_proposal(self, openspec_adapter: OpenSpecAdapter, openspec_repo: Path) -> None:
        """Test importing change proposal artifact."""
        from specfact_cli.models.plan import Product
        from specfact_cli.models.project import BundleManifest, BundleVersions, ProjectBundle

        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=[], releases=[])
        project_bundle = ProjectBundle(manifest=manifest, bundle_name="test", product=product, features={})
        proposal_path = openspec_repo / "openspec" / "changes" / "add-feature-x" / "proposal.md"

        bridge_config = BridgeConfig.preset_openspec()
        openspec_adapter.import_artifact("change_proposal", proposal_path, project_bundle, bridge_config)

        # Change proposals are tracked separately, not in features
        # Verify no errors occurred
        assert project_bundle.features is not None

    def test_export_artifact_raises_not_implemented(self, openspec_adapter: OpenSpecAdapter, tmp_path: Path) -> None:
        """Test that export_artifact raises NotImplementedError (Phase 1)."""
        bridge_config = BridgeConfig.preset_openspec()
        feature_mock = MagicMock()

        with pytest.raises(NotImplementedError, match=r"Phase 1.*read-only"):
            openspec_adapter.export_artifact("specification", feature_mock, bridge_config)

    def test_load_change_tracking(self, openspec_adapter: OpenSpecAdapter, openspec_repo: Path) -> None:
        """Test loading change tracking."""
        from specfact_cli.utils.structure import SpecFactStructure

        bridge_config = BridgeConfig.preset_openspec()
        # Create a bundle directory structure
        bundle_dir = openspec_repo / SpecFactStructure.PROJECTS / "test-bundle"
        bundle_dir.mkdir(parents=True)

        change_tracking = openspec_adapter.load_change_tracking(bundle_dir, bridge_config)

        assert change_tracking is not None
        assert len(change_tracking.proposals) >= 1

    def test_save_change_tracking_raises_not_implemented(
        self, openspec_adapter: OpenSpecAdapter, tmp_path: Path
    ) -> None:
        """Test that save_change_tracking raises NotImplementedError (Phase 1)."""
        from specfact_cli.models.change import ChangeTracking

        bridge_config = BridgeConfig.preset_openspec()
        change_tracking = ChangeTracking(proposals={}, feature_deltas={})

        with pytest.raises(NotImplementedError, match=r"Phase 1.*read-only"):
            openspec_adapter.save_change_tracking(tmp_path, change_tracking, bridge_config)

    def test_load_change_proposal(self, openspec_adapter: OpenSpecAdapter, openspec_repo: Path) -> None:
        """Test loading change proposal."""
        from specfact_cli.utils.structure import SpecFactStructure

        bridge_config = BridgeConfig.preset_openspec()
        # Create a bundle directory structure
        bundle_dir = openspec_repo / SpecFactStructure.PROJECTS / "test-bundle"
        bundle_dir.mkdir(parents=True)

        proposal = openspec_adapter.load_change_proposal(bundle_dir, "add-feature-x", bridge_config)

        assert proposal is not None
        assert proposal.name == "add-feature-x"
        assert "Add Feature X" in proposal.title or "Add new feature X" in proposal.description

    def test_save_change_proposal_raises_not_implemented(
        self, openspec_adapter: OpenSpecAdapter, tmp_path: Path
    ) -> None:
        """Test that save_change_proposal raises NotImplementedError (Phase 1)."""
        from datetime import UTC, datetime

        from specfact_cli.models.change import ChangeProposal

        bridge_config = BridgeConfig.preset_openspec()
        proposal = ChangeProposal(
            name="test",
            title="Test proposal",
            description="Test proposal description",
            rationale="Test rationale",
            timeline=None,
            owner=None,
            created_at=datetime.now(UTC).isoformat(),
            applied_at=None,
            archived_at=None,
            status="draft",
            source_tracking=None,
        )

        with pytest.raises(NotImplementedError, match=r"Phase 1.*read-only"):
            openspec_adapter.save_change_proposal(tmp_path, proposal, bridge_config)

    def test_source_tracking_metadata(self, openspec_adapter: OpenSpecAdapter, openspec_repo: Path) -> None:
        """Test that source tracking metadata is properly set."""
        from specfact_cli.models.plan import Product
        from specfact_cli.models.project import BundleManifest, BundleVersions, ProjectBundle

        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=[], releases=[])
        project_bundle = ProjectBundle(manifest=manifest, bundle_name="test", product=product, features={})
        spec_path = openspec_repo / "openspec" / "specs" / "001-auth" / "spec.md"

        bridge_config = BridgeConfig.preset_openspec()
        openspec_adapter.import_artifact("specification", spec_path, project_bundle, bridge_config)

        feature = project_bundle.features["001-auth"]
        assert feature.source_tracking is not None
        assert feature.source_tracking.tool == "openspec"
        assert "openspec/specs/001-auth/spec.md" in str(feature.source_tracking.source_metadata.get("path", ""))

    def test_adapter_registry_registration(self) -> None:
        """Test that OpenSpec adapter is registered in adapter registry."""
        assert AdapterRegistry.is_registered("openspec")

        adapter = AdapterRegistry.get_adapter("openspec")
        assert isinstance(adapter, OpenSpecAdapter)

    def test_cross_repo_path_resolution(self, openspec_adapter: OpenSpecAdapter, tmp_path: Path) -> None:
        """Test cross-repo path resolution."""
        external_path = tmp_path / "external"
        openspec_dir = external_path / "openspec"
        openspec_dir.mkdir(parents=True)
        (openspec_dir / "project.md").write_text("# Project")
        specs_dir = openspec_dir / "specs"
        specs_dir.mkdir()
        feature_dir = specs_dir / "001-auth"
        feature_dir.mkdir()
        (feature_dir / "spec.md").write_text("# Auth Feature")

        bridge_config = BridgeConfig.preset_openspec()
        bridge_config.external_base_path = external_path

        # Should detect using external_base_path
        assert openspec_adapter.detect(tmp_path, bridge_config) is True
