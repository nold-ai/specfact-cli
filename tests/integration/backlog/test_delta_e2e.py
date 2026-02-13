"""Integration-style tests for backlog delta subcommand suite."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from typer.testing import CliRunner


# ruff: noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "modules" / "backlog-core" / "src"))

from backlog_core.main import backlog_app

from specfact_cli.adapters.registry import AdapterRegistry


class _FakeDeltaAdapter:
    def fetch_all_issues(self, project_id: str, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        _ = project_id, filters
        return [
            {"id": "1", "key": "#1", "title": "Feature", "type": "feature", "status": "done"},
            {"id": "2", "key": "#2", "title": "Task", "type": "task", "status": "in progress"},
        ]

    def fetch_relationships(self, project_id: str) -> list[dict[str, Any]]:
        _ = project_id
        return [{"source_id": "1", "target_id": "2", "type": "blocks"}]


def _write_baseline(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "provider": "github",
                "project_key": "nold-ai/specfact-cli",
                "items": {
                    "1": {
                        "id": "1",
                        "key": "#1",
                        "title": "Feature",
                        "type": "feature",
                        "status": "todo",
                    }
                },
                "dependencies": [],
            }
        ),
        encoding="utf-8",
    )


def test_backlog_delta_commands_execute_for_status_impact_cost_and_rollback(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    baseline_file = tmp_path / ".specfact" / "backlog-baseline.json"
    _write_baseline(baseline_file)

    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda *_args, **_kwargs: _FakeDeltaAdapter())

    status_result = runner.invoke(
        backlog_app,
        [
            "delta",
            "status",
            "--project-id",
            "nold-ai/specfact-cli",
            "--adapter",
            "github",
            "--baseline-file",
            str(baseline_file),
            "--template",
            "github_projects",
        ],
    )
    assert status_result.exit_code == 0

    impact_result = runner.invoke(
        backlog_app,
        [
            "delta",
            "impact",
            "2",
            "--project-id",
            "nold-ai/specfact-cli",
            "--adapter",
            "github",
            "--template",
            "github_projects",
        ],
    )
    assert impact_result.exit_code == 0

    cost_result = runner.invoke(
        backlog_app,
        [
            "delta",
            "cost-estimate",
            "--project-id",
            "nold-ai/specfact-cli",
            "--adapter",
            "github",
            "--baseline-file",
            str(baseline_file),
            "--template",
            "github_projects",
        ],
    )
    assert cost_result.exit_code == 0

    rollback_result = runner.invoke(
        backlog_app,
        [
            "delta",
            "rollback-analysis",
            "--project-id",
            "nold-ai/specfact-cli",
            "--adapter",
            "github",
            "--baseline-file",
            str(baseline_file),
            "--template",
            "github_projects",
        ],
    )
    assert rollback_result.exit_code == 0
