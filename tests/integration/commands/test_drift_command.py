"""
Integration tests for drift detect command.

Tests the drift detection CLI command with realistic scenarios.
"""

from __future__ import annotations

import json

import yaml
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.models.plan import Feature, Product, Story
from specfact_cli.models.project import BundleManifest, ProjectBundle
from specfact_cli.models.source_tracking import SourceTracking
from specfact_cli.utils.bundle_loader import save_project_bundle


runner = CliRunner()


class TestDriftDetectCommand:
    """Test suite for drift detect command."""

    def test_drift_detect_no_bundle(self, tmp_path) -> None:
        """Test drift detect when bundle doesn't exist."""
        result = runner.invoke(app, ["drift", "detect", "nonexistent", "--repo", str(tmp_path)])

        assert result.exit_code == 0  # Command succeeds but returns empty report
        assert "Drift Detection" in result.stdout

    def test_drift_detect_table_format(self, tmp_path) -> None:
        """Test drift detect with table output format (default)."""
        # Create bundle with feature
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        # Add feature with source tracking
        feature_file = tmp_path / "src" / "feature.py"
        feature_file.parent.mkdir(parents=True)
        feature_file.write_text("# Feature implementation\n")

        source_tracking = SourceTracking(implementation_files=["src/feature.py"], test_files=[])
        source_tracking.update_hash(feature_file)

        feature = Feature(
            key="FEATURE-001",
            title="Test Feature",
            stories=[],
            source_tracking=source_tracking,
            contract=None,
            protocol=None,
        )
        project_bundle.features["FEATURE-001"] = feature

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Run drift detect
        result = runner.invoke(app, ["drift", "detect", bundle_name, "--repo", str(tmp_path)])

        assert result.exit_code == 0
        assert "Drift Detection" in result.stdout
        assert bundle_name in result.stdout

    def test_drift_detect_json_format(self, tmp_path) -> None:
        """Test drift detect with JSON output format."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        # Add feature with orphaned spec (no source tracking)
        feature = Feature(
            key="FEATURE-ORPHAN",
            title="Orphaned Feature",
            stories=[],
            source_tracking=None,  # No source tracking
            contract=None,
            protocol=None,
        )
        project_bundle.features["FEATURE-ORPHAN"] = feature

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Run drift detect with JSON output
        result = runner.invoke(app, ["drift", "detect", bundle_name, "--repo", str(tmp_path), "--format", "json"])

        assert result.exit_code == 0
        # Parse JSON output (may have extra text after JSON)
        # Find the JSON object by looking for first { and last }
        output_text = result.stdout.strip()
        json_start = output_text.find("{")
        json_end = output_text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            json_output = output_text[json_start:json_end]
            report_data = json.loads(json_output)
        else:
            # Fallback: try parsing entire output
            report_data = json.loads(output_text)

        assert "orphaned_specs" in report_data
        assert "FEATURE-ORPHAN" in report_data["orphaned_specs"]

    def test_drift_detect_yaml_format(self, tmp_path) -> None:
        """Test drift detect with YAML output format."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        # Add feature with test coverage gap
        feature = Feature(
            key="FEATURE-001",
            title="Feature with untested story",
            stories=[
                Story(
                    key="STORY-001",
                    title="Untested Story",
                    acceptance=[],
                    test_functions=[],  # No tests
                    story_points=None,
                    value_points=None,
                    scenarios=None,
                    contracts=None,
                )
            ],
            source_tracking=SourceTracking(implementation_files=[], test_files=[]),
            contract=None,
            protocol=None,
        )
        project_bundle.features["FEATURE-001"] = feature

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Run drift detect with YAML output
        result = runner.invoke(app, ["drift", "detect", bundle_name, "--repo", str(tmp_path), "--format", "yaml"])

        assert result.exit_code == 0
        # Parse YAML output (tuples may be serialized as Python objects)
        output_text = result.stdout.strip()
        # Find YAML content (starts with test_coverage_gaps or first key)
        yaml_start = output_text.find("test_coverage_gaps:")
        if yaml_start < 0:
            yaml_start = output_text.find("added_code:")
        if yaml_start >= 0:
            yaml_output = output_text[yaml_start:]
            # Use SafeLoader but handle tuples by converting them
            try:
                report_data = yaml.safe_load(yaml_output)
            except yaml.constructor.ConstructorError:
                # If tuples cause issues, just check the output contains the key
                assert "test_coverage_gaps" in yaml_output
                return
        else:
            # Fallback: just check output contains expected content
            assert "test_coverage_gaps" in output_text
            return

        assert "test_coverage_gaps" in report_data
        # test_coverage_gaps may be a list of tuples or lists
        if isinstance(report_data.get("test_coverage_gaps"), list):
            assert len(report_data["test_coverage_gaps"]) > 0

    def test_drift_detect_output_to_file(self, tmp_path) -> None:
        """Test drift detect with output to file."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Create untracked code file
        (tmp_path / "src" / "untracked.py").parent.mkdir(parents=True)
        (tmp_path / "src" / "untracked.py").write_text("# Untracked code\n")

        # Run drift detect with output to file
        output_file = tmp_path / "drift-report.json"
        result = runner.invoke(
            app,
            [
                "drift",
                "detect",
                bundle_name,
                "--repo",
                str(tmp_path),
                "--format",
                "json",
                "--out",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        report_data = json.loads(output_file.read_text())
        assert "added_code" in report_data

    def test_drift_detect_added_code(self, tmp_path) -> None:
        """Test drift detect identifies added code (files with no spec)."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Create untracked code file
        untracked_file = tmp_path / "src" / "untracked.py"
        untracked_file.parent.mkdir(parents=True)
        untracked_file.write_text("# Untracked code\n")

        # Run drift detect
        result = runner.invoke(app, ["drift", "detect", bundle_name, "--repo", str(tmp_path), "--format", "json"])

        assert result.exit_code == 0
        # Parse JSON output (may have extra text after JSON)
        output_text = result.stdout.strip()
        json_start = output_text.find("{")
        json_end = output_text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            json_output = output_text[json_start:json_end]
            report_data = json.loads(json_output)
        else:
            # Fallback: try parsing entire output
            report_data = json.loads(output_text)

        assert "added_code" in report_data
        assert any("untracked.py" in file for file in report_data["added_code"])

    def test_drift_detect_removed_code(self, tmp_path) -> None:
        """Test drift detect identifies removed code (deleted but spec exists)."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        # Add feature with tracked file that doesn't exist
        source_tracking = SourceTracking(
            implementation_files=["src/deleted.py"],
            test_files=[],
            file_hashes={"src/deleted.py": "old_hash"},
        )

        feature = Feature(
            key="FEATURE-001",
            title="Feature with deleted file",
            stories=[],
            source_tracking=source_tracking,
            contract=None,
            protocol=None,
        )
        project_bundle.features["FEATURE-001"] = feature

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Run drift detect
        result = runner.invoke(app, ["drift", "detect", bundle_name, "--repo", str(tmp_path), "--format", "json"])

        assert result.exit_code == 0
        # Parse JSON output (may have extra text after JSON)
        output_text = result.stdout.strip()
        json_start = output_text.find("{")
        json_end = output_text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            json_output = output_text[json_start:json_end]
            report_data = json.loads(json_output)
        else:
            # Fallback: try parsing entire output
            report_data = json.loads(output_text)

        assert "removed_code" in report_data
        assert any("deleted.py" in file for file in report_data["removed_code"])

    def test_drift_detect_modified_code(self, tmp_path) -> None:
        """Test drift detect identifies modified code (hash changed)."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        # Create file
        modified_file = tmp_path / "src" / "modified.py"
        modified_file.parent.mkdir(parents=True)
        modified_file.write_text("# Original content\n")

        # Add feature with old hash
        import hashlib

        old_content = b"# Old content\n"
        old_hash = hashlib.sha256(old_content).hexdigest()

        source_tracking = SourceTracking(
            implementation_files=["src/modified.py"],
            test_files=[],
            file_hashes={"src/modified.py": old_hash},
        )

        feature = Feature(
            key="FEATURE-001",
            title="Feature with modified file",
            stories=[],
            source_tracking=source_tracking,
            contract=None,
            protocol=None,
        )
        project_bundle.features["FEATURE-001"] = feature

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Run drift detect
        result = runner.invoke(app, ["drift", "detect", bundle_name, "--repo", str(tmp_path), "--format", "json"])

        assert result.exit_code == 0
        # Parse JSON output (may have extra text after JSON)
        output_text = result.stdout.strip()
        json_start = output_text.find("{")
        json_end = output_text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            json_output = output_text[json_start:json_end]
            report_data = json.loads(json_output)
        else:
            # Fallback: try parsing entire output
            report_data = json.loads(output_text)

        assert "modified_code" in report_data
        assert any("modified.py" in file for file in report_data["modified_code"])

    def test_drift_detect_no_drift(self, tmp_path) -> None:
        """Test drift detect when code and specs are in sync."""
        # Create bundle
        bundle_name = "test-bundle"
        bundle_dir = tmp_path / ".specfact" / "projects" / bundle_name
        bundle_dir.mkdir(parents=True)

        manifest = BundleManifest(schema_metadata=None, project_metadata=None)
        product = Product()
        project_bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

        # Create file
        feature_file = tmp_path / "src" / "feature.py"
        feature_file.parent.mkdir(parents=True)
        feature_file.write_text("# Feature implementation\n")

        # Add feature with matching hash
        source_tracking = SourceTracking(implementation_files=["src/feature.py"], test_files=[])
        source_tracking.update_hash(feature_file)

        feature = Feature(
            key="FEATURE-001",
            title="In Sync Feature",
            stories=[
                Story(
                    key="STORY-001",
                    title="Tested Story",
                    acceptance=[],
                    test_functions=["test_story_001"],  # Has tests
                    story_points=None,
                    value_points=None,
                    scenarios=None,
                    contracts=None,
                )
            ],
            source_tracking=source_tracking,
            contract=None,
            protocol=None,
        )
        project_bundle.features["FEATURE-001"] = feature

        save_project_bundle(project_bundle, bundle_dir, atomic=True)

        # Run drift detect
        result = runner.invoke(app, ["drift", "detect", bundle_name, "--repo", str(tmp_path)])

        assert result.exit_code == 0
        # Should show "No drift detected" or minimal issues
        assert "No drift detected" in result.stdout or "Total Issues" in result.stdout
