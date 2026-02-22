"""Unit tests for backlog graph protocol registration and conformance."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


# ruff: noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "modules" / "backlog-core" / "src"))
sys.path.insert(0, str(REPO_ROOT / "src"))

from backlog_core.adapters.backlog_protocol import BacklogGraphProtocol
from backlog_core.analyzers.dependency import DependencyAnalyzer

from specfact_cli.adapters.ado import AdoAdapter
from specfact_cli.adapters.github import GitHubAdapter
from specfact_cli.registry.bridge_registry import BRIDGE_PROTOCOL_REGISTRY


class _ValidAdapter:
    def fetch_all_issues(self, project_id: str, filters: dict | None = None) -> list[dict]:
        _ = project_id, filters
        return []

    def fetch_relationships(self, project_id: str) -> list[dict]:
        _ = project_id
        return []

    def create_issue(self, project_id: str, payload: dict) -> dict:
        _ = project_id, payload
        return {"id": "1", "key": "1", "url": "https://example.test/1"}


class _InvalidAdapter:
    def fetch_all_issues(self, project_id: str, filters: dict | None = None) -> list[dict]:
        _ = project_id, filters
        return []


def test_backlog_graph_protocol_is_registered() -> None:
    protocol = BRIDGE_PROTOCOL_REGISTRY.get_protocol("backlog_graph")

    assert protocol is BacklogGraphProtocol


def test_bridge_registry_resolves_adapter_implementations() -> None:
    github_impl = BRIDGE_PROTOCOL_REGISTRY.get_implementation("backlog_graph", "github")
    ado_impl = BRIDGE_PROTOCOL_REGISTRY.get_implementation("backlog_graph", "ado")

    assert github_impl is GitHubAdapter
    assert ado_impl is AdoAdapter


def test_runtime_protocol_conformance_for_adapters() -> None:
    assert isinstance(GitHubAdapter(), BacklogGraphProtocol)
    assert isinstance(AdoAdapter(), BacklogGraphProtocol)


def test_dependency_analyzer_fail_fast_for_missing_protocol() -> None:
    with pytest.raises(TypeError):
        DependencyAnalyzer.validate_adapter_protocol(_InvalidAdapter())


def test_dependency_analyzer_accepts_protocol_adapter() -> None:
    DependencyAnalyzer.validate_adapter_protocol(_ValidAdapter())
