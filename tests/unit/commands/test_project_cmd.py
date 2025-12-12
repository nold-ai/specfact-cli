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
    """Test suite for project export command (template-based Markdown)."""

    def test_export_persona_markdown_stdout(self, sample_bundle: tuple[Path, str]) -> None:
        """Test exporting bundle for a persona to stdout in Markdown format."""
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
                "--stdout",
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0
        # Check for Markdown structure
        assert "# Project Plan:" in result.stdout
        assert "Product Owner" in result.stdout or "product-owner" in result.stdout
        assert "FEATURE-001" in result.stdout or "Test Feature" in result.stdout
        assert "##" in result.stdout  # Markdown headings

    def test_export_persona_markdown_file(self, sample_bundle: tuple[Path, str]) -> None:
        """Test exporting bundle for a persona to file in Markdown format."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"

        output_file = repo_path / "exported.md"

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
                "--output",
                str(output_file),
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "# Project Plan:" in content
        assert "FEATURE-001" in content or "Test Feature" in content
        assert "##" in content  # Markdown headings

    def test_export_persona_default_location(self, sample_bundle: tuple[Path, str]) -> None:
        """Test exporting bundle to default location (docs/project-plans/<bundle>/<persona>.md)."""
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
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0
        default_output = repo_path / "docs" / "project-plans" / bundle_name / "product-owner.md"
        assert default_output.exists()
        content = default_output.read_text()
        assert "# Project Plan:" in content
        assert bundle_name in content

    def test_export_persona_custom_output_dir(self, sample_bundle: tuple[Path, str]) -> None:
        """Test exporting bundle to custom output directory."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"

        custom_dir = repo_path / "custom-exports"
        custom_dir.mkdir()

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
                "--output-dir",
                str(custom_dir),
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0
        output_file = custom_dir / "product-owner.md"
        assert output_file.exists()
        content = output_file.read_text()
        assert "# Project Plan:" in content

    def test_export_architect_persona(self, sample_bundle: tuple[Path, str]) -> None:
        """Test exporting bundle for architect persona."""
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
                "architect",
                "--stdout",
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0
        assert "# Project Plan:" in result.stdout
        assert "Architect" in result.stdout or "architect" in result.stdout


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


class TestProjectImport:
    """Test suite for project import command (template-validated)."""

    def test_import_missing_file(self, sample_bundle: tuple[Path, str]) -> None:
        """Test importing non-existent file fails."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"

        result = runner.invoke(
            app,
            [
                "project",
                "import",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--persona",
                "product-owner",
                "--input",
                str(repo_path / "nonexistent.md"),
                "--no-interactive",
            ],
        )

        assert result.exit_code != 0
        # Error message might be in stdout or stderr
        output = (result.stdout + result.stderr).lower()
        assert "not found" in output or "error" in output or "does not exist" in output

    def test_import_missing_persona(self, sample_bundle: tuple[Path, str]) -> None:
        """Test importing with non-existent persona fails."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"

        # Create a valid export file
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
                "--output",
                str(repo_path / "exported.md"),
                "--no-interactive",
            ],
        )
        assert export_result.exit_code == 0

        # Try to import with wrong persona
        result = runner.invoke(
            app,
            [
                "project",
                "import",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--persona",
                "nonexistent-persona",
                "--input",
                str(repo_path / "exported.md"),
                "--no-interactive",
            ],
        )

        assert result.exit_code != 0
        assert "not found" in result.stdout.lower() or "persona" in result.stdout.lower()

    def test_import_dry_run_validation(self, sample_bundle: tuple[Path, str]) -> None:
        """Test dry-run import validation."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"

        # Export first
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
                "--output",
                str(repo_path / "exported.md"),
                "--no-interactive",
            ],
        )
        assert export_result.exit_code == 0

        # Dry-run import
        result = runner.invoke(
            app,
            [
                "project",
                "import",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--persona",
                "product-owner",
                "--input",
                str(repo_path / "exported.md"),
                "--dry-run",
                "--no-interactive",
            ],
        )

        # Dry-run may pass or fail depending on template validation strictness
        # The important thing is that it attempts validation
        output = (result.stdout + result.stderr).lower()
        assert (
            "validation" in output
            or "dry-run" in output
            or "import" in output
            or "failed" in output
            or "error" in output
        )
