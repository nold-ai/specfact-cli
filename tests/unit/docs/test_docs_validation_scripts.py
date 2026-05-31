from __future__ import annotations

import importlib.util
import textwrap
from pathlib import Path

import pytest


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


def test_code_import_options_after_bundle_are_rejected() -> None:
    mod = _load_check_docs_commands()

    ok, message = mod.validate_command_tokens(["code", "import", "legacy-api", "--repo"])

    assert ok is False
    assert "code import" in message
    assert "--repo" in message


def test_core_cli_modes_page_is_not_excluded_from_command_validation() -> None:
    mod = _load_check_docs_commands()

    assert "docs/core-cli/modes.md" not in mod._EXCLUDED_DOC_PATHS


def test_tokens_skip_leading_global_options_before_subcommand() -> None:
    mod = _load_check_docs_commands()
    text = """
```bash
specfact --mode copilot import from-code legacy-api --repo . --confidence 0.7
```
"""
    cmds = mod.collect_specfact_commands_from_text(text)
    assert ["import", "from-code", "legacy-api"] in cmds


def test_collect_specfact_commands_from_guidance_text_handles_inline_and_yaml() -> None:
    mod = _load_check_docs_commands()
    text = """
guidance: "Run `specfact module list --show-origin` before editing."
steps:
  - specfact project sync bridge --help
"""
    cmds = mod.collect_specfact_commands_from_guidance_text(text)
    assert ["module", "list"] in cmds
    assert ["project", "sync", "bridge"] in cmds


def test_scan_guidance_templates_validates_resource_templates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_check_docs_commands()
    monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod, "_ADDITIONAL_GUIDANCE_ROOTS", (tmp_path / "resources",))
    monkeypatch.setattr(mod, "validate_command_tokens", lambda tokens: (tokens != ["sync", "bridge"], "stale"))

    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    template = tmp_path / "resources" / "templates" / "protocol.yaml.j2"
    template.parent.mkdir(parents=True)
    template.write_text('command: "specfact sync bridge --help"\n', encoding="utf-8")

    seen, failures = mod._scan_guidance_templates_for_command_validation(docs_root)

    assert ("sync", "bridge") in seen
    assert failures == ["resources/templates/protocol.yaml.j2: specfact sync bridge — stale"]


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
