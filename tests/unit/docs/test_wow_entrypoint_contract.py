"""Contract tests for the README proof-first onboarding surface."""

from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
README = REPO_ROOT / "README.md"
DOCS_INDEX = REPO_ROOT / "docs" / "index.md"
CAPTURE_SCRIPT = REPO_ROOT / "docs" / "_support" / "readme-first-contact" / "capture-readme-output.sh"
EVIDENCE_DIR = REPO_ROOT / "docs" / "_support" / "readme-first-contact" / "sample-output"

HOOK = "Review AI-assisted code against your own contracts."
CTA = "Star this repo if the output is useful."
UVX_INIT = "uvx specfact-cli init --profile solo-developer"
UVX_REVIEW = "uvx specfact-cli code review run --path . --scope full"
INSTALLED_INIT = "specfact init --profile solo-developer"
INSTALLED_REVIEW = "specfact code review run --path . --scope full"


@pytest.fixture(scope="module", autouse=True)
def _require_files() -> None:
    if not README.is_file():
        pytest.skip(f"README.md missing at {README}", allow_module_level=True)
    if not DOCS_INDEX.is_file():
        pytest.skip(f"docs/index.md missing at {DOCS_INDEX}", allow_module_level=True)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_readme_and_docs_index_include_identical_uvx_wow_commands() -> None:
    """README and docs/index must share the canonical uvx wow commands."""
    readme = _read(README)
    docs = _read(DOCS_INDEX)
    for needle in (UVX_INIT, UVX_REVIEW):
        assert needle in readme, f"README.md must contain {needle!r}"
        assert needle in docs, f"docs/index.md must contain {needle!r}"


def test_readme_documents_proof_block_cta_and_installed_equivalent() -> None:
    """README keeps the hook, proof block, CTA, and installed CLI path together."""
    readme = _read(README)
    assert HOOK in readme
    assert "Sample output:" in readme
    assert "Evidence bundle:" in readme
    assert CTA in readme
    assert INSTALLED_INIT in readme and INSTALLED_REVIEW in readme
    assert "Verdict:" in readme and "Findings:" in readme and "works offline" in readme.lower()


def test_readme_proof_first_sections_precede_deeper_sections() -> None:
    """Proof and workflow sections must appear before org and module detail."""
    readme = _read(README)
    try_it = readme.find("## Try it in 60 seconds")
    what_it_does = readme.find("## What SpecFact does")
    workflow = readme.find("## Add SpecFact to your workflow")
    teams = readme.find("## For teams and organizations")
    assert min(try_it, what_it_does, workflow, teams) != -1
    assert try_it < what_it_does < workflow < teams


def test_docs_index_shares_readme_hook_and_wow_block() -> None:
    """Docs landing keeps the same first-contact identity and ordering."""
    docs = _read(DOCS_INDEX)
    assert HOOK in docs
    assert docs.find(UVX_INIT) != -1
    assert docs.find(UVX_INIT) < docs.find("## What is SpecFact?")


def test_readme_capture_script_and_evidence_folder_exist() -> None:
    """README sample output must be backed by reproducible evidence artifacts."""
    assert CAPTURE_SCRIPT.is_file(), "Missing docs/_support/readme-first-contact/capture-readme-output.sh"
    assert EVIDENCE_DIR.is_dir(), "Missing docs/_support/readme-first-contact/sample-output/"
