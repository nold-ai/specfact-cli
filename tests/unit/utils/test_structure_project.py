"""
Unit tests for project bundle structure utilities.

Tests for project_dir, ensure_project_structure, and detect_bundle_format.
"""

from pathlib import Path

import yaml

from specfact_cli.models.project import BundleFormat
from specfact_cli.utils.structure import SpecFactStructure


class TestProjectDir:
    """Tests for project_dir helper method."""

    def test_project_dir_default_path(self):
        """Test project_dir with default base path."""
        path = SpecFactStructure.project_dir(bundle_name="legacy-api")
        assert path == Path(".specfact/projects/legacy-api")

    def test_project_dir_custom_base_path(self, tmp_path: Path):
        """Test project_dir with custom base path."""
        path = SpecFactStructure.project_dir(base_path=tmp_path, bundle_name="test-bundle")
        assert path == tmp_path / ".specfact/projects/test-bundle"

    def test_project_dir_normalizes_specfact_in_path(self, tmp_path: Path):
        """Test project_dir normalizes when .specfact is in base_path."""
        specfact_path = tmp_path / ".specfact" / "reports"
        path = SpecFactStructure.project_dir(base_path=specfact_path, bundle_name="test-bundle")
        # Should normalize to repository root
        assert path == tmp_path / ".specfact/projects/test-bundle"


class TestEnsureProjectStructure:
    """Tests for ensure_project_structure method."""

    def test_ensure_project_structure_creates_directories(self, tmp_path: Path):
        """Test ensure_project_structure creates required directories."""
        SpecFactStructure.ensure_project_structure(base_path=tmp_path, bundle_name="test-bundle")

        project_dir = tmp_path / ".specfact/projects/test-bundle"
        assert project_dir.exists()
        assert (project_dir / "features").exists()
        assert (project_dir / "protocols").exists()
        assert (project_dir / "contracts").exists()

    def test_ensure_project_structure_idempotent(self, tmp_path: Path):
        """Test ensure_project_structure is idempotent."""
        SpecFactStructure.ensure_project_structure(base_path=tmp_path, bundle_name="test-bundle")
        SpecFactStructure.ensure_project_structure(base_path=tmp_path, bundle_name="test-bundle")

        # Should not raise error on second call
        project_dir = tmp_path / ".specfact/projects/test-bundle"
        assert project_dir.exists()


class TestDetectBundleFormat:
    """Tests for detect_bundle_format function."""

    def test_detect_monolithic_bundle_file(self, tmp_path: Path):
        """Test detecting monolithic bundle from file."""
        plan_file = tmp_path / "plan.bundle.yaml"
        plan_data = {
            "version": "1.0",
            "idea": {"title": "Test", "narrative": "Test narrative"},
            "product": {"themes": []},
            "features": [],
        }
        plan_file.write_text(yaml.dump(plan_data))

        format_type, error = SpecFactStructure.detect_bundle_format(plan_file)
        assert format_type == BundleFormat.MONOLITHIC
        assert error is None

    def test_detect_modular_bundle_directory(self, tmp_path: Path):
        """Test detecting modular bundle from directory."""
        bundle_dir = tmp_path / "test-bundle"
        bundle_dir.mkdir()

        manifest_data = {
            "versions": {"schema": "1.0", "project": "0.1.0"},
            "bundle": {"format": "directory-based"},
        }
        (bundle_dir / "bundle.manifest.yaml").write_text(yaml.dump(manifest_data))

        format_type, error = SpecFactStructure.detect_bundle_format(bundle_dir)
        assert format_type == BundleFormat.MODULAR
        assert error is None

    def test_detect_unknown_format(self, tmp_path: Path):
        """Test detecting unknown format."""
        unknown_file = tmp_path / "unknown.txt"
        unknown_file.write_text("not a bundle")

        format_type, error = SpecFactStructure.detect_bundle_format(unknown_file)
        assert format_type == BundleFormat.UNKNOWN
        assert error is not None

    def test_detect_unknown_directory(self, tmp_path: Path):
        """Test detecting unknown format for empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        format_type, error = SpecFactStructure.detect_bundle_format(empty_dir)
        assert format_type == BundleFormat.UNKNOWN
        assert error is not None

    def test_detect_invalid_yaml_file(self, tmp_path: Path):
        """Test detecting format from invalid YAML file."""
        invalid_file = tmp_path / "invalid.yaml"
        invalid_file.write_text("invalid: yaml: content: [unclosed")

        format_type, error = SpecFactStructure.detect_bundle_format(invalid_file)
        assert format_type == BundleFormat.UNKNOWN
        assert error is not None
        assert "Failed to parse file" in error

    def test_detect_legacy_plans_directory(self, tmp_path: Path):
        """Test detecting monolithic format from legacy plans directory."""
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()

        plan_file = plans_dir / "main.bundle.yaml"
        plan_data = {"version": "1.0", "features": []}
        plan_file.write_text(yaml.dump(plan_data))

        format_type, error = SpecFactStructure.detect_bundle_format(plans_dir)
        assert format_type == BundleFormat.MONOLITHIC
        assert error is None
