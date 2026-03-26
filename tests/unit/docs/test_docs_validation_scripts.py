from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_check_docs_commands() -> object:
    path = REPO_ROOT / "scripts" / "check-docs-commands.py"
    spec = importlib.util.spec_from_file_location("check_docs_commands", path)
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


def test_cross_site_url_stops_at_markdown_delimiters() -> None:
    import importlib.util

    path = REPO_ROOT / "scripts" / "check-cross-site-links.py"
    spec = importlib.util.spec_from_file_location("check_cross_site_links", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    line = "| `https://modules.specfact.io/foo/bar/` |"
    urls = mod._urls_from_line(line)
    assert urls == ["https://modules.specfact.io/foo/bar/"]
