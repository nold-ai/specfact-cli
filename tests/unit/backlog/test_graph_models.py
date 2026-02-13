"""Unit tests for backlog-core graph models."""
# ruff: noqa: E402

from __future__ import annotations

import sys
from pathlib import Path


def _add_backlog_core_to_path() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    module_src = repo_root / "modules" / "backlog-core" / "src"
    sys.path.insert(0, str(module_src))


_add_backlog_core_to_path()

from backlog_core.graph.models import BacklogGraph, BacklogItem, Dependency, DependencyType, ItemType


def test_backlog_item_effective_type_uses_inferred_when_confident() -> None:
    item = BacklogItem(
        id="1",
        key="ABC-1",
        title="Example",
        type=ItemType.STORY,
        inferred_type=ItemType.FEATURE,
        confidence=0.9,
    )

    assert item.effective_type() == ItemType.FEATURE


def test_backlog_item_effective_type_falls_back_to_declared_type() -> None:
    item = BacklogItem(
        id="1",
        key="ABC-1",
        title="Example",
        type=ItemType.STORY,
        inferred_type=ItemType.FEATURE,
        confidence=0.2,
    )

    assert item.effective_type() == ItemType.STORY


def test_dependency_model_accepts_normalized_types() -> None:
    dep = Dependency(source_id="1", target_id="2", type=DependencyType.BLOCKS)

    assert dep.type == DependencyType.BLOCKS


def test_backlog_graph_json_roundtrip() -> None:
    item = BacklogItem(id="1", key="ABC-1", title="Example", type=ItemType.TASK)
    dep = Dependency(source_id="1", target_id="2", type=DependencyType.RELATES_TO)
    graph = BacklogGraph(
        items={"1": item},
        dependencies=[dep],
        provider="github",
        project_key="nold-ai/specfact-cli",
        transitive_closure={"1": ["2"]},
        cycles_detected=[],
        orphans=["1"],
    )

    payload = graph.to_json()
    restored = BacklogGraph.from_json(payload)

    assert restored.provider == "github"
    assert restored.project_key == "nold-ai/specfact-cli"
    assert restored.items["1"].title == "Example"
    assert restored.dependencies[0].type == DependencyType.RELATES_TO
    assert restored.transitive_closure["1"] == ["2"]
    assert restored.orphans == ["1"]
