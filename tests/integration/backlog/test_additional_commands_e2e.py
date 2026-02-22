"""Integration-style tests for additional backlog commands."""

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


class _FakeBacklogAdapter:
    def fetch_all_issues(self, project_id: str, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        _ = project_id, filters
        return [
            {"id": "1", "key": "FEATURE-1", "title": "Feature one", "type": "feature", "status": "done"},
            {"id": "2", "key": "TASK-2", "title": "Task two", "type": "task", "status": "in progress"},
        ]

    def fetch_relationships(self, project_id: str) -> list[dict[str, Any]]:
        _ = project_id
        return [{"source_id": "1", "target_id": "2", "type": "blocks"}]

    def create_issue(self, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        _ = project_id, payload
        return {"id": "3", "key": "TASK-3", "url": "https://example.test/issues/3"}


def _write_baseline(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "provider": "github",
                "project_key": "demo/project",
                "items": {
                    "1": {
                        "id": "1",
                        "key": "FEATURE-1",
                        "title": "Feature one",
                        "type": "feature",
                        "status": "todo",
                    }
                },
                "dependencies": [],
            }
        ),
        encoding="utf-8",
    )


def test_backlog_additional_commands_diff_promote_and_release_notes(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    baseline_file = tmp_path / ".specfact" / "backlog-baseline.json"
    _write_baseline(baseline_file)
    release_notes = tmp_path / "release-notes.md"

    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda *_args, **_kwargs: _FakeBacklogAdapter())

    diff_result = runner.invoke(
        backlog_app,
        [
            "diff",
            "--project-id",
            "demo/project",
            "--adapter",
            "github",
            "--baseline-file",
            str(baseline_file),
            "--template",
            "github_projects",
        ],
    )
    assert diff_result.exit_code == 0

    promote_result = runner.invoke(
        backlog_app,
        [
            "promote",
            "--project-id",
            "demo/project",
            "--adapter",
            "github",
            "--item-id",
            "2",
            "--to-status",
            "done",
            "--template",
            "github_projects",
        ],
    )
    assert promote_result.exit_code == 0

    release_result = runner.invoke(
        backlog_app,
        [
            "generate-release-notes",
            "--project-id",
            "demo/project",
            "--adapter",
            "github",
            "--output",
            str(release_notes),
            "--template",
            "github_projects",
        ],
    )
    assert release_result.exit_code == 0
    assert release_notes.exists()
