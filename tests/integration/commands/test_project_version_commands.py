"""Integration tests for project version commands."""

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.models.plan import Feature, Product, Story
from specfact_cli.models.project import BundleManifest, ProjectBundle
from specfact_cli.utils.bundle_loader import save_project_bundle


runner = CliRunner()


def _create_bundle(tmp_path: Path, bundle_name: str = "main") -> Path:
    projects_dir = tmp_path / ".specfact" / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)

    bundle_dir = projects_dir / bundle_name
    bundle_dir.mkdir(parents=True, exist_ok=True)

    manifest = BundleManifest(schema_metadata=None, project_metadata=None)
    product = Product(themes=["Testing"])
    bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

    feature = Feature(
        key="FEATURE-001",
        title="Test Feature",
        outcomes=["Outcome"],
        stories=[
            Story(
                key="STORY-001",
                title="Story Title",
                acceptance=["Given ..."],
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

    save_project_bundle(bundle, bundle_dir, atomic=True)
    return bundle_dir


def test_version_check_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    bundle_dir = _create_bundle(tmp_path)
    result = runner.invoke(
        app,
        [
            "project",
            "version",
            "check",
            "--repo",
            str(tmp_path),
            "--bundle",
            bundle_dir.name,
        ],
    )
    assert result.exit_code == 0
    assert "Recommended bump" in result.stdout


def test_version_bump_and_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    bundle_dir = _create_bundle(tmp_path)

    # Bump minor
    bump_result = runner.invoke(
        app,
        [
            "project",
            "version",
            "bump",
            "--repo",
            str(tmp_path),
            "--bundle",
            bundle_dir.name,
            "--type",
            "minor",
        ],
    )
    assert bump_result.exit_code == 0

    manifest_path = bundle_dir / "bundle.manifest.yaml"
    manifest_data = yaml.safe_load(manifest_path.read_text())
    assert manifest_data["versions"]["project"] == "0.2.0"
    history = manifest_data.get("project_metadata", {}).get("version_history", [])
    assert history
    assert history[-1]["to"] == "0.2.0"
    assert manifest_data.get("bundle", {}).get("content_hash")

    # Set explicit version
    set_result = runner.invoke(
        app,
        [
            "project",
            "version",
            "set",
            "--repo",
            str(tmp_path),
            "--bundle",
            bundle_dir.name,
            "--version",
            "2.0.0",
        ],
    )
    assert set_result.exit_code == 0

    manifest_data = yaml.safe_load(manifest_path.read_text())
    assert manifest_data["versions"]["project"] == "2.0.0"
    history = manifest_data.get("project_metadata", {}).get("version_history", [])
    assert len(history) >= 2
    assert history[-1]["to"] == "2.0.0"
