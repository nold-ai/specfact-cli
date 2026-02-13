"""Dependency analyzer utilities for backlog graphs."""

from __future__ import annotations

import sys
from collections import defaultdict
from typing import Any

from beartype import beartype
from icontract import ensure, require

from backlog_core.adapters.backlog_protocol import BacklogGraphProtocol
from backlog_core.graph.models import BacklogGraph, DependencyType


@beartype
class DependencyAnalyzer:
    """Analyze dependency relationships for a backlog graph."""

    @beartype
    @require(lambda graph: len(graph.items) >= 0, "Graph must be initialized")
    def __init__(self, graph: BacklogGraph) -> None:
        self.graph = graph
        self._adjacency: dict[str, list[str]] = defaultdict(list)
        self._reverse_adjacency: dict[str, list[str]] = defaultdict(list)
        self._dependency_types: dict[tuple[str, str], DependencyType] = {}

        for dep in graph.dependencies:
            self._adjacency[dep.source_id].append(dep.target_id)
            self._reverse_adjacency[dep.target_id].append(dep.source_id)
            self._dependency_types[(dep.source_id, dep.target_id)] = dep.type

    @staticmethod
    @beartype
    @require(lambda adapter: adapter is not None, "adapter must be provided")
    @ensure(lambda result: result is None, "Must return None")
    def validate_adapter_protocol(adapter: Any) -> None:
        """Fail fast when an adapter does not support backlog graph bulk fetch methods."""
        if not isinstance(adapter, BacklogGraphProtocol):
            msg = (
                f"Adapter '{type(adapter).__name__}' does not support BacklogGraphProtocol; "
                "required methods: fetch_all_issues(project_id, filters), fetch_relationships(project_id)."
            )
            raise TypeError(msg)

    @beartype
    @ensure(lambda result: isinstance(result, dict), "Transitive closure must be returned as dict")
    def compute_transitive_closure(self) -> dict[str, list[str]]:
        closure: dict[str, list[str]] = {}
        for item_id in self.graph.items:
            seen: set[str] = set()
            self._traverse_dfs(item_id, seen)
            seen.discard(item_id)
            if seen:
                closure[item_id] = sorted(seen)
        return closure

    def _traverse_dfs(self, item_id: str, seen: set[str]) -> None:
        for neighbor in self._adjacency.get(item_id, []):
            if neighbor in seen:
                continue
            seen.add(neighbor)
            self._traverse_dfs(neighbor, seen)

    @beartype
    @ensure(lambda result: isinstance(result, list), "Cycle detection must return list")
    def detect_cycles(self) -> list[list[str]]:
        visited: set[str] = set()
        recursion_stack: set[str] = set()
        traversal_path: list[str] = []
        cycles: list[list[str]] = []

        def visit(node: str) -> None:
            visited.add(node)
            recursion_stack.add(node)
            traversal_path.append(node)

            for neighbor in self._adjacency.get(node, []):
                if neighbor not in visited:
                    visit(neighbor)
                elif neighbor in recursion_stack:
                    start = traversal_path.index(neighbor)
                    cycles.append([*traversal_path[start:], neighbor])

            traversal_path.pop()
            recursion_stack.remove(node)

        for node in self.graph.items:
            if node not in visited:
                visit(node)

        return cycles

    @beartype
    @ensure(lambda result: isinstance(result, list), "Critical path must be returned as list")
    def critical_path(self) -> list[str]:
        # Beartype/icontract wrappers add call frames; allow ample headroom for deep chains.
        required_limit = max(10000, len(self.graph.items) * 20)
        if sys.getrecursionlimit() < required_limit:
            sys.setrecursionlimit(required_limit)

        longest: list[str] = []
        memo: dict[str, list[str]] = {}
        for node in self.graph.items:
            candidate = self._longest_path_from(node, set(), memo)
            if len(candidate) > len(longest):
                longest = candidate
        return longest

    def _longest_path_from(self, node: str, visiting: set[str], memo: dict[str, list[str]]) -> list[str]:
        if node in memo:
            return memo[node]
        if node in visiting:
            return [node]

        visiting.add(node)
        best_tail: list[str] = []
        for neighbor in self._adjacency.get(node, []):
            candidate = self._longest_path_from(neighbor, visiting, memo)
            if len(candidate) > len(best_tail):
                best_tail = candidate
        visiting.remove(node)
        path = [node, *best_tail]
        memo[node] = path
        return path

    @beartype
    @require(lambda item_id: item_id.strip() != "", "item_id must be non-empty")
    @ensure(lambda result: isinstance(result, dict), "Impact analysis result must be a dict")
    def impact_analysis(self, item_id: str) -> dict[str, Any]:
        direct_dependents = sorted(set(self._reverse_adjacency.get(item_id, [])))

        transitive_dependents: set[str] = set()
        stack = list(direct_dependents)
        while stack:
            node = stack.pop()
            if node in transitive_dependents:
                continue
            transitive_dependents.add(node)
            stack.extend(self._reverse_adjacency.get(node, []))

        blockers = sorted(
            target
            for (source, target), dep_type in self._dependency_types.items()
            if source == item_id and dep_type == DependencyType.BLOCKS
        )

        return {
            "direct_dependents": direct_dependents,
            "transitive_dependents": sorted(transitive_dependents),
            "blockers": blockers,
            "estimated_impact_count": len(transitive_dependents),
        }

    @beartype
    @ensure(lambda result: isinstance(result, dict), "Coverage analysis result must be a dict")
    def coverage_analysis(self) -> dict[str, Any]:
        total_items = len(self.graph.items)
        properly_typed = sum(1 for item in self.graph.items.values() if item.effective_type().value != "custom")
        items_with_dependencies = {dep.source_id for dep in self.graph.dependencies} | {
            dep.target_id for dep in self.graph.dependencies
        }
        cycles = self.detect_cycles()

        properly_typed_pct = (properly_typed / total_items * 100.0) if total_items else 0.0
        return {
            "total_items": total_items,
            "properly_typed": properly_typed,
            "properly_typed_pct": round(properly_typed_pct, 2),
            "with_dependencies": len(items_with_dependencies),
            "orphan_count": len(self.graph.orphans),
            "cycle_count": len(cycles),
        }
