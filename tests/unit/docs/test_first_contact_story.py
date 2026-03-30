from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
README = REPO_ROOT / "README.md"
DOCS_INDEX = REPO_ROOT / "docs" / "index.md"
CONTRIBUTING = REPO_ROOT / "CONTRIBUTING.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_readme_leads_with_validation_and_alignment_story() -> None:
    readme = _read(README)

    assert "validation and alignment layer" in readme
    assert "What is SpecFact?" in readme
    assert "Why does it exist?" in readme
    assert "Why should I use it?" in readme
    assert "What do I get?" in readme
    assert "How do I get started?" in readme


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

    assert "validation and alignment layer" in docs_index
    assert "What is SpecFact?" in docs_index
    assert "How to get started" in docs_index
    assert "modules.specfact.io" in docs_index
    assert "brownfield" in docs_index.lower()


def test_contributing_guidance_mentions_entrypoint_story_hierarchy() -> None:
    contributing = _read(CONTRIBUTING)

    assert "first-contact" in contributing
    assert "What is SpecFact?" in contributing
    assert "How do I get started?" in contributing
