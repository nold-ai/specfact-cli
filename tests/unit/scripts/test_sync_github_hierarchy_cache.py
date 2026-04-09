"""Tests for scripts/sync_github_hierarchy_cache.py."""

from __future__ import annotations

import importlib.util
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, TypedDict


class IssueOptions(TypedDict, total=False):
    """Optional test issue fields."""

    labels: list[str]
    summary: str
    parent: tuple[int, str]
    children: list[tuple[int, str]]
    updated_at: str


@lru_cache(maxsize=1)
def _load_script_module() -> Any:
    """Load scripts/sync_github_hierarchy_cache.py as a Python module."""
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "sync_github_hierarchy_cache.py"
    spec = importlib.util.spec_from_file_location("sync_github_hierarchy_cache", script_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load script module at {script_path}")
    sys.modules.pop(spec.name, None)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_issue(
    module: Any,
    *,
    number: int,
    title: str,
    issue_type: str,
    options: IssueOptions | None = None,
) -> Any:
    """Create a HierarchyIssue instance for tests."""
    issue_options = options or {}
    children = issue_options.get("children", [])
    child_links = [
        module.IssueLink(number=child_number, title=child_title, url=f"https://example.test/issues/{child_number}")
        for child_number, child_title in children
    ]

    parent_link = None
    parent = issue_options.get("parent")
    if parent is not None:
        parent_number, parent_title = parent
        parent_link = module.IssueLink(
            number=parent_number,
            title=parent_title,
            url=f"https://example.test/issues/{parent_number}",
        )

    return module.HierarchyIssue(
        number=number,
        title=title,
        url=f"https://example.test/issues/{number}",
        issue_type=issue_type,
        labels=issue_options.get("labels", []),
        summary=issue_options.get("summary", ""),
        updated_at=issue_options.get("updated_at", "2026-04-09T08:00:00Z"),
        parent=parent_link,
        children=child_links,
    )


def test_compute_hierarchy_fingerprint_is_order_independent() -> None:
    """Fingerprinting should stay stable regardless of input ordering."""
    module = _load_script_module()

    epic = _make_issue(
        module,
        number=485,
        title="[Epic] Governance",
        issue_type="Epic",
        options={
            "labels": ["openspec", "Epic"],
            "summary": "Governance epic.",
            "children": [(486, "[Feature] Alignment")],
        },
    )
    feature = _make_issue(
        module,
        number=486,
        title="[Feature] Alignment",
        issue_type="Feature",
        options={
            "labels": ["Feature", "openspec"],
            "summary": "Alignment feature.",
            "parent": (485, "[Epic] Governance"),
        },
    )

    first = module.compute_hierarchy_fingerprint([epic, feature])
    second = module.compute_hierarchy_fingerprint([feature, epic])

    assert first == second


def test_extract_summary_skips_heading_only_lines() -> None:
    """Summary extraction should skip markdown section headers."""
    module = _load_script_module()
    extract_summary = module._extract_summary  # pylint: disable=protected-access

    summary = extract_summary("## Why\n\nThis cache avoids repeated GitHub lookups.")

    assert summary == "This cache avoids repeated GitHub lookups."


def test_default_paths_use_ephemeral_specfact_backlog_cache() -> None:
    """Default cache files should live in ignored .specfact/backlog storage."""
    module = _load_script_module()

    assert str(module.DEFAULT_OUTPUT_PATH) == ".specfact/backlog/github_hierarchy_cache.md"
    assert str(module.DEFAULT_STATE_PATH) == ".specfact/backlog/github_hierarchy_cache_state.json"


def test_render_cache_markdown_groups_epics_and_features() -> None:
    """Rendered markdown should be deterministic and grouped by issue type."""
    module = _load_script_module()

    issues = [
        _make_issue(
            module,
            number=486,
            title="[Feature] Alignment",
            issue_type="Feature",
            options={
                "labels": ["openspec", "Feature"],
                "summary": "Alignment feature.",
                "parent": (485, "[Epic] Governance"),
            },
        ),
        _make_issue(
            module,
            number=485,
            title="[Epic] Governance",
            issue_type="Epic",
            options={
                "labels": ["Epic", "openspec"],
                "summary": "Governance epic.",
                "children": [(486, "[Feature] Alignment")],
            },
        ),
    ]

    rendered = module.render_cache_markdown(
        repo_full_name="nold-ai/specfact-cli",
        issues=issues,
        generated_at="2026-04-09T08:30:00Z",
        fingerprint="abc123",
    )

    assert "# GitHub Hierarchy Cache" in rendered
    assert "## Epics" in rendered
    assert "## Features" in rendered
    assert rendered.index("### #485") < rendered.index("### #486")
    assert "- Parent: none" in rendered
    assert "- Parent: #485 [Epic] Governance" in rendered
    assert "- Labels: Epic, openspec" in rendered
    assert "- Labels: Feature, openspec" in rendered


def test_sync_cache_skips_write_when_fingerprint_is_unchanged(monkeypatch: Any, tmp_path: Path) -> None:
    """sync_cache should not rewrite output when the fingerprint matches state."""
    module = _load_script_module()

    output_path = tmp_path / "GITHUB_HIERARCHY_CACHE.md"
    state_path = tmp_path / ".github_hierarchy_cache_state.json"
    output_path.write_text("unchanged cache\n", encoding="utf-8")
    state_path.write_text('{"fingerprint":"same"}', encoding="utf-8")

    issues = [
        _make_issue(
            module,
            number=485,
            title="[Epic] Governance",
            issue_type="Epic",
            options={
                "labels": ["Epic"],
                "summary": "Governance epic.",
            },
        )
    ]

    def _fake_fetch(*, repo_owner: str, repo_name: str, fingerprint_only: bool) -> list[Any]:
        assert repo_owner == "nold-ai"
        assert repo_name == "specfact-cli"
        assert fingerprint_only is True
        return issues

    def _same_fingerprint(_: list[Any]) -> str:
        return "same"

    monkeypatch.setattr(module, "fetch_hierarchy_issues", _fake_fetch)
    monkeypatch.setattr(module, "compute_hierarchy_fingerprint", _same_fingerprint)

    result = module.sync_cache(
        repo_owner="nold-ai",
        repo_name="specfact-cli",
        output_path=output_path,
        state_path=state_path,
    )

    assert result.changed is False
    assert result.issue_count == 1
    assert output_path.read_text(encoding="utf-8") == "unchanged cache\n"
