"""
Unit tests for bundle loader phases 2.2 and 2.3 - Contract-First approach.

Tests for load_project_bundle and save_project_bundle functions.
"""

from pathlib import Path

import pytest
import yaml

from specfact_cli.models.plan import Business, Feature, Idea, Product
from specfact_cli.models.project import BundleManifest, BundleVersions, ProjectBundle
from specfact_cli.utils.bundle_loader import (
    BundleFormatError,
    BundleLoadError,
    load_project_bundle,
    save_project_bundle,
)


class TestLoadProjectBundle:
    """Tests for load_project_bundle function."""

    def test_load_modular_bundle(self, tmp_path: Path):
        """Test loading modular bundle successfully."""
        bundle_dir = tmp_path / "test-bundle"
        bundle_dir.mkdir()

        # Create manifest
        manifest_data = {
            "versions": {"schema": "1.0", "project": "0.1.0"},
            "bundle": {"format": "directory-based"},
            "checksums": {"algorithm": "sha256", "files": {}},
            "features": [],
            "protocols": [],
        }
        (bundle_dir / "bundle.manifest.yaml").write_text(yaml.dump(manifest_data))

        # Create product file
        product_data = {"themes": [], "releases": []}
        (bundle_dir / "product.yaml").write_text(yaml.dump(product_data))

        # Load bundle
        bundle = load_project_bundle(bundle_dir)

        assert isinstance(bundle, ProjectBundle)
        assert bundle.bundle_name == "test-bundle"
        assert bundle.product is not None

    def test_load_bundle_with_optional_aspects(self, tmp_path: Path):
        """Test loading bundle with optional aspects (idea, business)."""
        bundle_dir = tmp_path / "test-bundle"
        bundle_dir.mkdir()

        # Create manifest
        manifest_data = {
            "versions": {"schema": "1.0", "project": "0.1.0"},
            "bundle": {},
            "checksums": {"algorithm": "sha256", "files": {}},
            "features": [],
        }
        (bundle_dir / "bundle.manifest.yaml").write_text(yaml.dump(manifest_data))

        # Create required product file
        product_data = {"themes": []}
        (bundle_dir / "product.yaml").write_text(yaml.dump(product_data))

        # Create optional idea file
        idea_data = {"title": "Test Idea", "narrative": "Test narrative"}
        (bundle_dir / "idea.yaml").write_text(yaml.dump(idea_data))

        # Create optional business file
        business_data = {"segments": ["Segment1"]}
        (bundle_dir / "business.yaml").write_text(yaml.dump(business_data))

        # Load bundle
        bundle = load_project_bundle(bundle_dir)

        assert bundle.idea is not None
        assert bundle.idea.title == "Test Idea"
        assert bundle.business is not None
        assert bundle.business.segments == ["Segment1"]

    def test_load_bundle_with_features(self, tmp_path: Path):
        """Test loading bundle with features."""
        bundle_dir = tmp_path / "test-bundle"
        bundle_dir.mkdir()
        features_dir = bundle_dir / "features"
        features_dir.mkdir()

        # Create manifest with feature index
        manifest_data = {
            "versions": {"schema": "1.0", "project": "0.1.0"},
            "bundle": {},
            "checksums": {"algorithm": "sha256", "files": {}},
            "features": [
                {
                    "key": "FEATURE-001",
                    "title": "Test Feature",
                    "file": "FEATURE-001.yaml",
                    "status": "active",
                    "stories_count": 0,
                    "created_at": "2025-11-25T00:00:00Z",
                    "updated_at": "2025-11-25T00:00:00Z",
                }
            ],
        }
        (bundle_dir / "bundle.manifest.yaml").write_text(yaml.dump(manifest_data))

        # Create product file
        product_data = {"themes": []}
        (bundle_dir / "product.yaml").write_text(yaml.dump(product_data))

        # Create feature file
        feature_data = {"key": "FEATURE-001", "title": "Test Feature"}
        (features_dir / "FEATURE-001.yaml").write_text(yaml.dump(feature_data))

        # Load bundle
        bundle = load_project_bundle(bundle_dir)

        assert "FEATURE-001" in bundle.features
        assert bundle.features["FEATURE-001"].title == "Test Feature"

    def test_load_bundle_missing_manifest_raises_error(self, tmp_path: Path):
        """Test that missing manifest raises format error."""
        bundle_dir = tmp_path / "test-bundle"
        bundle_dir.mkdir()

        # Empty directory will fail format validation first
        with pytest.raises(BundleFormatError) as exc_info:
            load_project_bundle(bundle_dir)

        assert "Cannot determine bundle format" in str(exc_info.value)

    def test_load_bundle_missing_product_raises_error(self, tmp_path: Path):
        """Test that missing product file raises error."""
        bundle_dir = tmp_path / "test-bundle"
        bundle_dir.mkdir()

        # Create manifest but no product
        manifest_data = {
            "versions": {"schema": "1.0", "project": "0.1.0"},
            "bundle": {},
            "checksums": {"algorithm": "sha256", "files": {}},
        }
        (bundle_dir / "bundle.manifest.yaml").write_text(yaml.dump(manifest_data))

        with pytest.raises(BundleLoadError) as exc_info:
            load_project_bundle(bundle_dir)

        assert "not found" in str(exc_info.value).lower()

    def test_load_bundle_invalid_format_raises_error(self, tmp_path: Path):
        """Test that non-modular format raises error."""
        # Create a file that looks like monolithic bundle
        bundle_file = tmp_path / "test.bundle.yaml"
        bundle_data = {
            "idea": {"title": "Test"},
            "product": {"themes": []},
            "features": [],
        }
        bundle_file.write_text(yaml.dump(bundle_data))

        with pytest.raises(BundleFormatError):
            load_project_bundle(bundle_file)


