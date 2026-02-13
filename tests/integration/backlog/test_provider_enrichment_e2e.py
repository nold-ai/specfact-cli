"""Integration tests for provider enrichment paths used by backlog graph analysis."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from typer.testing import CliRunner

from specfact_cli.adapters.ado import AdoAdapter
from specfact_cli.adapters.github import GitHubAdapter
from specfact_cli.models.backlog_item import BacklogItem


# ruff: noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "modules" / "backlog-core" / "src"))

from backlog_core.main import backlog_app

from specfact_cli.adapters.registry import AdapterRegistry


def test_analyze_deps_uses_github_enrichment_path(tmp_path: Path, monkeypatch) -> None:
    """GitHub adapter enrichment should yield typed items with dependency edges in graph export."""
    adapter = GitHubAdapter(repo_owner="nold-ai", repo_name="specfact-cli", use_gh_cli=False)
    monkeypatch.setattr(
        adapter,
        "fetch_backlog_items",
        lambda _filters: [
            BacklogItem(
                id="1",
                provider="github",
                url="https://github.com/nold-ai/specfact-cli/issues/1",
                title="Core epic",
                body_markdown="Body",
                state="open",
                tags=["epic"],
            ),
            BacklogItem(
                id="2",
                provider="github",
                url="https://github.com/nold-ai/specfact-cli/issues/2",
                title="Implement feature",
                body_markdown="Blocked by #1",
                state="open",
                tags=["feature"],
            ),
        ],
    )
    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda *_args, **_kwargs: adapter)

    runner = CliRunner()
    json_path = tmp_path / "github_graph.json"
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
            "--json-export",
            str(json_path),
        ],
    )

    assert result.exit_code == 0
    graph = json.loads(json_path.read_text(encoding="utf-8"))
    assert len(graph["dependencies"]) >= 1
    assert any(item["type"] != "custom" for item in graph["items"].values())


def test_analyze_deps_uses_ado_enrichment_path(tmp_path: Path, monkeypatch) -> None:
    """ADO relation enrichment should produce non-custom dependency edges in graph export."""
    adapter = AdoAdapter(org="nold-ai", project="specfact-cli", api_token="test-token")
    monkeypatch.setattr(
        adapter,
        "fetch_all_issues",
        lambda _project_id, filters=None: [
            {
                "id": "100",
                "title": "Epic",
                "work_item_type": "Epic",
                "status": "active",
                "provider_fields": {
                    "relations": [
                        {
                            "rel": "System.LinkTypes.Hierarchy-Forward",
                            "url": "https://dev.azure.com/nold-ai/_apis/wit/workItems/101",
                        }
                    ]
                },
            },
            {
                "id": "101",
                "title": "Story",
                "work_item_type": "User Story",
                "status": "new",
                "provider_fields": {"relations": []},
            },
        ],
    )
    monkeypatch.setattr(AdapterRegistry, "get_adapter", lambda *_args, **_kwargs: adapter)

    runner = CliRunner()
    json_path = tmp_path / "ado_graph.json"
    result = runner.invoke(
        backlog_app,
        [
            "analyze-deps",
            "--project-id",
            "nold-ai/specfact-cli",
            "--adapter",
            "ado",
            "--template",
            "ado_scrum",
            "--json-export",
            str(json_path),
        ],
    )

    assert result.exit_code == 0
    graph = json.loads(json_path.read_text(encoding="utf-8"))
    assert len(graph["dependencies"]) >= 1
    assert any(dep["type"] != "custom" for dep in graph["dependencies"])
