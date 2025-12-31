"""
Unit tests for project bundle data models - Contract-First approach.

Tests for modular project bundle models including BundleManifest,
ProjectBundle, and related models.
"""

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest

from specfact_cli.models.change import ChangeProposal, ChangeTracking, ChangeType, FeatureDelta
from specfact_cli.models.plan import Business, Feature, Idea, Product, Story
from specfact_cli.models.project import (
    BundleFormat,
    BundleManifest,
    BundleVersions,
    FeatureIndex,
    PersonaMapping,
    ProjectBundle,
    _is_schema_v1_1,
)


class TestBundleVersions:
    """Tests for BundleVersions model."""

    def test_default_versions(self):
        """Test default version values."""
        versions = BundleVersions(schema="1.0", project="0.1.0")
        assert versions.schema_version == "1.0"
        assert versions.project == "0.1.0"

    def test_custom_versions(self):
        """Test custom version values."""
        versions = BundleVersions(schema="2.0", project="1.2.3")
        assert versions.schema_version == "2.0"
        assert versions.project == "1.2.3"


class TestBundleManifest:
    """Tests for BundleManifest model."""

    def test_default_manifest(self):
        """Test default manifest creation."""
        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        assert manifest.versions.schema_version == "1.0"
        assert manifest.versions.project == "0.1.0"
        assert manifest.checksums.algorithm == "sha256"
        assert manifest.features == []
        assert manifest.protocols == []

    def test_manifest_with_features(self):
        """Test manifest with feature index."""
        feature_index = FeatureIndex(
            key="FEATURE-001",
            title="Test Feature",
            file="FEATURE-001.yaml",
            status="active",
            stories_count=0,
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
            contract=None,
            checksum=None,
        )
        manifest = BundleManifest(schema_metadata=None, project_metadata=None, features=[feature_index])
        assert len(manifest.features) == 1
        assert manifest.features[0].key == "FEATURE-001"

    def test_manifest_with_personas(self):
        """Test manifest with persona mappings."""
        persona = PersonaMapping(
            owns=["idea", "business", "features.*.stories"],
            exports_to="specs/*/spec.md",
        )
        manifest = BundleManifest(schema_metadata=None, project_metadata=None, personas={"product-owner": persona})
        assert "product-owner" in manifest.personas
        assert manifest.personas["product-owner"].exports_to == "specs/*/spec.md"

    def test_manifest_with_change_tracking_v1_1(self):
        """Test BundleManifest with change tracking (v1.1 schema)."""
        change_tracking = ChangeTracking()
        manifest = BundleManifest(
            schema_metadata=None,
            project_metadata=None,
            versions=BundleVersions(schema="1.1", project="0.1.0"),
            change_tracking=change_tracking,
        )
        assert manifest.change_tracking is not None
        assert manifest.change_archive == []

    def test_manifest_backward_compatibility_v1_0(self):
        """Test BundleManifest backward compatibility (v1.0 schema)."""
        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        # v1.0 bundles should have None/empty change tracking
        assert manifest.change_tracking is None
        assert manifest.change_archive == []


