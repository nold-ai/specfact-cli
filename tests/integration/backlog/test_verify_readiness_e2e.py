"""Integration-style test for verify-readiness command."""

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


class _FakeVerifyAdapter:
    def fetch_all_issues(self, project_id: str, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        _ = project_id, filters
        return [
            {"id": "100", "key": "A-100", "title": "Epic", "type": "epic", "status": "done"},
            {"id": "101", "key": "A-101", "title": "Story", "type": "story", "status": "done"},
            {"id": "102", "key": "A-102", "title": "Task", "type": "task", "status": "done"},
        ]

    def fetch_relationships(self, project_id: str) -> list[dict[str, Any]]:
        _ = project_id
        return [
            {"source_id": "100", "target_id": "101", "type": "parent_child"},
            {"source_id": "101", "target_id": "102", "type": "relates_to"},
        ]

    def create_issue(self, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        _ = project_id, payload
        return {"id": "103", "key": "A-103", "url": "https://example.test/workitems/103"}


def test_verify_readiness_returns_ready_exit_code(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda *_args, **_kwargs: _FakeVerifyAdapter())

    result = runner.invoke(
        backlog_app,
        [
            "verify-readiness",
            "--project-id",
            "demo/project",
            "--adapter",
            "github",
            "--target-items",
            "100,101",
            "--template",
            "github_projects",
        ],
    )

    assert result.exit_code == 0
    assert "READY" in result.stdout


class _FakeVerifyBlockedAdapter(_FakeVerifyAdapter):
    def fetch_relationships(self, project_id: str) -> list[dict[str, Any]]:
        _ = project_id
        return [
            {"source_id": "100", "target_id": "101", "type": "parent_child"},
            {"source_id": "101", "target_id": "102", "type": "blocks"},
        ]


def test_verify_readiness_returns_blocked_exit_code(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda *_args, **_kwargs: _FakeVerifyBlockedAdapter())

    result = runner.invoke(
        backlog_app,
        [
            "verify-readiness",
            "--project-id",
            "demo/project",
            "--adapter",
            "github",
            "--target-items",
            "100,101",
            "--template",
            "github_projects",
        ],
    )

    assert result.exit_code == 1
    assert "BLOCKED" in result.stdout
