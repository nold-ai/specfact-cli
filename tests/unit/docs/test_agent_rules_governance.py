from __future__ import annotations

from pathlib import Path

from tests.helpers.doc_frontmatter_types import CheckDocFrontmatterModule


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_agent_rules_index_and_checklist_exist() -> None:
    index_path = REPO_ROOT / "docs" / "agent-rules" / "INDEX.md"
    checklist_path = REPO_ROOT / "docs" / "agent-rules" / "05-non-negotiable-checklist.md"

    assert index_path.exists()
    assert checklist_path.exists()


def test_agent_rules_index_has_deterministic_bootstrap_metadata(
    check_doc_frontmatter_module: CheckDocFrontmatterModule,
) -> None:
    parse_frontmatter = check_doc_frontmatter_module.parse_frontmatter
    frontmatter = parse_frontmatter(REPO_ROOT / "docs" / "agent-rules" / "INDEX.md")
    assert isinstance(frontmatter, dict)

    applies_when = frontmatter["applies_when"]
    assert isinstance(applies_when, list)

    assert frontmatter["id"] == "agent-rules-index"
    assert frontmatter["always_load"] is True
    assert "session-bootstrap" in applies_when
    assert frontmatter["priority"] == 0


def test_non_negotiable_checklist_is_always_loaded(
    check_doc_frontmatter_module: CheckDocFrontmatterModule,
) -> None:
    parse_frontmatter = check_doc_frontmatter_module.parse_frontmatter
    frontmatter = parse_frontmatter(REPO_ROOT / "docs" / "agent-rules" / "05-non-negotiable-checklist.md")
    assert isinstance(frontmatter, dict)

    depends_on = frontmatter["depends_on"]
    assert isinstance(depends_on, list)

    assert frontmatter["id"] == "agent-rules-non-negotiable-checklist"
    assert frontmatter["always_load"] is True
    assert "agent-rules-index" in depends_on


def test_agents_references_canonical_rule_docs() -> None:
    agents_text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert "docs/agent-rules/INDEX.md" in agents_text
    assert "docs/agent-rules/05-non-negotiable-checklist.md" in agents_text
