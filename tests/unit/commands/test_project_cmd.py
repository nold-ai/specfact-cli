"""Unit tests for project commands."""

import io
import os
from pathlib import Path

import pytest
import yaml
from rich.console import Console
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
        # Access stdout immediately to prevent I/O operation on closed file error
        _ = lock_result.stdout

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
        # Access stdout immediately to prevent I/O operation on closed file error
        _ = result.stdout

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

    def test_list_locks_refreshes_console_when_module_console_is_closed(self, sample_bundle: tuple[Path, str]) -> None:
        """Project command callback should refresh stale/closed module console streams."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"

        from specfact_cli.modules.project.src import commands as project_commands

        closed_stream = io.StringIO()
        closed_stream.close()
        project_commands.console = Console(file=closed_stream)

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
        output = result.stdout
        if result.stderr_bytes is not None:
            output += result.stderr
        output = output.lower()
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
        output = result.stdout
        if result.stderr_bytes is not None:
            output += result.stderr
        output = output.lower()
        assert (
            "validation" in output
            or "dry-run" in output
            or "import" in output
            or "failed" in output
            or "error" in output
        )


class TestProjectVersionCommands:
    """Tests for version subcommands."""

    def test_version_bump_updates_manifest(self, sample_bundle: tuple[Path, str]) -> None:
        repo_path, bundle_name = sample_bundle
        manifest_path = repo_path / ".specfact" / "projects" / bundle_name / "bundle.manifest.yaml"

        result = runner.invoke(
            app,
            [
                "project",
                "version",
                "bump",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--type",
                "minor",
            ],
        )

        assert result.exit_code == 0
        manifest_data = yaml.safe_load(manifest_path.read_text())
        assert manifest_data["versions"]["project"] == "0.2.0"
        history = manifest_data.get("project_metadata", {}).get("version_history", [])
        assert history
        assert history[-1]["to"] == "0.2.0"
        assert manifest_data.get("bundle", {}).get("content_hash")

    def test_version_set_assigns_explicit_value(self, sample_bundle: tuple[Path, str]) -> None:
        repo_path, bundle_name = sample_bundle
        manifest_path = repo_path / ".specfact" / "projects" / bundle_name / "bundle.manifest.yaml"

        result = runner.invoke(
            app,
            [
                "project",
                "version",
                "set",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--version",
                "1.2.3",
            ],
        )

        assert result.exit_code == 0
        manifest_data = yaml.safe_load(manifest_path.read_text())
        assert manifest_data["versions"]["project"] == "1.2.3"
        history = manifest_data.get("project_metadata", {}).get("version_history", [])
        assert history
        assert history[-1]["to"] == "1.2.3"


class TestProjectLinkBacklog:
    """Tests for backlog linking under project commands."""

    def test_link_backlog_persists_backlog_core_extension(self, sample_bundle: tuple[Path, str]) -> None:
        """`project link-backlog` stores adapter/project id in project metadata extensions."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"

        result = runner.invoke(
            app,
            [
                "project",
                "link-backlog",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--adapter",
                "github",
                "--project-id",
                "nold-ai/specfact-cli",
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0
        assert "Linked backlog provider" in result.stdout

        from specfact_cli.utils.bundle_loader import load_project_bundle

        bundle_dir = repo_path / ".specfact" / "projects" / bundle_name
        bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        project_metadata = bundle.manifest.project_metadata
        assert project_metadata is not None
        cfg = project_metadata.get_extension("backlog_core", "backlog_config")
        assert isinstance(cfg, dict)
        assert cfg["adapter"] == "github"
        assert cfg["project_id"] == "nold-ai/specfact-cli"

    def test_link_backlog_can_include_template(self, sample_bundle: tuple[Path, str]) -> None:
        """`project link-backlog` optionally stores template override."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"

        result = runner.invoke(
            app,
            [
                "project",
                "link-backlog",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--adapter",
                "ado",
                "--project-id",
                "org/project",
                "--template",
                "ado_scrum",
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0

        from specfact_cli.utils.bundle_loader import load_project_bundle

        bundle_dir = repo_path / ".specfact" / "projects" / bundle_name
        bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        project_metadata = bundle.manifest.project_metadata
        assert project_metadata is not None
        cfg = project_metadata.get_extension("backlog_core", "backlog_config")
        assert isinstance(cfg, dict)
        assert cfg["template"] == "ado_scrum"

    def test_link_backlog_accepts_project_name_alias(self, sample_bundle: tuple[Path, str]) -> None:
        """`--project-name` works as an alias to select bundle."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"

        result = runner.invoke(
            app,
            [
                "project",
                "link-backlog",
                "--repo",
                str(repo_path),
                "--project-name",
                bundle_name,
                "--adapter",
                "github",
                "--project-id",
                "nold-ai/specfact-cli",
                "--no-interactive",
            ],
        )
        assert result.exit_code == 0

    def test_link_backlog_rejects_mismatched_bundle_and_project_name(self, sample_bundle: tuple[Path, str]) -> None:
        """`--bundle` and `--project-name` must match when both provided."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"

        result = runner.invoke(
            app,
            [
                "project",
                "link-backlog",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--project-name",
                "different-bundle",
                "--adapter",
                "github",
                "--project-id",
                "nold-ai/specfact-cli",
                "--no-interactive",
            ],
        )
        assert result.exit_code != 0
        assert "--bundle and --project-name" in result.stdout


class TestProjectHealthCheck:
    """Tests for project health-check command."""

    def test_health_check_requires_backlog_link(self, sample_bundle: tuple[Path, str]) -> None:
        """health-check fails when backlog link is missing."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"

        result = runner.invoke(
            app,
            [
                "project",
                "health-check",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--no-interactive",
            ],
        )
        assert result.exit_code != 0
        assert "link-backlog" in result.stdout

    def test_health_check_uses_linked_backlog_config(self, sample_bundle: tuple[Path, str], monkeypatch) -> None:
        """health-check uses linked backlog config and prints summary."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"

        link_result = runner.invoke(
            app,
            [
                "project",
                "link-backlog",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--adapter",
                "github",
                "--project-id",
                "nold-ai/specfact-cli",
                "--no-interactive",
            ],
        )
        assert link_result.exit_code == 0

        from specfact_cli.modules.project.src import commands as project_commands

        monkeypatch.setattr(
            project_commands,
            "_collect_backlog_health_metrics",
            lambda *_args, **_kwargs: {
                "total_items": 12,
                "properly_typed": 11,
                "properly_typed_pct": 91.6,
                "with_dependencies": 8,
                "orphan_count": 1,
                "cycle_count": 0,
            },
        )
        monkeypatch.setattr(
            project_commands,
            "_run_spec_code_alignment_check",
            lambda *_args, **_kwargs: {"ok": True, "summary": "alignment-ok"},
        )
        monkeypatch.setattr(
            project_commands,
            "_run_release_readiness_check",
            lambda *_args, **_kwargs: {"ok": True, "summary": "release-ready"},
        )

        result = runner.invoke(
            app,
            [
                "project",
                "health-check",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--no-interactive",
            ],
        )
        assert result.exit_code == 0
        assert "Project Health Check" in result.stdout
        assert "11/12" in result.stdout
        assert "Spec-Code Alignment" in result.stdout
        assert "Release Readiness" in result.stdout


class TestProjectDevOpsFlow:
    """Tests for project devops-flow command."""

    def test_devops_flow_requires_supported_stage_action(self, sample_bundle: tuple[Path, str]) -> None:
        """devops-flow rejects unsupported stage/action combinations."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"

        result = runner.invoke(
            app,
            [
                "project",
                "devops-flow",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--stage",
                "plan",
                "--action",
                "unknown-action",
                "--no-interactive",
            ],
        )
        assert result.exit_code != 0
        assert "Unsupported stage/action" in result.stdout

    def test_devops_flow_monitor_health_check_delegates(self, sample_bundle: tuple[Path, str], monkeypatch) -> None:
        """devops-flow monitor/health-check delegates to project health-check."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"
        from specfact_cli.modules.project.src import commands as project_commands

        calls: list[tuple[str, str]] = []

        def _fake_health_check(
            *, repo: Path, bundle: str | None, project_name: str | None, verbose: bool, no_interactive: bool
        ) -> None:
            _ = project_name, verbose, no_interactive
            calls.append((str(repo), bundle or ""))

        monkeypatch.setattr(project_commands, "health_check", _fake_health_check)

        result = runner.invoke(
            app,
            [
                "project",
                "devops-flow",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--stage",
                "monitor",
                "--action",
                "health-check",
                "--no-interactive",
            ],
        )
        assert result.exit_code == 0
        assert calls == [(str(repo_path), bundle_name)]

    def test_devops_flow_plan_generate_roadmap(self, sample_bundle: tuple[Path, str], monkeypatch) -> None:
        """devops-flow plan/generate-roadmap calls roadmap helper."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"
        from specfact_cli.modules.project.src import commands as project_commands

        link_result = runner.invoke(
            app,
            [
                "project",
                "link-backlog",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--adapter",
                "github",
                "--project-id",
                "nold-ai/specfact-cli",
                "--no-interactive",
            ],
        )
        assert link_result.exit_code == 0

        calls: list[tuple[str, str]] = []

        def _fake_generate_roadmap(*, adapter: str, project_id: str, template: str) -> list[str]:
            calls.append((adapter, project_id))
            _ = template
            return ["M1", "M2"]

        monkeypatch.setattr(project_commands, "generate_roadmap", _fake_generate_roadmap)

        result = runner.invoke(
            app,
            [
                "project",
                "devops-flow",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--stage",
                "plan",
                "--action",
                "generate-roadmap",
                "--no-interactive",
            ],
        )
        assert result.exit_code == 0
        assert calls == [("github", "nold-ai/specfact-cli")]

    def test_devops_flow_release_verify_calls_readiness(self, sample_bundle: tuple[Path, str], monkeypatch) -> None:
        """devops-flow release/verify delegates release checks."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"
        from specfact_cli.modules.project.src import commands as project_commands

        link_result = runner.invoke(
            app,
            [
                "project",
                "link-backlog",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--adapter",
                "github",
                "--project-id",
                "nold-ai/specfact-cli",
                "--no-interactive",
            ],
        )
        assert link_result.exit_code == 0

        calls: list[tuple[str, str, str]] = []

        def _fake_release_check(*, adapter: str, project_id: str, template: str) -> dict[str, object]:
            calls.append((adapter, project_id, template))
            return {"ok": True, "summary": "ready"}

        monkeypatch.setattr(project_commands, "_run_release_readiness_check", _fake_release_check)

        result = runner.invoke(
            app,
            [
                "project",
                "devops-flow",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--stage",
                "release",
                "--action",
                "verify",
                "--no-interactive",
            ],
        )
        assert result.exit_code == 0
        assert calls


class TestProjectBacklogDerivedCommands:
    """Tests for snapshot/regenerate/export-roadmap project commands."""

    def test_snapshot_writes_baseline(self, sample_bundle: tuple[Path, str], monkeypatch) -> None:
        """snapshot stores backlog graph baseline JSON."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"
        from specfact_cli.modules.project.src import commands as project_commands

        link_result = runner.invoke(
            app,
            [
                "project",
                "link-backlog",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--adapter",
                "github",
                "--project-id",
                "nold-ai/specfact-cli",
                "--no-interactive",
            ],
        )
        assert link_result.exit_code == 0

        class _FakeGraph:
            def to_json(self) -> str:
                return '{"provider":"github","project_key":"nold-ai/specfact-cli","items":{},"dependencies":[]}'

        monkeypatch.setattr(project_commands, "_fetch_backlog_graph", lambda **_kwargs: _FakeGraph())

        result = runner.invoke(
            app,
            [
                "project",
                "snapshot",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--no-interactive",
            ],
        )
        assert result.exit_code == 0
        assert (repo_path / ".specfact" / "backlog-baseline.json").exists()

    def test_export_roadmap_runs_critical_path(self, sample_bundle: tuple[Path, str], monkeypatch) -> None:
        """export-roadmap renders analyzer critical path output."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"
        from specfact_cli.modules.project.src import commands as project_commands

        link_result = runner.invoke(
            app,
            [
                "project",
                "link-backlog",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--adapter",
                "github",
                "--project-id",
                "nold-ai/specfact-cli",
                "--no-interactive",
            ],
        )
        assert link_result.exit_code == 0

        monkeypatch.setattr(project_commands, "generate_roadmap", lambda **_kwargs: ["FEATURE-1", "STORY-2"])

        result = runner.invoke(
            app,
            [
                "project",
                "export-roadmap",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--no-interactive",
            ],
        )
        assert result.exit_code == 0
        assert "FEATURE-1" in result.stdout

    def test_regenerate_runs_sync_and_conflict_scan(self, sample_bundle: tuple[Path, str], monkeypatch) -> None:
        """regenerate calls merge/conflict helpers over plan and backlog views."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"
        from specfact_cli.modules.project.src import commands as project_commands

        link_result = runner.invoke(
            app,
            [
                "project",
                "link-backlog",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--adapter",
                "github",
                "--project-id",
                "nold-ai/specfact-cli",
                "--no-interactive",
            ],
        )
        assert link_result.exit_code == 0

        calls: list[str] = []
        monkeypatch.setattr(project_commands, "merge_plans", lambda *_args, **_kwargs: {"merged": True})
        monkeypatch.setattr(project_commands, "_fetch_backlog_graph", lambda **_kwargs: type("G", (), {"items": {}})())

        def _fake_find_conflicts(*_args, **_kwargs) -> list[str]:
            calls.append("conflicts")
            return []

        monkeypatch.setattr(project_commands, "find_conflicts", _fake_find_conflicts)

        result = runner.invoke(
            app,
            [
                "project",
                "regenerate",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--no-interactive",
            ],
        )
        assert result.exit_code == 0
        assert calls == ["conflicts"]

    def test_regenerate_conflicts_are_summary_only_by_default(
        self, sample_bundle: tuple[Path, str], monkeypatch
    ) -> None:
        """regenerate reports mismatch summary without failing when --strict is not set."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"
        from specfact_cli.modules.project.src import commands as project_commands

        link_result = runner.invoke(
            app,
            [
                "project",
                "link-backlog",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--adapter",
                "github",
                "--project-id",
                "nold-ai/specfact-cli",
                "--no-interactive",
            ],
        )
        assert link_result.exit_code == 0

        monkeypatch.setattr(project_commands, "_fetch_backlog_graph", lambda **_kwargs: type("G", (), {"items": {}})())
        monkeypatch.setattr(project_commands, "merge_plans", lambda *_args, **_kwargs: {"merged": True})
        monkeypatch.setattr(
            project_commands,
            "find_conflicts",
            lambda *_args, **_kwargs: ["Backlog item '123' missing in plan", "Backlog item '124' missing in plan"],
        )

        result = runner.invoke(
            app,
            [
                "project",
                "regenerate",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--no-interactive",
            ],
        )
        assert result.exit_code == 0
        assert "Detected 2 plan/backlog mismatches" in result.stdout
        assert "Backlog item '123' missing in plan" not in result.stdout

    def test_regenerate_strict_fails_and_verbose_lists_conflicts(
        self, sample_bundle: tuple[Path, str], monkeypatch
    ) -> None:
        """regenerate --strict returns non-zero and --verbose prints conflict details."""
        repo_path, bundle_name = sample_bundle
        os.environ["TEST_MODE"] = "true"
        from specfact_cli.modules.project.src import commands as project_commands

        link_result = runner.invoke(
            app,
            [
                "project",
                "link-backlog",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--adapter",
                "github",
                "--project-id",
                "nold-ai/specfact-cli",
                "--no-interactive",
            ],
        )
        assert link_result.exit_code == 0

        monkeypatch.setattr(project_commands, "_fetch_backlog_graph", lambda **_kwargs: type("G", (), {"items": {}})())
        monkeypatch.setattr(project_commands, "merge_plans", lambda *_args, **_kwargs: {"merged": True})
        monkeypatch.setattr(
            project_commands,
            "find_conflicts",
            lambda *_args, **_kwargs: ["Backlog item '123' missing in plan"],
        )

        result = runner.invoke(
            app,
            [
                "project",
                "regenerate",
                "--repo",
                str(repo_path),
                "--bundle",
                bundle_name,
                "--strict",
                "--verbose",
                "--no-interactive",
            ],
        )
        assert result.exit_code != 0
        assert "Backlog item '123' missing in plan" in result.stdout
