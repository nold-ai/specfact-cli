"""Contract tests: README and docs landing must match the canonical uvx \"wow\" entry path.

The wow path is the primary onboarding surface (init + code review with --scope full).
"""

from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
README = REPO_ROOT / "README.md"
DOCS_INDEX = REPO_ROOT / "docs" / "index.md"

# Canonical strings — keep in sync with docs/index.md hero and README "Start Here".
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


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_readme_and_docs_index_include_identical_uvx_wow_commands() -> None:
    """Hero commands in README and docs/index.md must not drift."""
    readme = _read(README)
    docs = _read(DOCS_INDEX)
    for needle in (UVX_INIT, UVX_REVIEW):
        assert needle in readme, f"README.md must contain {needle!r}"
        assert needle in docs, f"docs/index.md must contain {needle!r}"


def test_readme_documents_pip_free_alternate_and_scope_full_rationale() -> None:
    """README explains --scope full and the installed-CLI equivalent."""
    readme = _read(README)
    assert "--scope full" in readme
    assert INSTALLED_INIT in readme and INSTALLED_REVIEW in readme
    assert "Verdict" in readme and "Score" in readme and "findings" in readme.lower()


def test_readme_wow_section_appears_before_choose_your_path() -> None:
    """Primary entry content must appear before outcome routing."""
    readme = _read(README)
    wow = readme.find("uvx specfact-cli init --profile solo-developer")
    choose = readme.find("## Choose Your Path")
    assert wow != -1 and choose != -1
    assert wow < choose


def test_docs_index_wow_block_precedes_what_is_specfact() -> None:
    """Landing page leads with the runnable block before deep product copy."""
    docs = _read(DOCS_INDEX)
    block = docs.find(UVX_INIT)
    heading = docs.find("## What is SpecFact?")
    assert block != -1 and heading != -1
    assert block < heading


def test_readme_start_here_precedes_documentation_topology() -> None:
    """Fast-start remains above internal docs topology (existing contract)."""
    readme = _read(README)
    start = readme.find("### Start Here")
    topo = readme.find("## Documentation Topology")
    assert start != -1 and topo != -1
    assert start < topo
