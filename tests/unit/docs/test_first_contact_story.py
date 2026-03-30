"""Validate first-contact messaging across the core repo entry points.

These tests ensure the README, docs landing page, and contributor guidance all
present the same canonical product story and onboarding order.
"""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
README = REPO_ROOT / "README.md"
DOCS_INDEX = REPO_ROOT / "docs" / "index.md"
CONTRIBUTING = REPO_ROOT / "CONTRIBUTING.md"

assert REPO_ROOT.exists(), f"Repository root missing: expected at {REPO_ROOT}"
assert README.is_file(), f"README.md missing: expected at {README}"
assert DOCS_INDEX.is_file(), f"docs/index.md missing: expected at {DOCS_INDEX}"
assert CONTRIBUTING.is_file(), f"CONTRIBUTING.md missing: expected at {CONTRIBUTING}"


def _read(path: Path) -> str:
    """Return the UTF-8 text contents of a repository file.

    Args:
        path: Path to the file to read.

    Returns:
        File contents as a string.
    """

    return path.read_text(encoding="utf-8")


def _assert_question_order(content: str, questions: list[str]) -> None:
    """Assert that the first-contact questions appear in increasing order.

    Args:
        content: Text content to inspect.
        questions: Ordered question strings that must appear in sequence.
    """

    indices = [content.index(question) for question in questions]
    assert indices == sorted(indices), f"Questions are out of order: {questions}"


def test_readme_leads_with_validation_and_alignment_story() -> None:
    readme = _read(README)
    questions = [
        "What is SpecFact?",
        "Why does it exist?",
        "Why should I use it?",
        "What do I get?",
        "How do I get started?",
    ]

    assert "validation and alignment layer" in readme
    _assert_question_order(readme, questions)


def test_readme_prioritizes_fast_start_over_docs_topology() -> None:
    readme = _read(README)

    start_idx = readme.index("## Start Here")
    topology_idx = readme.index("## Documentation Topology")
    assert start_idx < topology_idx


def test_readme_routes_users_by_outcome() -> None:
    readme = _read(README)

    assert "## Choose Your Path" in readme
    assert "Greenfield and AI-assisted delivery" in readme
    assert "Brownfield and reverse engineering" in readme
    assert "Backlog to code alignment" in readme


def test_docs_index_matches_first_contact_story() -> None:
    docs_index = _read(DOCS_INDEX)
    questions = [
        "What is SpecFact?",
        "Why does it exist?",
        "Why should I use it?",
        "What do I get?",
        "How to get started",
    ]

    assert "validation and alignment layer" in docs_index
    _assert_question_order(docs_index, questions)
    assert "modules.specfact.io" in docs_index
    assert "brownfield" in docs_index.lower()


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
    _assert_question_order(contributing, questions)
