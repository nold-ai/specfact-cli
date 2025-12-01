"""
Unit tests for progress display utilities.

Tests for load_bundle_with_progress and save_bundle_with_progress functions.
"""

from pathlib import Path
from unittest.mock import MagicMock

import yaml

from specfact_cli.models.plan import Product
from specfact_cli.models.project import BundleManifest, BundleVersions, ProjectBundle
from specfact_cli.utils.progress import (
    create_progress_callback,
    load_bundle_with_progress,
    save_bundle_with_progress,
)


class TestCreateProgressCallback:
    """Tests for create_progress_callback function."""

    def test_create_callback_with_prefix(self):
        """Test creating callback with prefix."""
        progress = MagicMock()
        task_id = MagicMock()

        callback = create_progress_callback(progress, task_id, prefix="Loading")

        callback(1, 5, "FEATURE-001.yaml")

        progress.update.assert_called_once_with(task_id, description="Loading artifact 1/5: FEATURE-001.yaml")

    def test_create_callback_without_prefix(self):
        """Test creating callback without prefix."""
        progress = MagicMock()
        task_id = MagicMock()

        callback = create_progress_callback(progress, task_id)

        callback(3, 10, "product.yaml")

        progress.update.assert_called_once_with(task_id, description="Processing artifact 3/10: product.yaml")


class TestLoadBundleWithProgress:
    """Tests for load_bundle_with_progress function."""

    def test_load_bundle_with_progress(self, tmp_path: Path):
        """Test loading bundle with progress display."""
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

        # Load bundle with progress
        bundle = load_bundle_with_progress(bundle_dir)

        assert isinstance(bundle, ProjectBundle)
        assert bundle.bundle_name == "test-bundle"
        assert bundle.product is not None

    def test_load_bundle_with_progress_validate_hashes(self, tmp_path: Path):
        """Test loading bundle with progress and hash validation."""
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

        # Load bundle with progress and hash validation
        bundle = load_bundle_with_progress(bundle_dir, validate_hashes=True)

        assert isinstance(bundle, ProjectBundle)
        assert bundle.bundle_name == "test-bundle"

    def test_load_bundle_with_progress_custom_console(self, tmp_path: Path):
        """Test loading bundle with progress using custom console."""
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

        # Create custom console
        custom_console = MagicMock()

        # Load bundle with progress using custom console
        bundle = load_bundle_with_progress(bundle_dir, console_instance=custom_console)

        assert isinstance(bundle, ProjectBundle)
        assert bundle.bundle_name == "test-bundle"


class TestSaveBundleWithProgress:
    """Tests for save_bundle_with_progress function."""

    def test_save_bundle_with_progress(self, tmp_path: Path):
        """Test saving bundle with progress display."""
        bundle_dir = tmp_path / "test-bundle"

        # Create bundle
        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=["Theme1"])
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)

        # Save bundle with progress
        save_bundle_with_progress(bundle, bundle_dir)

        # Verify files created
        assert (bundle_dir / "bundle.manifest.yaml").exists()
        assert (bundle_dir / "product.yaml").exists()

    def test_save_bundle_with_progress_non_atomic(self, tmp_path: Path):
        """Test saving bundle with progress without atomic writes."""
        bundle_dir = tmp_path / "test-bundle"

        # Create bundle
        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=["Theme1"])
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)

        # Save bundle with progress (non-atomic)
        save_bundle_with_progress(bundle, bundle_dir, atomic=False)

        # Verify files created
        assert (bundle_dir / "bundle.manifest.yaml").exists()
        assert (bundle_dir / "product.yaml").exists()

    def test_save_bundle_with_progress_custom_console(self, tmp_path: Path):
        """Test saving bundle with progress using custom console."""
        bundle_dir = tmp_path / "test-bundle"

        # Create bundle
        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=["Theme1"])
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)

        # Create custom console
        custom_console = MagicMock()

        # Save bundle with progress using custom console
        save_bundle_with_progress(bundle, bundle_dir, console_instance=custom_console)

        # Verify files created
        assert (bundle_dir / "bundle.manifest.yaml").exists()
        assert (bundle_dir / "product.yaml").exists()


class TestLoadSaveRoundtripWithProgress:
    """Tests for load/save roundtrip operations with progress."""

    def test_roundtrip_with_progress(self, tmp_path: Path):
        """Test saving and loading bundle with progress maintains data integrity."""
        bundle_dir = tmp_path / "test-bundle"

        # Create and save bundle
        manifest = BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        )
        product = Product(themes=["Theme1", "Theme2"])
        bundle = ProjectBundle(manifest=manifest, bundle_name="test-bundle", product=product)

        save_bundle_with_progress(bundle, bundle_dir)

        # Load bundle with progress
        loaded = load_bundle_with_progress(bundle_dir)

        # Verify data integrity
        assert loaded.bundle_name == "test-bundle"
        assert loaded.product.themes == ["Theme1", "Theme2"]
