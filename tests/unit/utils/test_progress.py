"""
Unit tests for progress display utilities.

Tests for load_bundle_with_progress and save_bundle_with_progress functions.
"""

from pathlib import Path
from unittest.mock import MagicMock

from specfact_cli.models.project import ProjectBundle
from specfact_cli.utils.progress import (
    create_progress_callback,
    load_bundle_with_progress,
    save_bundle_with_progress,
)
from tests.unit.utils.bundle_test_helpers import assert_core_bundle_files, make_test_bundle, write_minimal_bundle_files


class TestCreateProgressCallback:
    """Tests for create_progress_callback function."""

    def test_create_callback_with_prefix(self):
        """Test creating callback with prefix."""
        progress = MagicMock()
        task_id = MagicMock()

        callback = create_progress_callback(progress, task_id, prefix="Loading")

        callback(1, 5, "FEATURE-001.yaml")

        # Callback should be called twice: once to set total, once to set completed and description
        assert progress.update.call_count == 2
        progress.update.assert_any_call(task_id, total=5)
        progress.update.assert_any_call(task_id, completed=1, description="Loading artifact 1/5: FEATURE-001.yaml")

    def test_create_callback_without_prefix(self):
        """Test creating callback without prefix."""
        progress = MagicMock()
        task_id = MagicMock()

        callback = create_progress_callback(progress, task_id)

        callback(3, 10, "product.yaml")

        # Callback should be called twice: once to set total, once to set completed and description
        assert progress.update.call_count == 2
        progress.update.assert_any_call(task_id, total=10)
        progress.update.assert_any_call(task_id, completed=3, description="Processing artifact 3/10: product.yaml")


class TestLoadBundleWithProgress:
    """Tests for load_bundle_with_progress function."""

    def test_load_bundle_with_progress(self, tmp_path: Path):
        """Test loading bundle with progress display."""
        bundle_dir = tmp_path / "test-bundle"
        write_minimal_bundle_files(bundle_dir)

        # Load bundle with progress
        bundle = load_bundle_with_progress(bundle_dir)

        assert isinstance(bundle, ProjectBundle)
        assert bundle.bundle_name == "test-bundle"
        assert bundle.product is not None

    def test_load_bundle_with_progress_validate_hashes(self, tmp_path: Path):
        """Test loading bundle with progress and hash validation."""
        bundle_dir = tmp_path / "test-bundle"
        write_minimal_bundle_files(bundle_dir)

        # Load bundle with progress and hash validation
        bundle = load_bundle_with_progress(bundle_dir, validate_hashes=True)

        assert isinstance(bundle, ProjectBundle)
        assert bundle.bundle_name == "test-bundle"

    def test_load_bundle_with_progress_custom_console(self, tmp_path: Path):
        """Test loading bundle with progress using custom console."""
        bundle_dir = tmp_path / "test-bundle"
        write_minimal_bundle_files(bundle_dir)

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
        bundle = make_test_bundle(themes=["Theme1"])

        # Save bundle with progress
        save_bundle_with_progress(bundle, bundle_dir)

        # Verify files created
        assert_core_bundle_files(bundle_dir)

    def test_save_bundle_with_progress_non_atomic(self, tmp_path: Path):
        """Test saving bundle with progress without atomic writes."""
        bundle_dir = tmp_path / "test-bundle"
        bundle = make_test_bundle(themes=["Theme1"])

        # Save bundle with progress (non-atomic)
        save_bundle_with_progress(bundle, bundle_dir, atomic=False)

        # Verify files created
        assert_core_bundle_files(bundle_dir)

    def test_save_bundle_with_progress_custom_console(self, tmp_path: Path):
        """Test saving bundle with progress using custom console."""
        bundle_dir = tmp_path / "test-bundle"
        bundle = make_test_bundle(themes=["Theme1"])

        # Create custom console
        custom_console = MagicMock()

        # Save bundle with progress using custom console
        save_bundle_with_progress(bundle, bundle_dir, console_instance=custom_console)

        # Verify files created
        assert_core_bundle_files(bundle_dir)


class TestLoadSaveRoundtripWithProgress:
    """Tests for load/save roundtrip operations with progress."""

    def test_roundtrip_with_progress(self, tmp_path: Path):
        """Test saving and loading bundle with progress maintains data integrity."""
        bundle_dir = tmp_path / "test-bundle"
        bundle = make_test_bundle(themes=["Theme1", "Theme2"])

        save_bundle_with_progress(bundle, bundle_dir)

        # Load bundle with progress
        loaded = load_bundle_with_progress(bundle_dir)

        # Verify data integrity
        assert loaded.bundle_name == "test-bundle"
        assert loaded.product.themes == ["Theme1", "Theme2"]
