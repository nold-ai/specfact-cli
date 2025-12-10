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


class TestBundleSpecificPaths:
    """Tests for bundle-specific artifact paths (Phase 8.5)."""

    def test_get_bundle_reports_dir(self, tmp_path: Path):
        """Test get_bundle_reports_dir returns correct path."""
        reports_dir = SpecFactStructure.get_bundle_reports_dir("test-bundle", base_path=tmp_path)
        assert reports_dir == tmp_path / ".specfact/projects/test-bundle/reports"

    def test_get_bundle_brownfield_report_path(self, tmp_path: Path):
        """Test get_bundle_brownfield_report_path creates timestamped path."""
        report_path = SpecFactStructure.get_bundle_brownfield_report_path("test-bundle", base_path=tmp_path)
        assert report_path.parent == tmp_path / ".specfact/projects/test-bundle/reports/brownfield"
        assert report_path.name.startswith("analysis-")
        assert report_path.suffix == ".md"

    def test_get_bundle_comparison_report_path(self, tmp_path: Path):
        """Test get_bundle_comparison_report_path creates timestamped path."""
        report_path = SpecFactStructure.get_bundle_comparison_report_path(
            "test-bundle", base_path=tmp_path, format="md"
        )
        assert report_path.parent == tmp_path / ".specfact/projects/test-bundle/reports/comparison"
        assert report_path.name.startswith("report-")
        assert report_path.suffix == ".md"

    def test_get_bundle_enrichment_report_path(self, tmp_path: Path):
        """Test get_bundle_enrichment_report_path creates timestamped path."""
        report_path = SpecFactStructure.get_bundle_enrichment_report_path("test-bundle", base_path=tmp_path)
        assert report_path.parent == tmp_path / ".specfact/projects/test-bundle/reports/enrichment"
        assert "test-bundle" in report_path.name
        assert report_path.name.endswith(".enrichment.md")

    def test_get_bundle_enforcement_report_path(self, tmp_path: Path):
        """Test get_bundle_enforcement_report_path creates timestamped path."""
        report_path = SpecFactStructure.get_bundle_enforcement_report_path("test-bundle", base_path=tmp_path)
        assert report_path.parent == tmp_path / ".specfact/projects/test-bundle/reports/enforcement"
        assert report_path.name.startswith("report-")
        assert report_path.suffix == ".yaml"

    def test_get_bundle_sdd_path(self, tmp_path: Path):
        """Test get_bundle_sdd_path returns correct path."""
        from specfact_cli.utils.structured_io import StructuredFormat

        sdd_path = SpecFactStructure.get_bundle_sdd_path(
            "test-bundle", base_path=tmp_path, format=StructuredFormat.YAML
        )
        assert sdd_path == tmp_path / ".specfact/projects/test-bundle/sdd.yaml"

        sdd_path_json = SpecFactStructure.get_bundle_sdd_path(
            "test-bundle", base_path=tmp_path, format=StructuredFormat.JSON
        )
        assert sdd_path_json == tmp_path / ".specfact/projects/test-bundle/sdd.json"

    def test_get_bundle_tasks_path(self, tmp_path: Path):
        """Test get_bundle_tasks_path returns correct path."""
        tasks_path = SpecFactStructure.get_bundle_tasks_path("test-bundle", base_path=tmp_path)
        assert tasks_path == tmp_path / ".specfact/projects/test-bundle/tasks.yaml"

    def test_get_bundle_logs_dir(self, tmp_path: Path):
        """Test get_bundle_logs_dir creates and returns correct path."""
        logs_dir = SpecFactStructure.get_bundle_logs_dir("test-bundle", base_path=tmp_path)
        assert logs_dir == tmp_path / ".specfact/projects/test-bundle/logs"
        assert logs_dir.exists(), "Logs directory should be created"

    def test_ensure_project_structure_creates_bundle_specific_dirs(self, tmp_path: Path):
        """Test ensure_project_structure creates bundle-specific directories (Phase 8.5)."""
        SpecFactStructure.ensure_project_structure(base_path=tmp_path, bundle_name="test-bundle")

        project_dir = tmp_path / ".specfact/projects/test-bundle"
        assert (project_dir / "reports" / "brownfield").exists()
        assert (project_dir / "reports" / "comparison").exists()
        assert (project_dir / "reports" / "enrichment").exists()
        assert (project_dir / "reports" / "enforcement").exists()
        assert (project_dir / "logs").exists()
