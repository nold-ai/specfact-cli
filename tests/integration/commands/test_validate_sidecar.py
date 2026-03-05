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


@pytest.fixture
def flask_test_repo(tmp_path: Path) -> Path:
    """Create a Flask test repository structure."""
    repo = tmp_path / "flask-test-repo"
    repo.mkdir()
    (repo / "app.py").write_text(
        """from flask import Flask

app = Flask(__name__)

@app.route("/api/users", methods=["GET"])
def get_users():
    return {"users": []}
"""
    )
    return repo


def test_validate_sidecar_init_command(runner: CliRunner, test_repo: Path, tmp_path: Path) -> None:
    """Test validate sidecar init command."""
    bundle_name = "test-bundle"
    result = runner.invoke(
        app,
        ["code", "validate", "sidecar", "init", bundle_name, str(test_repo)],
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
        ["code", "validate", "sidecar", "init", bundle_name, str(invalid_path)],
    )

    assert result.exit_code != 0


@pytest.mark.timeout(30)
def test_validate_sidecar_run_command(runner: CliRunner, test_repo: Path, tmp_path: Path) -> None:
    """Test validate sidecar run command."""
    bundle_name = "test-bundle"

    # First initialize
    init_result = runner.invoke(
        app,
        ["code", "validate", "sidecar", "init", bundle_name, str(test_repo)],
    )
    assert init_result.exit_code == 0

    # Then run validation
    result = runner.invoke(
        app,
        ["code", "validate", "sidecar", "run", bundle_name, str(test_repo), "--no-run-crosshair", "--no-run-specmatic"],
    )

    # Command should execute (may fail if tools not available, but should not crash)
    assert "Running sidecar validation" in result.stdout or "Validation Results" in result.stdout


def test_validate_sidecar_help(runner: CliRunner) -> None:
    """Test validate sidecar help text."""
    result = runner.invoke(app, ["code", "validate", "sidecar", "--help"])

    assert result.exit_code == 0
    assert "init" in result.stdout
    assert "run" in result.stdout


def test_validate_sidecar_init_help(runner: CliRunner) -> None:
    """Test validate sidecar init help text."""
    result = runner.invoke(app, ["code", "validate", "sidecar", "init", "--help"])

    assert result.exit_code == 0
    assert "Initialize sidecar workspace" in result.stdout


def test_validate_sidecar_run_help(runner: CliRunner) -> None:
    """Test validate sidecar run help text."""
    import re

    result = runner.invoke(app, ["code", "validate", "sidecar", "run", "--help"])

    assert result.exit_code == 0
    assert "Run sidecar validation workflow" in result.stdout
    # Strip ANSI codes for reliable string matching
    clean_output = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
    assert "--run-crosshair" in clean_output
    assert "--run-specmatic" in clean_output


def test_validate_sidecar_init_command_flask(runner: CliRunner, flask_test_repo: Path, tmp_path: Path) -> None:
    """Test validate sidecar init command with Flask repository."""
    bundle_name = "flask-bundle"
    result = runner.invoke(
        app,
        ["code", "validate", "sidecar", "init", bundle_name, str(flask_test_repo)],
    )

    assert result.exit_code == 0
    assert "Sidecar workspace initialized successfully" in result.stdout
    assert "Framework detected" in result.stdout
    # Should detect Flask (not PURE_PYTHON)
    assert "flask" in result.stdout.lower()


@pytest.mark.timeout(30)
def test_validate_sidecar_run_command_flask(runner: CliRunner, flask_test_repo: Path, tmp_path: Path) -> None:
    """Test validate sidecar run command with Flask repository."""
    bundle_name = "flask-bundle"

    # First initialize
    init_result = runner.invoke(
        app,
        ["code", "validate", "sidecar", "init", bundle_name, str(flask_test_repo)],
    )
    assert init_result.exit_code == 0

    # Then run validation
    result = runner.invoke(
        app,
        [
            "code",
            "validate",
            "sidecar",
            "run",
            bundle_name,
            str(flask_test_repo),
            "--no-run-crosshair",
            "--no-run-specmatic",
        ],
    )

    # Command should execute (may fail if tools not available, but should not crash)
    assert "Running sidecar validation" in result.stdout or "Validation Results" in result.stdout
    # Verify routes were extracted
    assert "Routes extracted" in result.stdout or "routes extracted" in result.stdout.lower()
