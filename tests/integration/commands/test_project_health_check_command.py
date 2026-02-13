"""Integration tests for project health-check command."""

from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.models.plan import Product
from specfact_cli.models.project import BundleManifest, ProjectBundle
from specfact_cli.utils.bundle_loader import save_project_bundle


runner = CliRunner()


def _create_bundle(repo_path: Path, bundle_name: str) -> None:
    projects_dir = repo_path / ".specfact" / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    bundle_dir = projects_dir / bundle_name
    bundle_dir.mkdir(parents=True, exist_ok=True)
    bundle = ProjectBundle(
        manifest=BundleManifest(schema_metadata=None, project_metadata=None),
        bundle_name=bundle_name,
        product=Product(themes=["Testing"]),
    )
    save_project_bundle(bundle, bundle_dir, atomic=True)


def test_project_health_check_requires_backlog_link(tmp_path: Path, monkeypatch) -> None:
    """health-check exits non-zero when project backlog link is missing."""
    monkeypatch.chdir(tmp_path)
    os.environ["TEST_MODE"] = "true"
    bundle_name = "integration-bundle"
    _create_bundle(tmp_path, bundle_name)

    result = runner.invoke(
        app,
        [
            "project",
            "health-check",
            "--repo",
            str(tmp_path),
            "--bundle",
            bundle_name,
            "--no-interactive",
        ],
    )

    assert result.exit_code != 0
    assert "link-backlog" in result.stdout


def test_project_health_check_linked_config_reports_metrics(tmp_path: Path, monkeypatch) -> None:
    """health-check reports metrics when backlog link exists."""
    monkeypatch.chdir(tmp_path)
    os.environ["TEST_MODE"] = "true"
    bundle_name = "integration-bundle"
    _create_bundle(tmp_path, bundle_name)

    link_result = runner.invoke(
        app,
        [
            "project",
            "link-backlog",
            "--repo",
            str(tmp_path),
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
            "total_items": 10,
            "properly_typed": 9,
            "properly_typed_pct": 90.0,
            "with_dependencies": 7,
            "orphan_count": 1,
            "cycle_count": 0,
        },
    )

    result = runner.invoke(
        app,
        [
            "project",
            "health-check",
            "--repo",
            str(tmp_path),
            "--bundle",
            bundle_name,
            "--no-interactive",
        ],
    )

    assert result.exit_code == 0
    assert "Project Health Check" in result.stdout
    assert "9/10" in result.stdout
