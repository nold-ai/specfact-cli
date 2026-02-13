"""Unit tests for provider-specific enrichment used by backlog dependency analysis."""

from __future__ import annotations

import sys
from pathlib import Path


# ruff: noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "modules" / "backlog-core" / "src"))
sys.path.insert(0, str(REPO_ROOT / "src"))

from backlog_core.analyzers.dependency import DependencyAnalyzer
from backlog_core.graph.builder import BacklogGraphBuilder

from specfact_cli.adapters.ado import AdoAdapter
from specfact_cli.adapters.github import GitHubAdapter
from specfact_cli.models.backlog_item import BacklogItem


def test_github_fetch_all_issues_enriches_normalized_item_type(monkeypatch) -> None:
    """GitHub fetch_all_issues should include normalized type values for builder mapping."""
    adapter = GitHubAdapter(repo_owner="nold-ai", repo_name="specfact-cli", use_gh_cli=False)

    items = [
        BacklogItem(
            id="101",
            provider="github",
            url="https://github.com/nold-ai/specfact-cli/issues/101",
            title="Add dependency model",
            body_markdown="Body",
            state="open",
            tags=["Type: Feature"],
        ),
        BacklogItem(
            id="102",
            provider="github",
            url="https://github.com/nold-ai/specfact-cli/issues/102",
            title="[Bug] Fix parser",
            body_markdown="Body",
            state="open",
            tags=[],
        ),
    ]
    monkeypatch.setattr(adapter, "fetch_backlog_items", lambda _filters: items)

    enriched = adapter.fetch_all_issues("nold-ai/specfact-cli")

    assert enriched[0]["type"] == "feature"
    assert enriched[1]["type"] == "bug"


def test_github_fetch_relationships_extracts_blocks_and_related(monkeypatch) -> None:
    """GitHub fetch_relationships should normalize body references into dependency edges."""
    adapter = GitHubAdapter(repo_owner="nold-ai", repo_name="specfact-cli", use_gh_cli=False)
    monkeypatch.setattr(
        adapter,
        "fetch_all_issues",
        lambda _project_id, filters=None: [
            {
                "id": "10",
                "body_markdown": "Blocks #11\nBlocked by #12\nRelated to #13",
                "provider_fields": {},
            }
        ],
    )

    relationships = adapter.fetch_relationships("nold-ai/specfact-cli")
    edges = {(edge["source_id"], edge["target_id"], edge["type"]) for edge in relationships}

    assert ("10", "11", "blocks") in edges
    assert ("12", "10", "blocks") in edges
    assert ("10", "13", "relates") in edges


def test_ado_fetch_relationships_maps_forward_and_reverse_links(monkeypatch) -> None:
    """ADO fetch_relationships should preserve hierarchy and blocker semantics."""
    adapter = AdoAdapter(org="nold-ai", project="specfact-cli", api_token="test-token")
    monkeypatch.setattr(
        adapter,
        "fetch_all_issues",
        lambda _project_id, filters=None: [
            {
                "id": "100",
                "provider_fields": {
                    "relations": [
                        {
                            "rel": "System.LinkTypes.Hierarchy-Forward",
                            "url": "https://dev.azure.com/nold-ai/_apis/wit/workItems/101",
                        },
                        {
                            "rel": "System.LinkTypes.Dependency-Reverse",
                            "url": "https://dev.azure.com/nold-ai/_apis/wit/workItems/200",
                        },
                        {
                            "rel": "System.LinkTypes.Related",
                            "url": "https://dev.azure.com/nold-ai/_apis/wit/workItems/300",
                        },
                    ]
                },
            }
        ],
    )

    relationships = adapter.fetch_relationships("nold-ai/specfact-cli")
    edges = {(edge["source_id"], edge["target_id"], edge["type"]) for edge in relationships}

    assert ("100", "101", "parent") in edges
    assert ("200", "100", "blocks") in edges
    assert ("100", "300", "relates") in edges


def test_provider_enrichment_improves_typed_and_dependency_coverage(monkeypatch) -> None:
    """Enriched provider outputs should yield non-zero typed/dependency coverage."""
    github = GitHubAdapter(repo_owner="nold-ai", repo_name="specfact-cli", use_gh_cli=False)
    monkeypatch.setattr(
        github,
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

    items = github.fetch_all_issues("nold-ai/specfact-cli")
    relationships = github.fetch_relationships("nold-ai/specfact-cli")

    graph = (
        BacklogGraphBuilder(provider="github", template_name="github_projects")
        .add_items(items)
        .add_dependencies(relationships)
        .build()
    )
    coverage = DependencyAnalyzer(graph).coverage_analysis()

    assert coverage["properly_typed"] >= 2
    assert coverage["with_dependencies"] >= 1
