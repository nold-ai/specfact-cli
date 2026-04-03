"""Validate the README-first first-contact story across entrypoint surfaces."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
README = REPO_ROOT / "README.md"
DOCS_INDEX = REPO_ROOT / "docs" / "index.md"
CONTRIBUTING = REPO_ROOT / "CONTRIBUTING.md"

ABSOLUTE_URL_RE = re.compile(r"https?://[^\s)>'\"`]+")
HOOK = "Review AI-assisted code against your own contracts."
SUBHOOK = "Catch drift before it reaches PR or main."


@pytest.fixture(scope="module", autouse=True)
def _require_entrypoint_files() -> None:
    if not REPO_ROOT.exists():
        pytest.skip(f"Repository root missing: expected at {REPO_ROOT}", allow_module_level=True)
    if not README.is_file():
        pytest.skip(f"README.md missing: expected at {README}", allow_module_level=True)
    if not DOCS_INDEX.is_file():
        pytest.skip(f"docs/index.md missing: expected at {DOCS_INDEX}", allow_module_level=True)
    if not CONTRIBUTING.is_file():
        pytest.skip(f"CONTRIBUTING.md missing: expected at {CONTRIBUTING}", allow_module_level=True)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _assert_contains_url_host(content: str, host: str, surface: str) -> None:
    found_hosts = {urlparse(match.group(0).rstrip(".,;:")).netloc for match in ABSOLUTE_URL_RE.finditer(content)}
    assert host in found_hosts, f"Missing URL host {host!r} in {surface}; found hosts: {sorted(found_hosts)}"


def test_readme_hero_uses_proof_first_story() -> None:
    readme = _read(README)
    first_screen = "\n".join(readme.splitlines()[:40]).lower()

    assert HOOK in readme
    assert SUBHOOK in readme
    assert "## Try it in 60 seconds" in readme
    assert "validation and alignment layer" not in first_screen
    assert "swiss knife" not in first_screen


def test_readme_prioritizes_quickstart_before_deep_sections() -> None:
    readme = _read(README)
    try_it = readme.find("## Try it in 60 seconds")
    teams = readme.find("## For teams and organizations")
    modules = readme.find("## Module system")
    topology = readme.find("## Documentation topology")
    assert min(try_it, teams, modules, topology) != -1
    assert try_it < teams < modules < topology


def test_readme_includes_trust_and_pipeline_sections() -> None:
    readme = _read(README)
    assert "## How SpecFact is built" in readme
    assert "OpenSpec" in readme
    assert "TDD" in readme
    assert "quality gates" in readme.lower()


def test_docs_index_matches_proof_first_story() -> None:
    docs_index = _read(DOCS_INDEX)
    assert HOOK in docs_index
    assert SUBHOOK in docs_index
    assert "## What is SpecFact?" in docs_index
    _assert_contains_url_host(docs_index, "modules.specfact.io", "docs/index.md")
    assert "default starting point" in docs_index.lower()


def test_contributing_guidance_mentions_entrypoint_story_hierarchy() -> None:
    contributing = _read(CONTRIBUTING)
    assert "first-contact" in contributing
    assert "What is SpecFact?" in contributing
    assert "How do I get started?" in contributing
