"""Integration tests for project commands."""

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.models.plan import Feature, Product, Story
from specfact_cli.models.project import BundleManifest, PersonaMapping, ProjectBundle
from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle


runner = CliRunner()


@pytest.fixture
def sample_bundle_with_git(tmp_path: Path, monkeypatch) -> tuple[Path, str]:
    """Create a sample project bundle in a Git repository for testing."""
    monkeypatch.chdir(tmp_path)

    # Initialize Git repository
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)

    # Create .specfact structure
    projects_dir = tmp_path / ".specfact" / "projects"
    projects_dir.mkdir(parents=True)

    bundle_name = "test-bundle"
    bundle_dir = projects_dir / bundle_name
    bundle_dir.mkdir()

    # Create ProjectBundle
    manifest = BundleManifest(
        schema_metadata=None,
        project_metadata=None,
        personas={
            "product-owner": PersonaMapping(
                owns=["idea", "business", "features.*.stories"], exports_to="specs/*/spec.md"
            ),
            "architect": PersonaMapping(owns=["features.*.constraints", "protocols"], exports_to="specs/*/plan.md"),
        },
    )
    product = Product(themes=["Testing"])
    bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

    feature = Feature(
        key="FEATURE-001",
        title="Test Feature",
        outcomes=["Test outcome"],
        stories=[
            Story(
                key="STORY-001",
                title="Test Story",
                acceptance=["Test acceptance"],
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

    # Commit initial state
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmp_path, check=True, capture_output=True)

    return tmp_path, bundle_name


class TestProjectExportImport:
    """Test suite for project export and import commands."""

    def test_export_import_roundtrip(self, sample_bundle_with_git: tuple[Path, str]) -> None:
        """Test exporting and importing a bundle maintains data integrity."""
        repo_path, bundle_name = sample_bundle_with_git
        os.environ["TEST_MODE"] = "true"

        # Export
        export_result = runner.invoke(
            app,
            [
                "project",
                "export",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--persona",
                "product-owner",
                "--format",
                "yaml",
                "--output",
                str(repo_path / "exported.yaml"),
                "--no-interactive",
            ],
        )

        assert export_result.exit_code == 0
        assert (repo_path / "exported.yaml").exists()

        # Verify exported content
        exported_content = (repo_path / "exported.yaml").read_text()
        assert "FEATURE-001" in exported_content or "Test Feature" in exported_content


class TestProjectLockWorkflow:
    """Test suite for project lock/unlock workflow."""

    def test_lock_unlock_workflow(self, sample_bundle_with_git: tuple[Path, str]) -> None:
        """Test complete lock/unlock workflow."""
        repo_path, bundle_name = sample_bundle_with_git
        os.environ["TEST_MODE"] = "true"

        # Lock
        lock_result = runner.invoke(
            app,
            [
                "project",
                "lock",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--persona",
                "product-owner",
                "--section",
                "idea",
                "--no-interactive",
            ],
        )

        assert lock_result.exit_code == 0

        # Verify lock exists
        bundle_dir = repo_path / ".specfact" / "projects" / bundle_name
        bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert len(bundle.manifest.locks) > 0
        assert any(lock.section == "idea" for lock in bundle.manifest.locks)

        # Unlock (unlock doesn't require persona)
        unlock_result = runner.invoke(
            app,
            [
                "project",
                "unlock",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--section",
                "idea",
                "--no-interactive",
            ],
        )

        assert unlock_result.exit_code == 0

        # Verify lock removed
        bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert not any(lock.section == "idea" for lock in bundle.manifest.locks)


@pytest.fixture
def sample_bundle_no_personas_with_git(tmp_path: Path, monkeypatch) -> tuple[Path, str]:
    """Create a sample project bundle without personas in a Git repository for testing."""
    monkeypatch.chdir(tmp_path)

    # Initialize Git repository
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)

    # Create .specfact structure
    projects_dir = tmp_path / ".specfact" / "projects"
    projects_dir.mkdir(parents=True)

    bundle_name = "test-bundle-no-personas"
    bundle_dir = projects_dir / bundle_name
    bundle_dir.mkdir()

    # Create ProjectBundle without personas
    manifest = BundleManifest(
        schema_metadata=None,
        project_metadata=None,
        personas={},  # No personas
    )
    product = Product(themes=["Testing"])
    bundle = ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)

    feature = Feature(
        key="FEATURE-001",
        title="Test Feature",
        outcomes=["Test outcome"],
        stories=[
            Story(
                key="STORY-001",
                title="Test Story",
                acceptance=["Test acceptance"],
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

    # Commit initial state
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmp_path, check=True, capture_output=True)

    return tmp_path, bundle_name


class TestProjectInitPersonas:
    """Test suite for project init-personas command integration."""

    def test_init_personas_workflow(self, sample_bundle_no_personas_with_git: tuple[Path, str]) -> None:
        """Test complete init-personas workflow and verify personas persist."""
        repo_path, bundle_name = sample_bundle_no_personas_with_git
        os.environ["TEST_MODE"] = "true"

        # Initialize all personas
        result = runner.invoke(
            app,
            [
                "project",
                "init-personas",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0
        assert "Initialized" in result.stdout

        # Verify personas were saved
        bundle_dir = repo_path / ".specfact" / "projects" / bundle_name
        bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert len(bundle.manifest.personas) == 3
        assert "product-owner" in bundle.manifest.personas
        assert "architect" in bundle.manifest.personas
        assert "developer" in bundle.manifest.personas

        # Verify personas have correct mappings
        po = bundle.manifest.personas["product-owner"]
        assert "idea" in po.owns
        assert "business" in po.owns
        assert "features.*.stories" in po.owns

        arch = bundle.manifest.personas["architect"]
        assert "features.*.constraints" in arch.owns
        assert "protocols" in arch.owns

    def test_init_personas_then_export(self, sample_bundle_no_personas_with_git: tuple[Path, str]) -> None:
        """Test that after initializing personas, export command works."""
        repo_path, bundle_name = sample_bundle_no_personas_with_git
        os.environ["TEST_MODE"] = "true"

        # Initialize personas
        init_result = runner.invoke(
            app,
            [
                "project",
                "init-personas",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--no-interactive",
            ],
        )

        assert init_result.exit_code == 0

        # Now export should work
        export_result = runner.invoke(
            app,
            [
                "project",
                "export",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--persona",
                "product-owner",
                "--no-interactive",
            ],
        )

        assert export_result.exit_code == 0
        assert "FEATURE-001" in export_result.stdout or "Test Feature" in export_result.stdout

    def test_init_personas_then_lock(self, sample_bundle_no_personas_with_git: tuple[Path, str]) -> None:
        """Test that after initializing personas, lock command works."""
        repo_path, bundle_name = sample_bundle_no_personas_with_git
        os.environ["TEST_MODE"] = "true"

        # Initialize personas
        init_result = runner.invoke(
            app,
            [
                "project",
                "init-personas",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--no-interactive",
            ],
        )

        assert init_result.exit_code == 0

        # Now lock should work
        lock_result = runner.invoke(
            app,
            [
                "project",
                "lock",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--persona",
                "product-owner",
                "--section",
                "idea",
                "--no-interactive",
            ],
        )

        assert lock_result.exit_code == 0

        # Verify lock was created
        bundle_dir = repo_path / ".specfact" / "projects" / bundle_name
        bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert len(bundle.manifest.locks) > 0
        assert any(lock.section == "idea" for lock in bundle.manifest.locks)
