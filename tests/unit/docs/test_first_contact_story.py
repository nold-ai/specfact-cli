"""Validate the README-first first-contact story across entrypoint surfaces."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from urllib.parse import urlparse

import pytest

from tests.unit.docs.docs_test_constants import HOOK, SUBHOOK


REPO_ROOT = Path(__file__).resolve().parents[3]
README = REPO_ROOT / "README.md"
DOCS_INDEX = REPO_ROOT / "docs" / "index.md"
DOCS_README = REPO_ROOT / "docs" / "README.md"
GETTING_STARTED = REPO_ROOT / "docs" / "getting-started" / "README.md"
QUICKSTART = REPO_ROOT / "docs" / "getting-started" / "quickstart.md"
CODE_REVIEW_MODULE = REPO_ROOT / "docs" / "modules" / "code-review.md"
CONTRIBUTING = REPO_ROOT / "CONTRIBUTING.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"
SETUP_PY = REPO_ROOT / "setup.py"
PACKAGE_INIT = REPO_ROOT / "src" / "specfact_cli" / "__init__.py"

ABSOLUTE_URL_RE = re.compile(r"https?://[^\s)>'\"`]+")


@pytest.fixture(scope="module", autouse=True)
def require_entrypoint_files() -> None:
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
    try_it_idx = readme.lower().find("## try it in 60 seconds")
    assert try_it_idx != -1
    first_screen = readme[:try_it_idx].lower()

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


def test_docs_entrypoints_share_ai_bloat_defense_story() -> None:
    for path in (DOCS_README, GETTING_STARTED, QUICKSTART):
        content = _read(path)
        assert "AI-bloat defense" in content
        assert "cleanup forecast" in content
        assert "remediation packet" in content
        assert "AI-authorship detection" in content
        _assert_contains_url_host(content, "modules.specfact.io", str(path.relative_to(REPO_ROOT)))


def test_quickstart_documents_json_first_cleanup_loop() -> None:
    quickstart = _read(QUICKSTART)
    expected_steps = (
        "Run simplify-focused review with JSON output",
        "Inspect `cleanup_forecast` and the AI-bloat index",
        "Hand remediation packets to your AI IDE",
        "Re-run review for proof",
    )
    for step in expected_steps:
        assert step in quickstart


def test_code_review_handoff_mentions_cleanup_forecast_and_modules_ownership() -> None:
    docs = _read(CODE_REVIEW_MODULE)
    for needle in (
        "cleanup forecast",
        "AI-bloat index",
        "preserve reasons",
        "remediation packets",
        "modules.specfact.io/bundles/code-review/run/",
        "modules.specfact.io/quickstart-ai-bloat/",
    ):
        assert needle in docs
    assert "AI-authorship proof" in docs


def test_distribution_description_mentions_ai_bloat_defense_cli() -> None:
    pyproject = tomllib.loads(_read(PYPROJECT))
    description = pyproject["project"]["description"]
    keywords = set(pyproject["project"]["keywords"])
    setup_py = _read(SETUP_PY)
    package_init = _read(PACKAGE_INIT)

    assert "AI-bloat defense CLI" in description
    assert "cleanup forecasts" in description
    assert {"ai-bloat", "code-review", "clean-code", "technical-debt"} <= keywords
    assert "AI-bloat defense CLI" in setup_py
    assert "AI-bloat defense CLI" in package_init
    for metadata_text in (description, setup_py, package_init):
        assert "swiss knife" not in metadata_text.lower()


def test_contributing_guidance_mentions_entrypoint_story_hierarchy() -> None:
    contributing = _read(CONTRIBUTING)
    assert "first-contact" in contributing
    assert "What is SpecFact?" in contributing
    assert "How do I get started?" in contributing
