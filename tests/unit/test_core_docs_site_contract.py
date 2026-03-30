from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_CONFIG = REPO_ROOT / "docs" / "_config.yml"
DOCS_INDEX = REPO_ROOT / "docs" / "index.md"
DOCS_LAYOUT = REPO_ROOT / "docs" / "_layouts" / "default.html"
OUTDATED_DOCS_HOSTS = (
    "modules.docs.specfact.io",
    "cli.docs.specfact.io",
    "nold-ai.github.io/specfact-cli-modules",
    "nold-ai.github.io/specfact-cli",
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_bytes().decode("utf-8", errors="ignore")


def _config() -> dict[str, object]:
    return yaml.safe_load(_read(DOCS_CONFIG))


def test_core_docs_config_targets_public_core_domain() -> None:
    config = _config()

    assert config["url"] == "https://docs.specfact.io"
    assert config["baseurl"] == ""
    assert config["docs_home_url"] == "https://docs.specfact.io"
    assert config["core_cli_docs_url"] == "https://docs.specfact.io"
    assert config["modules_docs_url"] == "https://modules.specfact.io"


def test_core_landing_page_marks_core_repo_as_canonical_owner() -> None:
    index = _read(DOCS_INDEX)

    assert "SpecFact is the validation and alignment layer for software delivery." in index
    assert "canonical starting point for the core CLI story" in index
    assert "module-deep workflows" in index
    assert "https://modules.specfact.io/" in index
    assert "nold-ai.github.io/specfact-cli" not in index


def test_core_layout_exposes_shared_cross_site_navigation() -> None:
    layout = _read(DOCS_LAYOUT)

    assert ">Docs Home<" in layout
    assert ">Core CLI<" in layout
    assert ">Modules<" in layout
    assert "{{ site.docs_home_url }}" in layout
    assert "{{ site.core_cli_docs_url }}" in layout
    assert "{{ site.modules_docs_url }}" in layout


def test_core_layout_exposes_shared_portal_features() -> None:
    layout = _read(DOCS_LAYOUT)

    assert "{% include theme-toggle.html %}" in layout
    assert "{% include search.html %}" in layout
    assert "{% include expertise-filter.html %}" in layout
    assert "{% include sidebar-nav.html %}" in layout
    assert "{% include breadcrumbs.html %}" in layout
    assert "search.js" in layout
    assert "filters.js" in layout


def test_core_layout_keeps_sidebar_core_focused() -> None:
    layout = _read(DOCS_LAYOUT)

    assert "Core CLI Docs" in layout
    assert 'aria-label="Documentation navigation"' in layout
    assert "Official Modules Docs" not in layout


def test_docs_tree_does_not_reference_retired_public_hosts() -> None:
    skip_parts = frozenset({"vendor", "_site", ".bundle", ".jekyll-cache"})
    for path in REPO_ROOT.joinpath("docs").rglob("*"):
        if not path.is_file():
            continue
        if skip_parts.intersection(path.parts):
            continue
        text = _read(path)
        for host in OUTDATED_DOCS_HOSTS:
            assert host not in text, f"{path} still references retired host {host}"
