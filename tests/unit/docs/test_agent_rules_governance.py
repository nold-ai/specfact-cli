from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]


def _read_frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    _, body = text.split("---\n", 1)
    frontmatter, _ = body.split("\n---\n", 1)
    loaded = yaml.safe_load(frontmatter)
    assert isinstance(loaded, dict)
    return loaded


def test_agent_rules_index_and_checklist_exist() -> None:
    index_path = REPO_ROOT / "docs" / "agent-rules" / "INDEX.md"
    checklist_path = REPO_ROOT / "docs" / "agent-rules" / "05-non-negotiable-checklist.md"

    assert index_path.exists()
    assert checklist_path.exists()


def test_agent_rules_index_has_deterministic_bootstrap_metadata() -> None:
    frontmatter = _read_frontmatter(REPO_ROOT / "docs" / "agent-rules" / "INDEX.md")
    applies_when = frontmatter["applies_when"]
    assert isinstance(applies_when, list)

    assert frontmatter["id"] == "agent-rules-index"
    assert frontmatter["always_load"] is True
    assert "session-bootstrap" in applies_when
    assert frontmatter["priority"] == 0


def test_non_negotiable_checklist_is_always_loaded() -> None:
    frontmatter = _read_frontmatter(REPO_ROOT / "docs" / "agent-rules" / "05-non-negotiable-checklist.md")
    depends_on = frontmatter["depends_on"]
    assert isinstance(depends_on, list)

    assert frontmatter["id"] == "agent-rules-non-negotiable-checklist"
    assert frontmatter["always_load"] is True
    assert "agent-rules-index" in depends_on


def test_agents_references_canonical_rule_docs() -> None:
    agents_text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert "docs/agent-rules/INDEX.md" in agents_text
    assert "docs/agent-rules/05-non-negotiable-checklist.md" in agents_text
