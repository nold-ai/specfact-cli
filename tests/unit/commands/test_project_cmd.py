"""Unit tests for project commands."""

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.models.plan import Feature, Product, Story
from specfact_cli.models.project import BundleManifest, PersonaMapping, ProjectBundle
from specfact_cli.utils.bundle_loader import save_project_bundle


runner = CliRunner()


@pytest.fixture
def sample_bundle(tmp_path: Path, monkeypatch) -> tuple[Path, str]:
    """Create a sample project bundle for testing."""
    monkeypatch.chdir(tmp_path)

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

    return tmp_path, bundle_name


@pytest.fixture
def sample_bundle_no_personas(tmp_path: Path, monkeypatch) -> tuple[Path, str]:
    """Create a sample project bundle without personas for testing init-personas."""
    monkeypatch.chdir(tmp_path)

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

    return tmp_path, bundle_name


class TestProjectExport:
    """Test suite for project export command."""

    def test_export_persona_yaml(self, sample_bundle: tuple[Path, str]) -> None:
        """Test exporting bundle for a persona in YAML format."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"

        result = runner.invoke(
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
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0
        assert "FEATURE-001" in result.stdout or "Test Feature" in result.stdout

    def test_export_persona_json(self, sample_bundle: tuple[Path, str]) -> None:
        """Test exporting bundle for a persona in JSON format."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"

        result = runner.invoke(
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
                "json",
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0
        assert "FEATURE-001" in result.stdout or "Test Feature" in result.stdout


class TestProjectLock:
    """Test suite for project lock command."""

    def test_lock_section(self, sample_bundle: tuple[Path, str]) -> None:
        """Test locking a section."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"

        result = runner.invoke(
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

        assert result.exit_code == 0

    def test_lock_feature_section(self, sample_bundle: tuple[Path, str]) -> None:
        """Test locking a feature section."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"

        result = runner.invoke(
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
                "features.FEATURE-001.stories",
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0


class TestProjectUnlock:
    """Test suite for project unlock command."""

    def test_unlock_section(self, sample_bundle: tuple[Path, str]) -> None:
        """Test unlocking a section."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"

        # First lock
        runner.invoke(
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

        # Then unlock (unlock doesn't require persona)
        result = runner.invoke(
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

        assert result.exit_code == 0


class TestProjectLocks:
    """Test suite for project locks command."""

    def test_list_locks(self, sample_bundle: tuple[Path, str]) -> None:
        """Test listing locks."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"

        # First lock a section
        runner.invoke(
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

        # Then list locks
        result = runner.invoke(
            app,
            [
                "project",
                "locks",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0
        # Check if locks were listed (either shows locks or "No locks found")
        assert "Section" in result.stdout or "No locks found" in result.stdout or "idea" in result.stdout


class TestProjectInitPersonas:
    """Test suite for project init-personas command."""

    def test_init_all_personas(self, sample_bundle_no_personas: tuple[Path, str]) -> None:
        """Test initializing all default personas."""
        repo_path, bundle_name = sample_bundle_no_personas
        os.environ["TEST_MODE"] = "true"

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
        assert "persona" in result.stdout.lower()

        # Verify personas were actually added
        from specfact_cli.utils.bundle_loader import load_project_bundle

        bundle_dir = repo_path / ".specfact" / "projects" / bundle_name
        bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert len(bundle.manifest.personas) == 3  # product-owner, architect, developer
        assert "product-owner" in bundle.manifest.personas
        assert "architect" in bundle.manifest.personas
        assert "developer" in bundle.manifest.personas

    def test_init_specific_personas(self, sample_bundle_no_personas: tuple[Path, str]) -> None:
        """Test initializing specific personas."""
        repo_path, bundle_name = sample_bundle_no_personas
        os.environ["TEST_MODE"] = "true"

        result = runner.invoke(
            app,
            [
                "project",
                "init-personas",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--persona",
                "product-owner",
                "--persona",
                "architect",
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0
        assert "Initialized" in result.stdout

        # Verify only specified personas were added
        from specfact_cli.utils.bundle_loader import load_project_bundle

        bundle_dir = repo_path / ".specfact" / "projects" / bundle_name
        bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert len(bundle.manifest.personas) == 2
        assert "product-owner" in bundle.manifest.personas
        assert "architect" in bundle.manifest.personas
        assert "developer" not in bundle.manifest.personas

    def test_init_personas_when_already_exist(self, sample_bundle: tuple[Path, str]) -> None:
        """Test initializing personas when some already exist."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"

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
        # Should initialize developer (missing) and warn about existing ones
        assert "Initialized" in result.stdout or "already exists" in result.stdout.lower()

        # Verify developer was added
        from specfact_cli.utils.bundle_loader import load_project_bundle

        bundle_dir = repo_path / ".specfact" / "projects" / bundle_name
        bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        assert "developer" in bundle.manifest.personas

    def test_init_personas_all_exist(self, sample_bundle: tuple[Path, str]) -> None:
        """Test initializing personas when all already exist."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"

        # First initialize all personas
        runner.invoke(
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

        # Try again - should show message that all exist
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
        assert "already initialized" in result.stdout.lower() or "already exists" in result.stdout.lower()

    def test_init_invalid_persona(self, sample_bundle_no_personas: tuple[Path, str]) -> None:
        """Test initializing with invalid persona name."""
        repo_path, bundle_name = sample_bundle_no_personas
        os.environ["TEST_MODE"] = "true"

        result = runner.invoke(
            app,
            [
                "project",
                "init-personas",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--persona",
                "invalid-persona",
                "--no-interactive",
            ],
        )

        assert result.exit_code != 0
        assert "not a default persona" in result.stdout or "invalid" in result.stdout.lower()

    def test_init_personas_bundle_not_found(self, tmp_path: Path, monkeypatch) -> None:
        """Test initializing personas when bundle doesn't exist."""
        monkeypatch.chdir(tmp_path)
        os.environ["TEST_MODE"] = "true"

        result = runner.invoke(
            app,
            [
                "project",
                "init-personas",
                "--repo",
                str(tmp_path),
                "--bundle",
                "non-existent-bundle",
                "--no-interactive",
            ],
        )

        assert result.exit_code != 0
        assert "not found" in result.stdout.lower()
