"""
Unit tests for project bundle data models - Contract-First approach.

Tests for modular project bundle models including BundleManifest,
ProjectBundle, and related models.
"""

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest

from specfact_cli.models.plan import Business, Feature, Idea, Product, Story
from specfact_cli.models.project import (
    BundleFormat,
    BundleManifest,
    BundleVersions,
    FeatureIndex,
    PersonaMapping,
    ProjectBundle,
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