class TestProjectBundle:
    """Tests for ProjectBundle class."""

    def test_create_project_bundle(self):
        """Test creating a ProjectBundle instance."""
        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)
        assert bundle.bundle_name == "test-bundle"
        assert bundle.product == product
        assert bundle.features == {}

    def test_add_feature(self):
        """Test adding a feature to bundle."""
        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)

        feature = Feature(key="FEATURE-001", title="Test Feature", source_tracking=None, contract=None, protocol=None)
        bundle.add_feature(feature)

        assert "FEATURE-001" in bundle.features
        assert bundle.features["FEATURE-001"].title == "Test Feature"

    def test_update_feature(self):
        """Test updating a feature in bundle."""
        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)

        feature1 = Feature(
            key="FEATURE-001", title="Original Title", source_tracking=None, contract=None, protocol=None
        )
        bundle.add_feature(feature1)

        feature2 = Feature(key="FEATURE-001", title="Updated Title", source_tracking=None, contract=None, protocol=None)
        bundle.update_feature("FEATURE-001", feature2)

        assert bundle.features["FEATURE-001"].title == "Updated Title"

    def test_update_feature_key_mismatch(self):
        """Test updating feature with mismatched key raises error."""
        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)

        feature = Feature(key="FEATURE-001", title="Test", source_tracking=None, contract=None, protocol=None)
        bundle.add_feature(feature)

        feature2 = Feature(key="FEATURE-002", title="Test", source_tracking=None, contract=None, protocol=None)
        with pytest.raises(ValueError, match="Feature key mismatch"):
            bundle.update_feature("FEATURE-001", feature2)

    def test_get_feature(self):
        """Test getting a feature by key."""
        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)

        feature = Feature(key="FEATURE-001", title="Test Feature", source_tracking=None, contract=None, protocol=None)
        bundle.add_feature(feature)

        retrieved = bundle.get_feature("FEATURE-001")
        assert retrieved is not None
        assert retrieved.title == "Test Feature"

        assert bundle.get_feature("FEATURE-999") is None

    def test_compute_summary(self):
        """Test computing summary from bundle."""
        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product(themes=["Theme1", "Theme2"])
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)

        feature1 = Feature(
            key="FEATURE-001",
            title="Feature 1",
            stories=[
                Story(
                    key="STORY-001",
                    title="Story 1",
                    story_points=None,
                    value_points=None,
                    scenarios=None,
                    contracts=None,
                )
            ],
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        feature2 = Feature(
            key="FEATURE-002",
            title="Feature 2",
            stories=[
                Story(
                    key="STORY-002",
                    title="Story 2",
                    story_points=None,
                    value_points=None,
                    scenarios=None,
                    contracts=None,
                )
            ],
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        bundle.add_feature(feature1)
        bundle.add_feature(feature2)

        summary = bundle.compute_summary(include_hash=False)
        assert summary.features_count == 2
        assert summary.stories_count == 2
        assert summary.themes_count == 2
        assert summary.content_hash is None

    def test_compute_summary_with_hash(self):
        """Test computing summary with content hash."""
        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)

        feature = Feature(key="FEATURE-001", title="Test", source_tracking=None, contract=None, protocol=None)
        bundle.add_feature(feature)

        summary = bundle.compute_summary(include_hash=True)
        assert summary.content_hash is not None
        assert len(summary.content_hash) == 64  # SHA256 hex digest

    def test_load_from_directory(self, tmp_path: Path):
        """Test loading project bundle from directory."""
        # Create directory structure
        bundle_dir = tmp_path / "test-bundle"
        bundle_dir.mkdir()

        # Create manifest
        manifest_data = {
            "versions": {"schema": "1.0", "project": "0.1.0"},
            "bundle": {"format": "directory-based", "created_at": datetime.now(UTC).isoformat()},
            "checksums": {"algorithm": "sha256", "files": {}},
            "features": [],
            "protocols": [],
        }
        import yaml

        (bundle_dir / "bundle.manifest.yaml").write_text(yaml.dump(manifest_data))

        # Create product file
        product_data = {"themes": [], "releases": []}
        (bundle_dir / "product.yaml").write_text(yaml.dump(product_data))

        # Load bundle
        bundle = ProjectBundle.load_from_directory(bundle_dir)
        assert bundle.bundle_name == "test-bundle"
        assert bundle.product is not None

    def test_load_from_directory_missing_manifest(self, tmp_path: Path):
        """Test loading from directory without manifest raises error."""
        bundle_dir = tmp_path / "test-bundle"
        bundle_dir.mkdir()

        with pytest.raises(FileNotFoundError, match="Bundle manifest not found"):
            ProjectBundle.load_from_directory(bundle_dir)

    def test_load_from_directory_missing_product(self, tmp_path: Path):
        """Test loading from directory without product raises error."""
        bundle_dir = tmp_path / "test-bundle"
        bundle_dir.mkdir()

        # Create manifest but no product
        manifest_data = {
            "versions": {"schema": "1.0", "project": "0.1.0"},
            "bundle": {},
            "checksums": {"algorithm": "sha256", "files": {}},
        }
        import yaml

        (bundle_dir / "bundle.manifest.yaml").write_text(yaml.dump(manifest_data))

        with pytest.raises(FileNotFoundError, match="Product file not found"):
            ProjectBundle.load_from_directory(bundle_dir)

    def test_save_to_directory(self, tmp_path: Path):
        """Test saving project bundle to directory."""
        bundle_dir = tmp_path / "test-bundle"

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product(themes=["Theme1"])
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)

        feature = Feature(key="FEATURE-001", title="Test Feature", source_tracking=None, contract=None, protocol=None)
        bundle.add_feature(feature)

        bundle.save_to_directory(bundle_dir)

        # Verify files created
        assert (bundle_dir / "bundle.manifest.yaml").exists()
        assert (bundle_dir / "product.yaml").exists()
        assert (bundle_dir / "features" / "FEATURE-001.yaml").exists()
        assert (bundle_dir / "features").exists()

    def test_save_to_directory_with_optional_aspects(self, tmp_path: Path):
        """Test saving bundle with optional aspects (idea, business, clarifications)."""
        bundle_dir = tmp_path / "test-bundle"

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        idea = Idea(title="Test Idea", narrative="Test narrative", metrics=None)
        business = Business(segments=["Segment1"])
        bundle = ProjectBundle(
            manifest=manifest, bundle_name="test-bundle", product=product, idea=idea, business=business
        )

        bundle.save_to_directory(bundle_dir)

        # Verify optional files created
        assert (bundle_dir / "idea.yaml").exists()
        assert (bundle_dir / "business.yaml").exists()

    def test_save_and_load_roundtrip(self, tmp_path: Path):
        """Test saving and loading bundle maintains data integrity."""
        bundle_dir = tmp_path / "test-bundle"

        # Create and save bundle
        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product(themes=["Theme1"])
        idea = Idea(title="Test Idea", narrative="Test narrative", metrics=None)
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product, idea=idea)

        feature = Feature(
            key="FEATURE-001",
            title="Test Feature",
            stories=[
                Story(
                    key="STORY-001",
                    title="Story 1",
                    story_points=None,
                    value_points=None,
                    scenarios=None,
                    contracts=None,
                )
            ],
            source_tracking=None,
            contract=None,
            protocol=None,
        )
        bundle.add_feature(feature)

        bundle.save_to_directory(bundle_dir)

        # Load bundle
        loaded = ProjectBundle.load_from_directory(bundle_dir)

        # Verify data integrity
        assert loaded.bundle_name == "test-bundle"
        assert loaded.product.themes == ["Theme1"]
        assert loaded.idea is not None
        assert loaded.idea.title == "Test Idea"
        assert "FEATURE-001" in loaded.features
        assert len(loaded.features["FEATURE-001"].stories) == 1

    def test_compute_file_checksum(self, tmp_path: Path):
        """Test file checksum computation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        checksum = ProjectBundle._compute_file_checksum(test_file)

        # Verify it's a SHA256 hex digest
        assert len(checksum) == 64
        assert all(c in "0123456789abcdef" for c in checksum)

        # Verify it matches expected hash
        expected = hashlib.sha256(b"test content").hexdigest()
        assert checksum == expected


class TestBundleFormat:
    """Tests for BundleFormat enum."""

    def test_format_values(self):
        """Test BundleFormat enum values."""
        assert BundleFormat.MONOLITHIC == "monolithic"
        assert BundleFormat.MODULAR == "modular"
        assert BundleFormat.UNKNOWN == "unknown"


class TestProjectBundleChangeTracking:
    """Tests for ProjectBundle change tracking extensions."""

    def test_project_bundle_with_change_tracking(self):
        """Test ProjectBundle with change tracking."""
        manifest = BundleManifest(
            schema_metadata=None,
            project_metadata=None,
            versions=BundleVersions(schema="1.1", project="0.1.0"),
        )
        product = Product()
        change_tracking = ChangeTracking()
        bundle = ProjectBundle(
            manifest=manifest, bundle_name="test-bundle", product=product, change_tracking=change_tracking
        )
        assert bundle.change_tracking is not None

    def test_get_active_changes(self):
        """Test get_active_changes() helper method."""
        manifest = BundleManifest(
            schema_metadata=None,
            project_metadata=None,
            versions=BundleVersions(schema="1.1", project="0.1.0"),
        )
        product = Product()
        change_tracking = ChangeTracking()
        proposal1 = ChangeProposal(
            name="add-feature-1",
            title="Add Feature 1",
            description="Add first feature",
            rationale="Needed for MVP",
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
            name="add-feature-2",
            title="Add Feature 2",
            description="Add second feature",
            rationale="Needed for MVP",
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
        proposal3 = ChangeProposal(
            name="add-feature-3",
            title="Add Feature 3",
            description="Add third feature",
            rationale="Needed for MVP",
            timeline=None,
            owner=None,
            stakeholders=[],
            dependencies=[],
            status="applied",
            created_at=datetime.now(UTC).isoformat(),
            applied_at=datetime.now(UTC).isoformat(),
            archived_at=None,
            source_tracking=None,
        )
        change_tracking.proposals = {
            "add-feature-1": proposal1,
            "add-feature-2": proposal2,
            "add-feature-3": proposal3,
        }
        bundle = ProjectBundle(
            manifest=manifest, bundle_name="test-bundle", product=product, change_tracking=change_tracking
        )

        active_changes = bundle.get_active_changes()
        assert len(active_changes) == 2
        assert proposal1 in active_changes
        assert proposal2 in active_changes
        assert proposal3 not in active_changes

    def test_get_active_changes_empty(self):
        """Test get_active_changes() when no active changes."""
        manifest = BundleManifest(
            schema_metadata=None,
            project_metadata=None,
            versions=BundleVersions(schema="1.1", project="0.1.0"),
        )
        product = Product()
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)
        # No change_tracking set
        assert bundle.get_active_changes() == []

    def test_get_feature_deltas(self):
        """Test get_feature_deltas() helper method."""
        manifest = BundleManifest(
            schema_metadata=None,
            project_metadata=None,
            versions=BundleVersions(schema="1.1", project="0.1.0"),
        )
        product = Product()
        change_tracking = ChangeTracking()
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
        change_tracking.feature_deltas = {"add-feature-1": [delta]}
        bundle = ProjectBundle(
            manifest=manifest, bundle_name="test-bundle", product=product, change_tracking=change_tracking
        )

        deltas = bundle.get_feature_deltas("add-feature-1")
        assert len(deltas) == 1
        assert deltas[0].feature_key == "FEATURE-001"

    def test_get_feature_deltas_not_found(self):
        """Test get_feature_deltas() when change not found."""
        manifest = BundleManifest(
            schema_metadata=None,
            project_metadata=None,
            versions=BundleVersions(schema="1.1", project="0.1.0"),
        )
        product = Product()
        change_tracking = ChangeTracking()
        bundle = ProjectBundle(
            manifest=manifest, bundle_name="test-bundle", product=product, change_tracking=change_tracking
        )

        deltas = bundle.get_feature_deltas("non-existent-change")
        assert deltas == []

    def test_get_feature_deltas_no_change_tracking(self):
        """Test get_feature_deltas() when change_tracking is None."""
        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)
        # No change_tracking set
        assert bundle.get_feature_deltas("any-change") == []


class TestSchemaVersionCheck:
    """Tests for schema version check utility."""

    def test_is_schema_v1_1_true(self):
        """Test _is_schema_v1_1 returns True for v1.1."""
        manifest = BundleManifest(
            schema_metadata=None,
            project_metadata=None,
            versions=BundleVersions(schema="1.1", project="0.1.0"),
        )
        assert _is_schema_v1_1(manifest) is True

    def test_is_schema_v1_1_false(self):
        """Test _is_schema_v1_1 returns False for v1.0."""
        manifest = BundleManifest(
            schema_metadata=None,
            project_metadata=None,
            versions=BundleVersions(schema="1.0", project="0.1.0"),
        )
        assert _is_schema_v1_1(manifest) is False

    def test_is_schema_v1_1_invalid_manifest(self):
        """Test _is_schema_v1_1 handles invalid manifest gracefully."""
        # Create manifest without versions (shouldn't happen in practice, but test defensive code)
        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        # Should still work because default versions are set
        assert _is_schema_v1_1(manifest) is False  # Default is 1.0
