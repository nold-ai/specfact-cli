from __future__ import annotations

import importlib.util
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_check_docs_commands() -> object:
    path = REPO_ROOT / "scripts" / "check-docs-commands.py"
    spec = importlib.util.spec_from_file_location("check_docs_commands", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_check_cross_site_links() -> object:
    path = REPO_ROOT / "scripts" / "check-cross-site-links.py"
    spec = importlib.util.spec_from_file_location("check_cross_site_links", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_collect_specfact_commands_from_markdown_code_block() -> None:
    mod = _load_check_docs_commands()
    text = """
```bash
$ specfact backlog ceremony standup
```
"""
    cmds = mod.collect_specfact_commands_from_text(text)
    assert ["backlog", "ceremony", "standup"] in cmds


def test_collect_specfact_commands_chained_with_and() -> None:
    mod = _load_check_docs_commands()
    text = """
```bash
specfact init && specfact module list
```
"""
    cmds = mod.collect_specfact_commands_from_text(text)
    assert ["init"] in cmds
    assert ["module", "list"] in cmds


def test_tokens_from_line_stops_at_flags() -> None:
    mod = _load_check_docs_commands()
    text = """
```bash
specfact backlog analyze-deps --json
```
"""
    cmds = mod.collect_specfact_commands_from_text(text)
    assert ["backlog", "analyze-deps"] in cmds


def test_tokens_skip_leading_global_options_before_subcommand() -> None:
    mod = _load_check_docs_commands()
    text = """
```bash
specfact --mode copilot import from-code legacy-api --repo . --confidence 0.7
```
"""
    cmds = mod.collect_specfact_commands_from_text(text)
    assert ["import", "from-code", "legacy-api"] in cmds


def test_cross_site_url_stops_at_markdown_delimiters() -> None:
    mod = _load_check_cross_site_links()
    line = "| `https://modules.specfact.io/foo/bar/` |"
    urls = mod._urls_from_line(line)
    assert urls == ["https://modules.specfact.io/foo/bar/"]


def test_validate_nav_targets_accepts_known_routes(tmp_path: Path) -> None:
    mod = _load_check_docs_commands()
    mod._REPO_ROOT = tmp_path

    docs_root = tmp_path / "docs"
    (docs_root / "_data").mkdir(parents=True)
    (docs_root / "index.md").write_text(
        textwrap.dedent(
            """\
            ---
            title: Home
            permalink: /
            ---
            """
        ),
        encoding="utf-8",
    )
    (docs_root / "getting-started.md").write_text(
        textwrap.dedent(
            """\
            ---
            title: Getting Started
            permalink: /getting-started/
            ---
            """
        ),
        encoding="utf-8",
    )
    (docs_root / "_data" / "nav.yml").write_text(
        textwrap.dedent(
            """\
            - section: Start
              items:
                - title: Home
                  url: /
                  expertise: [beginner]
                - title: Getting Started
                  url: /getting-started/
                  expertise: [beginner]
            """
        ),
        encoding="utf-8",
    )

    assert mod._validate_nav_targets(docs_root) == []


def test_validate_nav_targets_reports_unknown_route(tmp_path: Path) -> None:
    mod = _load_check_docs_commands()
    mod._REPO_ROOT = tmp_path

    docs_root = tmp_path / "docs"
    (docs_root / "_data").mkdir(parents=True)
    (docs_root / "index.md").write_text(
        textwrap.dedent(
            """\
            ---
            title: Home
            permalink: /
            ---
            """
        ),
        encoding="utf-8",
    )
    (docs_root / "_data" / "nav.yml").write_text(
        textwrap.dedent(
            """\
            - section: Start
              items:
                - title: Missing
                  url: /missing/
                  expertise: [beginner]
            """
        ),
        encoding="utf-8",
    )

    failures = mod._validate_nav_targets(docs_root)
    assert failures == ["docs/_data/nav.yml: unknown docs route /missing/"]