class TestSaveProjectBundle:
    """Tests for save_project_bundle function."""

    def test_save_bundle_atomic(self, tmp_path: Path):
        """Test saving bundle with atomic writes."""
        bundle_dir = tmp_path / "test-bundle"

        # Create bundle
        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=["Theme1"])
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)

        # Save bundle
        save_project_bundle(bundle, bundle_dir, atomic=True)

        # Verify files created
        assert (bundle_dir / "bundle.manifest.yaml").exists()
        assert (bundle_dir / "product.yaml").exists()

    def test_save_bundle_non_atomic(self, tmp_path: Path):
        """Test saving bundle without atomic writes."""
        bundle_dir = tmp_path / "test-bundle"

        # Create bundle
        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=["Theme1"])
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)

        # Save bundle
        save_project_bundle(bundle, bundle_dir, atomic=False)

        # Verify files created
        assert (bundle_dir / "bundle.manifest.yaml").exists()
        assert (bundle_dir / "product.yaml").exists()

    def test_save_bundle_with_features(self, tmp_path: Path):
        """Test saving bundle with features."""
        bundle_dir = tmp_path / "test-bundle"

        # Create bundle with feature
        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=[])
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)

        feature = Feature(key="FEATURE-001", title="Test Feature")
        bundle.add_feature(feature)

        # Save bundle
        save_project_bundle(bundle, bundle_dir)

        # Verify feature file created
        assert (bundle_dir / "features" / "FEATURE-001.yaml").exists()

    def test_save_bundle_with_optional_aspects(self, tmp_path: Path):
        """Test saving bundle with optional aspects."""
        bundle_dir = tmp_path / "test-bundle"

        # Create bundle with optional aspects
        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=[])
        idea = Idea(title="Test Idea", narrative="Test narrative", metrics=None)
        business = Business(segments=["Segment1"])
        bundle = ProjectBundle(
            manifest=manifest, bundle_name="test-bundle", product=product, idea=idea, business=business
        )

        # Save bundle
        save_project_bundle(bundle, bundle_dir)

        # Verify optional files created
        assert (bundle_dir / "idea.yaml").exists()
        assert (bundle_dir / "business.yaml").exists()

    def test_save_bundle_updates_checksums(self, tmp_path: Path):
        """Test that saving bundle updates checksums in manifest."""
        bundle_dir = tmp_path / "test-bundle"

        # Create bundle
        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=["Theme1"])
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)

        # Save bundle
        save_project_bundle(bundle, bundle_dir)

        # Reload and check checksums
        loaded = load_project_bundle(bundle_dir)
        assert "product.yaml" in loaded.manifest.checksums.files
        assert len(loaded.manifest.checksums.files["product.yaml"]) == 64  # SHA256 hex digest


class TestLoadSaveRoundtrip:
    """Tests for load/save roundtrip operations."""

    def test_roundtrip_basic_bundle(self, tmp_path: Path):
        """Test saving and loading bundle maintains data integrity."""
        bundle_dir = tmp_path / "test-bundle"

        # Create and save bundle
        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=["Theme1", "Theme2"])
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)

        save_project_bundle(bundle, bundle_dir)

        # Load bundle
        loaded = load_project_bundle(bundle_dir)

        # Verify data integrity
        assert loaded.bundle_name == "test-bundle"
        assert loaded.product.themes == ["Theme1", "Theme2"]

    def test_roundtrip_with_features(self, tmp_path: Path):
        """Test roundtrip with features."""
        bundle_dir = tmp_path / "test-bundle"

        # Create and save bundle with features
        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=[])
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)

        feature1 = Feature(key="FEATURE-001", title="Feature 1")
        feature2 = Feature(key="FEATURE-002", title="Feature 2")
        bundle.add_feature(feature1)
        bundle.add_feature(feature2)

        save_project_bundle(bundle, bundle_dir)

        # Load bundle
        loaded = load_project_bundle(bundle_dir)

        # Verify features
        assert len(loaded.features) == 2
        assert "FEATURE-001" in loaded.features
        assert "FEATURE-002" in loaded.features
        assert loaded.features["FEATURE-001"].title == "Feature 1"
        assert loaded.features["FEATURE-002"].title == "Feature 2"


class TestHashValidation:
    """Tests for hash validation functionality."""

    def test_load_with_hash_validation_success(self, tmp_path: Path):
        """Test loading bundle with hash validation when hashes match."""
        bundle_dir = tmp_path / "test-bundle"

        # Create and save bundle
        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=["Theme1"])
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)

        save_project_bundle(bundle, bundle_dir)

        # Load with hash validation (should succeed)
        loaded = load_project_bundle(bundle_dir, validate_hashes=True)

        assert loaded.bundle_name == "test-bundle"

    def test_load_with_hash_validation_failure(self, tmp_path: Path):
        """Test loading bundle with hash validation fails when file is modified."""
        bundle_dir = tmp_path / "test-bundle"

        # Create and save bundle
        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=["Theme1"])
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)

        save_project_bundle(bundle, bundle_dir)

        # Modify product file (corrupt it)
        product_file = bundle_dir / "product.yaml"
        product_file.write_text("corrupted: data")

        # Load with hash validation (should fail)
        with pytest.raises(BundleLoadError) as exc_info:
            load_project_bundle(bundle_dir, validate_hashes=True)

        assert "Hash validation failed" in str(exc_info.value)
        assert "Hash mismatch" in str(exc_info.value)
