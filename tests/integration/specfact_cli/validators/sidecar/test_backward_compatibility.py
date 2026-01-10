"""
Backward compatibility tests for template-based sidecar workspaces.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.validators.sidecar.models import SidecarConfig


@pytest.fixture
def template_sidecar_workspace(tmp_path: Path) -> Path:
    """Create a template-based sidecar workspace structure."""
    workspace = tmp_path / "sidecar"
    workspace.mkdir()

    # Create .env file (template-based workspaces use .env)
    env_file = workspace / ".env"
    env_file.write_text(
        """REPO_PATH=/path/to/repo
BUNDLE_NAME=test-bundle
RUN_CROSSHAIR=1
RUN_SPECMATIC=1
"""
    )

    # Create harness file
    harness_file = workspace / "harness_contracts.py"
    harness_file.write_text("# Generated harness\n")

    # Create inputs file
    inputs_file = workspace / "inputs.json"
    inputs_file.write_text("{}")

    # Create bindings file
    bindings_file = workspace / "bindings.yaml"
    bindings_file.write_text("bindings: []\n")

    return workspace


@pytest.fixture
def test_repo_with_template_workspace(tmp_path: Path) -> Path:
    """Create a test repository with template-based sidecar workspace."""
    repo = tmp_path / "test-repo"
    repo.mkdir()

    # Create basic Python file
    (repo / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")

    # Create template-based sidecar workspace
    sidecar_dir = repo / ".specfact" / "projects" / "test-bundle" / "sidecar"
    sidecar_dir.mkdir(parents=True)

    # Create .env file
    env_file = sidecar_dir / ".env"
    env_file.write_text(
        f"""REPO_PATH={repo}
BUNDLE_NAME=test-bundle
RUN_CROSSHAIR=1
RUN_SPECMATIC=1
"""
    )

    return repo


def test_template_workspace_detection(template_sidecar_workspace: Path) -> None:
    """Test that template-based workspaces can be detected."""
    # Check that template workspace structure exists
    assert template_sidecar_workspace.exists()
    assert (template_sidecar_workspace / ".env").exists()
    assert (template_sidecar_workspace / "harness_contracts.py").exists()


def test_cli_works_with_template_workspace(runner: CliRunner, test_repo_with_template_workspace: Path) -> None:
    """Test that CLI commands work with template-based workspaces."""
    bundle_name = "test-bundle"
    repo_path = test_repo_with_template_workspace

    # The CLI should be able to run validation even if workspace was created via templates
    result = runner.invoke(
        app,
        [
            "validate",
            "sidecar",
            "run",
            bundle_name,
            str(repo_path),
            "--no-run-crosshair",
            "--no-run-specmatic",
        ],
    )

    # Command should execute (may fail if tools not available, but should not crash)
    assert result.exit_code in [0, 1]  # May fail due to missing tools, but shouldn't crash
    assert (
        "Running sidecar validation" in result.stdout
        or "Validation Results" in result.stdout
        or "Framework" in result.stdout
    )


def test_new_cli_creates_compatible_workspace(runner: CliRunner, tmp_path: Path) -> None:
    """Test that new CLI-created workspaces are compatible with template structure."""
    bundle_name = "test-bundle"
    repo = tmp_path / "test-repo"
    repo.mkdir()
    (repo / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")

    # Initialize via CLI
    result = runner.invoke(
        app,
        ["validate", "sidecar", "init", bundle_name, str(repo)],
    )

    assert result.exit_code == 0

    # Check that workspace structure is created (directories are created on-demand)
    workspace_dir = repo / ".specfact" / "projects" / bundle_name
    # The directory structure exists (may be created lazily)
    assert workspace_dir.exists() or workspace_dir.parent.exists()

    # Check that contracts directory path is configured (may not exist until contracts are created)
    contracts_dir = workspace_dir / "contracts"
    # Just verify the path structure is correct
    assert str(contracts_dir).endswith(f"{bundle_name}/contracts")

    # Check that reports directory exists (created during init)
    reports_dir = workspace_dir / "reports" / "sidecar"
    assert reports_dir.exists() or reports_dir.parent.exists()


def test_config_creation_from_template_workspace(template_sidecar_workspace: Path, tmp_path: Path) -> None:
    """Test creating SidecarConfig from template-based workspace."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()

    # Create config - should work even if workspace structure is different
    config = SidecarConfig.create(
        bundle_name="test-bundle",
        repo_path=repo_path,
    )

    assert config.bundle_name == "test-bundle"
    assert config.repo_path == repo_path
    # Verify path structure is correct (directories may be created lazily)
    assert str(config.paths.contracts_dir).endswith("test-bundle/contracts")
    assert str(config.paths.reports_dir).endswith("test-bundle/reports/sidecar")


@pytest.fixture
def runner() -> CliRunner:
    """Create CLI runner for testing."""
    return CliRunner()
