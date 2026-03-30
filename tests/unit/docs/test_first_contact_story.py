"""Validate first-contact messaging across the core repo entry points.

These tests ensure the README, docs landing page, and contributor guidance all
present the same canonical product story and onboarding order.
"""

import re
from pathlib import Path
from urllib.parse import urlparse

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
README = REPO_ROOT / "README.md"
DOCS_INDEX = REPO_ROOT / "docs" / "index.md"
CONTRIBUTING = REPO_ROOT / "CONTRIBUTING.md"

ABSOLUTE_URL_RE = re.compile(r"https?://[^\s)>'\"`]+")


@pytest.fixture(scope="module", autouse=True)
def _require_entrypoint_files() -> None:
    """Skip the module if the docs entrypoint files are not present."""

    if not REPO_ROOT.exists():
        pytest.skip(f"Repository root missing: expected at {REPO_ROOT}", allow_module_level=True)
    if not README.is_file():
        pytest.skip(f"README.md missing: expected at {README}", allow_module_level=True)
    if not DOCS_INDEX.is_file():
        pytest.skip(f"docs/index.md missing: expected at {DOCS_INDEX}", allow_module_level=True)
    if not CONTRIBUTING.is_file():
        pytest.skip(f"CONTRIBUTING.md missing: expected at {CONTRIBUTING}", allow_module_level=True)


def _read(path: Path) -> str:
    """Return the UTF-8 text contents of a repository file.

    Args:
        path: Path to the file to read.

    Returns:
        File contents as a string.
    """

    return path.read_text(encoding="utf-8")


def _assert_question_order(content: str, questions: list[str], surface: str) -> None:
    """Assert that the first-contact questions appear in increasing order.

    Args:
        content: Text content to inspect.
        questions: Ordered question strings that must appear in sequence.
        surface: Human-readable name of the file or surface being inspected.
    """

    indices: list[int] = []
    for question in questions:
        index = content.find(question)
        assert index != -1, f"Missing question {question!r} in {surface}"
        indices.append(index)

    assert indices == sorted(indices), f"Questions are out of order in {surface}: {questions}"


def _assert_contains_url_host(content: str, host: str, surface: str) -> None:
    """Assert that a surface contains at least one absolute URL for the expected host.

    Args:
        content: Text content to inspect.
        host: Expected URL host name.
        surface: Human-readable name of the file or surface being inspected.
    """

    found_hosts = {urlparse(match.group(0).rstrip(".,;:")).netloc for match in ABSOLUTE_URL_RE.finditer(content)}
    assert host in found_hosts, f"Missing URL host {host!r} in {surface}; found hosts: {sorted(found_hosts)}"


def _assert_contains_any_phrase(content: str, phrases: tuple[str, ...], message: str) -> None:
    """Assert that at least one of the candidate phrases appears in the content."""

    lowered = content.lower()
    assert any(phrase in lowered for phrase in phrases), message


def test_readme_leads_with_validation_and_alignment_story() -> None:
    readme = _read(README)
    readme_lower = readme.lower()
    questions = [
        "What is SpecFact?",
        "Why does it exist?",
        "Why should I use it?",
        "What do I get?",
        "How do I get started?",
    ]

    assert "validation and alignment layer" in readme
    _assert_question_order(readme, questions, "README.md")
    _assert_contains_any_phrase(
        readme_lower,
        ("ai-assisted", "vibe-coded", "ai-generated"),
        "README.md must explain AI-assisted validation pressure in the why-story.",
    )
    _assert_contains_any_phrase(
        readme_lower,
        ("brownfield", "reverse-engineer", "reverse-engineered"),
        "README.md must explain the brownfield reverse-engineering pressure.",
    )
    _assert_contains_any_phrase(
        readme_lower,
        ("i wanted x but got y", "backlog/spec/code drift", "drift between backlog"),
        "README.md must explain backlog/spec/code drift as a reason SpecFact exists.",
    )
    _assert_contains_any_phrase(
        readme_lower,
        ("policy enforcement", "enterprise policy", "ci/cd", "shared rules"),
        "README.md must explain team and enterprise policy consistency pressure.",
    )


def test_readme_prioritizes_fast_start_over_docs_topology() -> None:
    readme = _read(README)

    start_match = re.search(r"^#+\s*Start Here", readme, re.MULTILINE)
    topology_match = re.search(r"^#+\s*Documentation Topology", readme, re.MULTILINE)
    assert start_match is not None, "Missing Start Here heading in README.md"
    assert topology_match is not None, "Missing Documentation Topology heading in README.md"
    start_idx = start_match.start()
    topology_idx = topology_match.start()
    assert start_idx < topology_idx


def test_readme_routes_users_by_outcome() -> None:
    readme = _read(README)
    readme_lower = readme.lower()

    assert "## Choose Your Path" in readme
    assert "Greenfield and AI-assisted delivery" in readme
    assert "Brownfield and reverse engineering" in readme
    assert "Backlog to code alignment" in readme
    _assert_contains_any_phrase(
        readme_lower,
        ("govern", "policy enforcement", "team and policy enforcement"),
        "README.md must route users toward team and enterprise policy enforcement outcomes.",
    )


def test_docs_index_matches_first_contact_story() -> None:
    docs_index = _read(DOCS_INDEX)
    docs_index_lower = docs_index.lower()
    questions = [
        "What is SpecFact?",
        "Why does it exist?",
        "Why should I use it?",
        "What do I get?",
        "How to get started",
    ]

    assert "validation and alignment layer" in docs_index
    _assert_question_order(docs_index, questions, "docs/index.md")
    _assert_contains_url_host(docs_index, "modules.specfact.io", "docs/index.md")
    _assert_contains_any_phrase(
        docs_index_lower,
        ("brownfield", "legacy code", "existing systems"),
        "docs/index.md must describe the brownfield path.",
    )
    _assert_contains_any_phrase(
        docs_index_lower,
        ("spec-first", "openspec", "spec-kit"),
        "docs/index.md must explain the spec-first handoff for brownfield workflows.",
    )
    _assert_contains_any_phrase(
        docs_index_lower,
        ("default starting point", "start here before jumping", "start here before"),
        "docs/index.md must orient users that core docs are the default starting point.",
    )
    _assert_contains_any_phrase(
        docs_index_lower,
        ("ai-assisted", "vibe-coded", "validation layer"),
        "docs/index.md must explain AI-assisted validation pressure in the why-story.",
    )
    _assert_contains_any_phrase(
        docs_index_lower,
        ("i wanted x but got y", "backlog language", "backlog/spec/code"),
        "docs/index.md must explain backlog/spec/code drift as a reason SpecFact exists.",
    )
    _assert_contains_any_phrase(
        docs_index_lower,
        ("policy enforcement", "organizations need a path", "developers, ai ides, and ci/cd"),
        "docs/index.md must explain team and enterprise policy consistency pressure.",
    )


def test_contributing_guidance_mentions_entrypoint_story_hierarchy() -> None:
    contributing = _read(CONTRIBUTING)
    questions = [
        "What is SpecFact?",
        "Why does it exist?",
        "Why should I use it?",
        "What do I get?",
        "How do I get started?",
    ]

    assert "first-contact" in contributing
    _assert_question_order(contributing, questions, "CONTRIBUTING.md")
