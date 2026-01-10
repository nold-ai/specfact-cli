"""
Integration tests for validate sidecar commands.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app


@pytest.fixture
def runner() -> CliRunner:
    """Create CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def test_repo(tmp_path: Path) -> Path:
    """Create a test repository structure."""
    repo = tmp_path / "test-repo"
    repo.mkdir()
    (repo / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")
    return repo


def test_validate_sidecar_init_command(runner: CliRunner, test_repo: Path, tmp_path: Path) -> None:
    """Test validate sidecar init command."""
    bundle_name = "test-bundle"
    result = runner.invoke(
        app,
        ["validate", "sidecar", "init", bundle_name, str(test_repo)],
    )

    assert result.exit_code == 0
    assert "Sidecar workspace initialized successfully" in result.stdout
    assert "Framework detected" in result.stdout


def test_validate_sidecar_init_command_invalid_path(runner: CliRunner, tmp_path: Path) -> None:
    """Test validate sidecar init command with invalid path."""
    bundle_name = "test-bundle"
    invalid_path = tmp_path / "nonexistent"
    result = runner.invoke(
        app,
        ["validate", "sidecar", "init", bundle_name, str(invalid_path)],
    )

    assert result.exit_code != 0


def test_validate_sidecar_run_command(runner: CliRunner, test_repo: Path, tmp_path: Path) -> None:
    """Test validate sidecar run command."""
    bundle_name = "test-bundle"

    # First initialize
    init_result = runner.invoke(
        app,
        ["validate", "sidecar", "init", bundle_name, str(test_repo)],
    )
    assert init_result.exit_code == 0

    # Then run validation
    result = runner.invoke(
        app,
        ["validate", "sidecar", "run", bundle_name, str(test_repo), "--no-run-crosshair", "--no-run-specmatic"],
    )

    # Command should execute (may fail if tools not available, but should not crash)
    assert "Running sidecar validation" in result.stdout or "Validation Results" in result.stdout


def test_validate_sidecar_help(runner: CliRunner) -> None:
    """Test validate sidecar help text."""
    result = runner.invoke(app, ["validate", "sidecar", "--help"])

    assert result.exit_code == 0
    assert "init" in result.stdout
    assert "run" in result.stdout


def test_validate_sidecar_init_help(runner: CliRunner) -> None:
    """Test validate sidecar init help text."""
    result = runner.invoke(app, ["validate", "sidecar", "init", "--help"])

    assert result.exit_code == 0
    assert "Initialize sidecar workspace" in result.stdout


def test_validate_sidecar_run_help(runner: CliRunner) -> None:
    """Test validate sidecar run help text."""
    result = runner.invoke(app, ["validate", "sidecar", "run", "--help"])

    assert result.exit_code == 0
    assert "Run sidecar validation workflow" in result.stdout
    assert "--run-crosshair" in result.stdout
    assert "--run-specmatic" in result.stdout
