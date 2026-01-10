"""
E2E tests for complete sidecar validation workflows.
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
def fastapi_repo(tmp_path: Path) -> Path:
    """Create a FastAPI test repository."""
    repo = tmp_path / "fastapi-repo"
    repo.mkdir()

    # Create FastAPI app
    main_py = repo / "main.py"
    main_py.write_text(
        """from fastapi import FastAPI

app = FastAPI()

@app.get("/api/users")
def get_users():
    return {"users": []}
"""
    )

    return repo


@pytest.fixture
def django_repo(tmp_path: Path) -> Path:
    """Create a Django test repository."""
    repo = tmp_path / "django-repo"
    repo.mkdir()

    # Create manage.py
    manage_py = repo / "manage.py"
    manage_py.write_text(
        """import os
import django

DJANGO_SETTINGS_MODULE = "myproject.settings"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", DJANGO_SETTINGS_MODULE)
"""
    )

    # Create urls.py
    urls_py = repo / "urls.py"
    urls_py.write_text(
        """from django.urls import path

urlpatterns = [
    path("api/users/", lambda request: None, name="users"),
]
"""
    )

    return repo


def test_sidecar_init_run_workflow_fastapi(runner: CliRunner, fastapi_repo: Path) -> None:
    """Test complete sidecar init → run workflow for FastAPI."""
    bundle_name = "fastapi-test"

    # Step 1: Initialize
    init_result = runner.invoke(
        app,
        ["validate", "sidecar", "init", bundle_name, str(fastapi_repo)],
    )

    assert init_result.exit_code == 0
    assert "Sidecar workspace initialized successfully" in init_result.stdout
    assert "fastapi" in init_result.stdout.lower()

    # Step 2: Run validation (without tools to avoid external dependencies)
    run_result = runner.invoke(
        app,
        [
            "validate",
            "sidecar",
            "run",
            bundle_name,
            str(fastapi_repo),
            "--no-run-crosshair",
            "--no-run-specmatic",
        ],
    )

    # Should execute workflow steps (framework detection, route extraction, etc.)
    assert "Running sidecar validation" in run_result.stdout or "Validation Results" in run_result.stdout


def test_sidecar_init_run_workflow_django(runner: CliRunner, django_repo: Path) -> None:
    """Test complete sidecar init → run workflow for Django."""
    bundle_name = "django-test"

    # Step 1: Initialize
    init_result = runner.invoke(
        app,
        ["validate", "sidecar", "init", bundle_name, str(django_repo)],
    )

    assert init_result.exit_code == 0
    assert "Sidecar workspace initialized successfully" in init_result.stdout
    assert "django" in init_result.stdout.lower()

    # Step 2: Run validation (without tools to avoid external dependencies)
    run_result = runner.invoke(
        app,
        [
            "validate",
            "sidecar",
            "run",
            bundle_name,
            str(django_repo),
            "--no-run-crosshair",
            "--no-run-specmatic",
        ],
    )

    # Should execute workflow steps
    assert "Running sidecar validation" in run_result.stdout or "Validation Results" in run_result.stdout


def test_sidecar_framework_detection(runner: CliRunner, fastapi_repo: Path) -> None:
    """Test framework detection in sidecar workflow."""
    bundle_name = "framework-test"

    result = runner.invoke(
        app,
        ["validate", "sidecar", "init", bundle_name, str(fastapi_repo)],
    )

    assert result.exit_code == 0
    # Should detect FastAPI
    assert "fastapi" in result.stdout.lower() or "Framework detected" in result.stdout


def test_sidecar_workflow_with_invalid_repo(runner: CliRunner, tmp_path: Path) -> None:
    """Test sidecar workflow with invalid repository path."""
    bundle_name = "invalid-test"
    invalid_repo = tmp_path / "nonexistent"

    result = runner.invoke(
        app,
        ["validate", "sidecar", "init", bundle_name, str(invalid_repo)],
    )

    assert result.exit_code != 0
