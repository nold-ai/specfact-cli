"""Integration-style test for backlog trace-impact command with ADO adapter."""

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


class _FakeAdoAdapter:
    def fetch_all_issues(self, project_id: str, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        _ = project_id, filters
        return [
            {"id": "100", "key": "ADO-100", "title": "Epic", "type": "Epic", "status": "New"},
            {
                "id": "101",
                "key": "ADO-101",
                "title": "Story",
                "type": "User Story",
                "status": "Active",
            },
        ]

    def fetch_relationships(self, project_id: str) -> list[dict[str, Any]]:
        _ = project_id
        return [{"source_id": "100", "target_id": "101", "type": "blocks"}]


def test_backlog_trace_impact_ado_flow(monkeypatch) -> None:
    runner = CliRunner()

    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda *_args, **_kwargs: _FakeAdoAdapter())

    result = runner.invoke(
        backlog_app,
        [
            "trace-impact",
            "100",
            "--project-id",
            "demo/project",
            "--adapter",
            "ado",
            "--template",
            "ado_scrum",
        ],
    )

    assert result.exit_code == 0
    assert "Estimated impact count" in result.stdout
