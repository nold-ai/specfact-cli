"""
Unit tests for bundle loader utilities - Contract-First approach.

Tests for format detection, validation, and bundle type checking.
"""

from pathlib import Path

import pytest
import yaml

from specfact_cli.models.project import BundleFormat
from specfact_cli.utils.bundle_loader import (
    BundleFormatError,
    detect_bundle_format,
    is_modular_bundle,
    is_monolithic_bundle,
    validate_bundle_format,
)


class TestDetectBundleFormat:
    """Tests for detect_bundle_format function."""

    def test_detect_monolithic_bundle_file(self, tmp_path: Path):
        """Test detecting monolithic bundle from file."""
        bundle_file = tmp_path / "test.bundle.yaml"
        bundle_data = {
            "idea": {"title": "Test Idea"},
            "product": {"themes": []},
            "features": [{"key": "FEATURE-001", "title": "Test"}],
        }
        bundle_file.write_text(yaml.dump(bundle_data))

        format_type, error = detect_bundle_format(bundle_file)
        assert format_type == BundleFormat.MONOLITHIC
        assert error is None

    def test_detect_modular_bundle_directory(self, tmp_path: Path):
        """Test detecting modular bundle from directory."""
        bundle_dir = tmp_path / "test-bundle"
        bundle_dir.mkdir()
        manifest_file = bundle_dir / "bundle.manifest.yaml"
        manifest_data = {
            "versions": {"schema": "1.0", "project": "0.1.0"},
            "bundle": {"format": "directory-based"},
        }
        manifest_file.write_text(yaml.dump(manifest_data))

        format_type, error = detect_bundle_format(bundle_dir)
        assert format_type == BundleFormat.MODULAR
        assert error is None

    def test_detect_modular_bundle_manifest_file(self, tmp_path: Path):
        """Test detecting modular bundle from manifest file."""
        manifest_file = tmp_path / "bundle.manifest.yaml"
        manifest_data = {
            "versions": {"schema": "1.0", "project": "0.1.0"},
            "bundle": {"format": "directory-based"},
        }
        manifest_file.write_text(yaml.dump(manifest_data))

        format_type, error = detect_bundle_format(manifest_file)
        assert format_type == BundleFormat.MODULAR
        assert error is None

    def test_detect_legacy_plans_directory(self, tmp_path: Path):
        """Test detecting legacy plans directory as monolithic."""
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        bundle_file = plans_dir / "main.bundle.yaml"
        bundle_file.write_text(yaml.dump({"idea": {}, "product": {}, "features": []}))

        format_type, error = detect_bundle_format(plans_dir)
        assert format_type == BundleFormat.MONOLITHIC
        assert error is None

    def test_detect_unknown_file(self, tmp_path: Path):
        """Test detecting unknown format from invalid file."""
        unknown_file = tmp_path / "unknown.txt"
        unknown_file.write_text("not a bundle")

        format_type, error = detect_bundle_format(unknown_file)
        assert format_type == BundleFormat.UNKNOWN
        assert error is not None

    def test_detect_unknown_directory(self, tmp_path: Path):
        """Test detecting unknown format from empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        format_type, error = detect_bundle_format(empty_dir)
        assert format_type == BundleFormat.UNKNOWN
        assert error is not None

    def test_detect_nonexistent_path(self, tmp_path: Path):
        """Test detecting format from nonexistent path."""
        nonexistent = tmp_path / "nonexistent.yaml"

        format_type, error = detect_bundle_format(nonexistent)
        assert format_type == BundleFormat.UNKNOWN
        assert error is not None
        if error:
            assert "does not exist" in error

    def test_detect_invalid_yaml_file(self, tmp_path: Path):
        """Test detecting format from invalid YAML file."""
        invalid_file = tmp_path / "invalid.yaml"
        invalid_file.write_text("invalid: yaml: content: [unclosed")

        format_type, error = detect_bundle_format(invalid_file)
        assert format_type == BundleFormat.UNKNOWN
        assert error is not None
        assert "Failed to parse" in error


class TestValidateBundleFormat:
    """Tests for validate_bundle_format function."""

    def test_validate_monolithic_bundle(self, tmp_path: Path):
        """Test validating monolithic bundle."""
        bundle_file = tmp_path / "test.bundle.yaml"
        bundle_data = {
            "idea": {"title": "Test"},
            "product": {"themes": []},
            "features": [],
        }
        bundle_file.write_text(yaml.dump(bundle_data))

        format_type = validate_bundle_format(bundle_file)
        assert format_type == BundleFormat.MONOLITHIC

    def test_validate_modular_bundle(self, tmp_path: Path):
        """Test validating modular bundle."""
        bundle_dir = tmp_path / "test-bundle"
        bundle_dir.mkdir()
        manifest_file = bundle_dir / "bundle.manifest.yaml"
        manifest_data = {
            "versions": {"schema": "1.0", "project": "0.1.0"},
            "bundle": {},
        }
        manifest_file.write_text(yaml.dump(manifest_data))

        format_type = validate_bundle_format(bundle_dir)
        assert format_type == BundleFormat.MODULAR

    def test_validate_unknown_format_raises_error(self, tmp_path: Path):
        """Test that unknown format raises BundleFormatError."""
        unknown_file = tmp_path / "unknown.txt"
        unknown_file.write_text("not a bundle")

        with pytest.raises(BundleFormatError) as exc_info:
            validate_bundle_format(unknown_file)

        assert "Cannot determine bundle format" in str(exc_info.value)
        assert "Supported formats" in str(exc_info.value)

    def test_validate_nonexistent_path_raises_error(self, tmp_path: Path):
        """Test that nonexistent path raises contract violation or FileNotFoundError."""
        from icontract.errors import ViolationError

        nonexistent = tmp_path / "nonexistent.yaml"

        # Note: The contract requires path.exists(), so ViolationError is raised
        # by the contract checker before the function body executes
        with pytest.raises((ViolationError, FileNotFoundError)):
            validate_bundle_format(nonexistent)


class TestIsMonolithicBundle:
    """Tests for is_monolithic_bundle function."""

    def test_is_monolithic_true(self, tmp_path: Path):
        """Test is_monolithic_bundle returns True for monolithic bundle."""
        bundle_file = tmp_path / "test.bundle.yaml"
        bundle_data = {
            "idea": {"title": "Test"},
            "product": {"themes": []},
            "features": [],
        }
        bundle_file.write_text(yaml.dump(bundle_data))

        assert is_monolithic_bundle(bundle_file) is True

    def test_is_monolithic_false(self, tmp_path: Path):
        """Test is_monolithic_bundle returns False for modular bundle."""
        bundle_dir = tmp_path / "test-bundle"
        bundle_dir.mkdir()
        manifest_file = bundle_dir / "bundle.manifest.yaml"
        manifest_data = {"versions": {"schema": "1.0"}, "bundle": {}}
        manifest_file.write_text(yaml.dump(manifest_data))

        assert is_monolithic_bundle(bundle_dir) is False


class TestIsModularBundle:
    """Tests for is_modular_bundle function."""

    def test_is_modular_true(self, tmp_path: Path):
        """Test is_modular_bundle returns True for modular bundle."""
        bundle_dir = tmp_path / "test-bundle"
        bundle_dir.mkdir()
        manifest_file = bundle_dir / "bundle.manifest.yaml"
        manifest_data = {"versions": {"schema": "1.0"}, "bundle": {}}
        manifest_file.write_text(yaml.dump(manifest_data))

        assert is_modular_bundle(bundle_dir) is True

    def test_is_modular_false(self, tmp_path: Path):
        """Test is_modular_bundle returns False for monolithic bundle."""
        bundle_file = tmp_path / "test.bundle.yaml"
        bundle_data = {
            "idea": {"title": "Test"},
            "product": {"themes": []},
            "features": [],
        }
        bundle_file.write_text(yaml.dump(bundle_data))

        assert is_modular_bundle(bundle_file) is False
