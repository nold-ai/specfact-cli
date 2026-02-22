"""Integration-style tests for backlog sync command."""

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


class _FakeGitHubSyncAdapter:
    def fetch_all_issues(self, project_id: str, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        _ = project_id, filters
        return [
            {"id": "1", "key": "#1", "title": "Feature", "type": "feature", "status": "done"},
            {"id": "2", "key": "#2", "title": "Task", "type": "task", "status": "in progress"},
        ]

    def fetch_relationships(self, project_id: str) -> list[dict[str, Any]]:
        _ = project_id
        return [{"source_id": "1", "target_id": "2", "type": "blocks"}]

    def create_issue(self, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        _ = project_id, payload
        return {"id": "3", "key": "#3", "url": "https://example.test/issues/3"}


def test_backlog_sync_generates_plan_and_updates_baseline(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    baseline_file = tmp_path / ".specfact" / "backlog-baseline.json"
    baseline_file.parent.mkdir(parents=True, exist_ok=True)
    baseline_file.write_text(
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

    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda *_args, **_kwargs: _FakeGitHubSyncAdapter())
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        backlog_app,
        [
            "sync",
            "--project-id",
            "nold-ai/specfact-cli",
            "--adapter",
            "github",
            "--baseline-file",
            str(baseline_file),
            "--template",
            "github_projects",
            "--output-format",
            "plan",
        ],
    )

    assert result.exit_code == 0
    assert baseline_file.exists()
    plans_dir = tmp_path / ".specfact" / "plans"
    assert plans_dir.exists()
    assert list(plans_dir.glob("backlog-*.yaml"))
