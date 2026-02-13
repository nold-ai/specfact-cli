"""Integration tests for project devops-flow/snapshot/regenerate/export-roadmap commands."""

from __future__ import annotations

import os
import sys
import types
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


def _link_backlog(repo_path: Path, bundle_name: str) -> None:
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


def test_project_devops_flow_plan_generate_roadmap(tmp_path: Path, monkeypatch) -> None:
    """devops-flow plan/generate-roadmap renders roadmap output."""
    monkeypatch.chdir(tmp_path)
    os.environ["TEST_MODE"] = "true"
    bundle_name = "integration-bundle"
    _create_bundle(tmp_path, bundle_name)
    _link_backlog(tmp_path, bundle_name)

    from specfact_cli.modules.project.src import commands as project_commands

    monkeypatch.setattr(project_commands, "generate_roadmap", lambda **_kwargs: ["A-1", "A-2"])

    result = runner.invoke(
        app,
        [
            "project",
            "devops-flow",
            "--repo",
            str(tmp_path),
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
    assert "Roadmap" in result.stdout
    assert "A-1" in result.stdout


def test_project_snapshot_writes_baseline(tmp_path: Path, monkeypatch) -> None:
    """snapshot command writes backlog baseline file."""
    monkeypatch.chdir(tmp_path)
    os.environ["TEST_MODE"] = "true"
    bundle_name = "integration-bundle"
    _create_bundle(tmp_path, bundle_name)
    _link_backlog(tmp_path, bundle_name)

    from specfact_cli.modules.project.src import commands as project_commands

    class _FakeGraph:
        def __init__(self) -> None:
            self.items: dict[str, str] = {}

        def to_json(self) -> str:
            return '{"provider":"github","project_key":"nold-ai/specfact-cli","items":{},"dependencies":[]}'

    monkeypatch.setattr(project_commands, "_fetch_backlog_graph", lambda **_kwargs: _FakeGraph())

    result = runner.invoke(
        app,
        [
            "project",
            "snapshot",
            "--repo",
            str(tmp_path),
            "--bundle",
            bundle_name,
            "--no-interactive",
        ],
    )
    assert result.exit_code == 0
    assert (tmp_path / ".specfact" / "backlog-baseline.json").exists()


def test_project_regenerate_and_export_roadmap(tmp_path: Path, monkeypatch) -> None:
    """regenerate and export-roadmap run against linked backlog config."""
    monkeypatch.chdir(tmp_path)
    os.environ["TEST_MODE"] = "true"
    bundle_name = "integration-bundle"
    _create_bundle(tmp_path, bundle_name)
    _link_backlog(tmp_path, bundle_name)

    from specfact_cli.modules.project.src import commands as project_commands

    monkeypatch.setattr(project_commands, "_fetch_backlog_graph", lambda **_kwargs: type("G", (), {"items": {}})())
    monkeypatch.setattr(project_commands, "merge_plans", lambda *_args, **_kwargs: {"merged": True})
    monkeypatch.setattr(project_commands, "find_conflicts", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(project_commands, "generate_roadmap", lambda **_kwargs: ["M1"])

    regenerate_result = runner.invoke(
        app,
        [
            "project",
            "regenerate",
            "--repo",
            str(tmp_path),
            "--bundle",
            bundle_name,
            "--no-interactive",
        ],
    )
    assert regenerate_result.exit_code == 0

    roadmap_result = runner.invoke(
        app,
        [
            "project",
            "export-roadmap",
            "--repo",
            str(tmp_path),
            "--bundle",
            bundle_name,
            "--no-interactive",
        ],
    )
    assert roadmap_result.exit_code == 0
    assert "M1" in roadmap_result.stdout


def test_project_devops_flow_complete_stage_sequence(tmp_path: Path, monkeypatch) -> None:
    """Validate full DevOps flow sequence plan→develop→review→release→monitor."""
    monkeypatch.chdir(tmp_path)
    os.environ["TEST_MODE"] = "true"
    os.environ["PR_BODY"] = "Implements #123"
    bundle_name = "integration-bundle"
    _create_bundle(tmp_path, bundle_name)
    _link_backlog(tmp_path, bundle_name)

    from specfact_cli.modules.project.src import commands as project_commands

    calls: list[str] = []
    monkeypatch.setattr(project_commands, "generate_roadmap", lambda **_kwargs: ["CP-1"])
    monkeypatch.setattr(project_commands, "_run_spec_code_alignment_check", lambda **_kwargs: {"ok": True})
    monkeypatch.setattr(project_commands, "_run_release_readiness_check", lambda **_kwargs: {"ok": True})
    monkeypatch.setattr(
        project_commands,
        "health_check",
        lambda **_kwargs: calls.append("monitor-health-check"),
    )
    monkeypatch.setattr(project_commands, "_ensure_backlog_core_loaded", lambda: None)

    sync_module = types.ModuleType("backlog_core.commands.sync")

    def _fake_sync(**_kwargs) -> None:
        calls.append("develop-sync")

    sync_module.sync = _fake_sync  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "backlog_core.commands.sync", sync_module)

    notes_module = types.ModuleType("backlog_core.commands.release_notes")

    def _fake_release_notes(**_kwargs) -> None:
        calls.append("release-notes")

    notes_module.generate_release_notes = _fake_release_notes  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "backlog_core.commands.release_notes", notes_module)

    plan_result = runner.invoke(
        app,
        [
            "project",
            "devops-flow",
            "--repo",
            str(tmp_path),
            "--bundle",
            bundle_name,
            "--stage",
            "plan",
            "--action",
            "generate-roadmap",
            "--no-interactive",
        ],
    )
    assert plan_result.exit_code == 0
    assert "CP-1" in plan_result.stdout

    develop_result = runner.invoke(
        app,
        [
            "project",
            "devops-flow",
            "--repo",
            str(tmp_path),
            "--bundle",
            bundle_name,
            "--stage",
            "develop",
            "--action",
            "sync",
            "--no-interactive",
        ],
    )
    assert develop_result.exit_code == 0

    review_result = runner.invoke(
        app,
        [
            "project",
            "devops-flow",
            "--repo",
            str(tmp_path),
            "--bundle",
            bundle_name,
            "--stage",
            "review",
            "--action",
            "validate-pr",
            "--no-interactive",
        ],
    )
    assert review_result.exit_code == 0

    release_result = runner.invoke(
        app,
        [
            "project",
            "devops-flow",
            "--repo",
            str(tmp_path),
            "--bundle",
            bundle_name,
            "--stage",
            "release",
            "--action",
            "verify",
            "--no-interactive",
        ],
    )
    assert release_result.exit_code == 0

    monitor_result = runner.invoke(
        app,
        [
            "project",
            "devops-flow",
            "--repo",
            str(tmp_path),
            "--bundle",
            bundle_name,
            "--stage",
            "monitor",
            "--action",
            "health-check",
            "--no-interactive",
        ],
    )
    assert monitor_result.exit_code == 0

    assert "develop-sync" in calls
    assert "release-notes" in calls
    assert "monitor-health-check" in calls
