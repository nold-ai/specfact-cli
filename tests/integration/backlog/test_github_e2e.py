"""Integration-style test for backlog analyze-deps command with GitHub adapter."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from typer.testing import CliRunner


# ruff: noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "modules" / "backlog-core" / "src"))

from backlog_core.main import backlog_app

from specfact_cli.adapters.registry import AdapterRegistry


class _FakeGitHubAdapter:
    def fetch_all_issues(self, project_id: str, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        _ = project_id, filters
        return [
            {"id": "1", "key": "#1", "title": "Feature", "type": "feature", "status": "todo"},
            {"id": "2", "key": "#2", "title": "Task", "type": "task", "status": "in progress"},
        ]

    def fetch_relationships(self, project_id: str) -> list[dict[str, Any]]:
        _ = project_id
        return [{"source_id": "1", "target_id": "2", "type": "blocks"}]


def test_backlog_analyze_deps_github_flow(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    report_path = tmp_path / "report.md"
    json_path = tmp_path / "graph.json"

    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda *_args, **_kwargs: _FakeGitHubAdapter())

    result = runner.invoke(
        backlog_app,
        [
            "analyze-deps",
            "--project-id",
            "nold-ai/specfact-cli",
            "--adapter",
            "github",
            "--template",
            "github_projects",
            "--output",
            str(report_path),
            "--json-export",
            str(json_path),
        ],
    )

    assert result.exit_code == 0
    assert report_path.exists()
    assert json_path.exists()
