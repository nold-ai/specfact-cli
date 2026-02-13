"""Unit tests for DependencyAnalyzer."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path


# ruff: noqa: E402


def _add_backlog_core_to_path() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    module_src = repo_root / "modules" / "backlog-core" / "src"
    sys.path.insert(0, str(module_src))


_add_backlog_core_to_path()

from backlog_core.analyzers.dependency import DependencyAnalyzer
from backlog_core.graph.builder import BacklogGraphBuilder
from backlog_core.graph.models import BacklogGraph, BacklogItem, Dependency, DependencyType, ItemType


def _load_fixture(name: str) -> dict[str, object]:
    fixture = Path(__file__).resolve().parent / "fixtures" / name
    return json.loads(fixture.read_text(encoding="utf-8"))


def _build_linear_graph() -> BacklogGraph:
    items = {
        "1": BacklogItem(id="1", key="A", title="A", type=ItemType.FEATURE),
        "2": BacklogItem(id="2", key="B", title="B", type=ItemType.STORY),
        "3": BacklogItem(id="3", key="C", title="C", type=ItemType.TASK),
    }
    deps = [
        Dependency(source_id="1", target_id="2", type=DependencyType.BLOCKS),
        Dependency(source_id="2", target_id="3", type=DependencyType.BLOCKS),
    ]
    return BacklogGraph(items=items, dependencies=deps, provider="github", project_key="repo")


def _build_large_chain_graph(node_count: int = 1200) -> BacklogGraph:
    items = {
        str(i): BacklogItem(id=str(i), key=f"K-{i}", title=f"Item {i}", type=ItemType.TASK) for i in range(node_count)
    }
    deps = [
        Dependency(source_id=str(i), target_id=str(i + 1), type=DependencyType.BLOCKS) for i in range(node_count - 1)
    ]
    return BacklogGraph(items=items, dependencies=deps, provider="github", project_key="repo")


def test_compute_transitive_closure() -> None:
    analyzer = DependencyAnalyzer(_build_linear_graph())

    closure = analyzer.compute_transitive_closure()

    assert closure["1"] == ["2", "3"]


def test_detect_cycles_with_fixture() -> None:
    sample = _load_fixture("cycles_fixture.json")
    graph = (
        BacklogGraphBuilder("github", "github_projects")
        .add_items(sample["items"])
        .add_dependencies(sample["relationships"])
        .build()
    )  # type: ignore[index]

    analyzer = DependencyAnalyzer(graph)
    cycles = analyzer.detect_cycles()

    assert cycles


def test_critical_path_prefers_longest_chain() -> None:
    analyzer = DependencyAnalyzer(_build_linear_graph())

    assert analyzer.critical_path() == ["1", "2", "3"]


def test_critical_path_handles_large_graph_under_one_second() -> None:
    analyzer = DependencyAnalyzer(_build_large_chain_graph())

    started_at = time.perf_counter()
    path = analyzer.critical_path()
    elapsed = time.perf_counter() - started_at

    assert len(path) == 1200
    assert elapsed < 1.0


def test_impact_analysis_reports_dependents_and_blockers() -> None:
    analyzer = DependencyAnalyzer(_build_linear_graph())

    impact = analyzer.impact_analysis("2")

    assert impact["direct_dependents"] == ["1"]
    assert impact["transitive_dependents"] == ["1"]
    assert impact["blockers"] == ["3"]
    assert impact["estimated_impact_count"] == 1


def test_coverage_analysis_includes_cycle_and_orphan_counts() -> None:
    graph = _build_linear_graph()
    graph.orphans = ["1"]
    analyzer = DependencyAnalyzer(graph)

    metrics = analyzer.coverage_analysis()

    assert metrics["total_items"] == 3
    assert metrics["properly_typed"] == 3
    assert metrics["with_dependencies"] == 3
    assert metrics["orphan_count"] == 1
    assert metrics["cycle_count"] == 0
