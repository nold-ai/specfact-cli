from __future__ import annotations

import importlib.util
import re
import textwrap
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_docs_json_gem_uses_the_patched_security_floor() -> None:
    """The documentation-site lock must not reintroduce the alerted json release."""
    gemfile = (REPO_ROOT / "docs" / "Gemfile").read_text(encoding="utf-8")
    lockfile = (REPO_ROOT / "docs" / "Gemfile.lock").read_text(encoding="utf-8")

    assert 'gem "json", ">= 2.21.2", "< 3"' in gemfile
    match = re.search(r"^    json \(([^)]+)\)$", lockfile, re.MULTILINE)
    assert match is not None
    assert (2, 21, 2) <= tuple(int(part) for part in match.group(1).split(".")) < (3,)
    assert "    jekyll (4.4.1)" in lockfile


def test_frozen_docs_job_installs_the_reviewed_relative_links_artifact() -> None:
    gemfile = (REPO_ROOT / "docs" / "Gemfile").read_text(encoding="utf-8")
    lockfile = (REPO_ROOT / "docs" / "Gemfile.lock").read_text(encoding="utf-8")
    workflow = (REPO_ROOT / ".github/workflows/docs-dependency-checks.yml").read_text(encoding="utf-8")
    artifact = "jekyll-relative-links-0.9.2.gem"
    digest = "9a1e7c58465f4fc63827a6d59ff95e1386b5f6b7683b633ec0230a144859c38c"

    assert 'gem "jekyll-relative-links", "~> 0.9.2"' in gemfile
    assert "    jekyll-relative-links (0.9.2)\n" in lockfile
    assert f"https://rubygems.org/gems/{artifact}" in workflow
    assert f"{digest}  {artifact}" in workflow
    assert "| sha256sum --check" in workflow
    assert "redirect feed_language feed_cdata relative" in workflow
    assert "jekyll build --baseurl ''" in workflow
    assert "jekyll build --baseurl '/preview'" in workflow


class _DocsCommands(Protocol):
    _REPO_ROOT: Path
    _EXCLUDED_DOC_PATHS: frozenset[str]

    def collect_specfact_commands_from_text(self, text: str) -> list[list[str]]: ...
    def collect_specfact_commands_from_guidance_text(self, text: str) -> list[list[str]]: ...
    def validate_command_tokens(self, tokens: list[str]) -> tuple[bool, str]: ...
    def _should_skip_guidance_path(self, rel: Path) -> bool: ...
    def _scan_guidance_templates_for_command_validation(
        self, docs_root: Path
    ) -> tuple[set[tuple[str, ...]], list[str]]: ...
    def _validate_nav_targets(self, docs_root: Path) -> list[str]: ...


class _CrossSiteLinks(Protocol):
    def _urls_from_line(self, line: str) -> list[str]: ...


class _CommandContract(Protocol):
    def _check_help(
        self, runner: object, apps: dict[tuple[str, ...], tuple[object, tuple[()]]], record: dict[str, object]
    ) -> list[str]: ...


def _load_script(stem: str) -> ModuleType:
    path = REPO_ROOT / "scripts" / f"{stem}.py"
    spec = importlib.util.spec_from_file_location(stem.replace("-", "_"), path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_check_docs_commands() -> _DocsCommands:
    return cast(_DocsCommands, _load_script("check-docs-commands"))


@pytest.mark.parametrize(
    ("example", "expected"),
    [
        ("$ specfact backlog ceremony standup", [["backlog", "ceremony", "standup"]]),
        ("specfact init && specfact module list", [["init"], ["module", "list"]]),
        ("specfact backlog analyze-deps --json", [["backlog", "analyze-deps", "--json"]]),
    ],
)
def test_collect_specfact_commands_from_markdown_code_block(example: str, expected: list[list[str]]) -> None:
    commands = _load_check_docs_commands().collect_specfact_commands_from_text(f"```bash\n{example}\n```\n")
    assert commands == expected


def test_code_import_options_after_bundle_are_rejected() -> None:
    mod = _load_check_docs_commands()

    ok, message = mod.validate_command_tokens(["code", "import", "legacy-api", "--repo"])

    assert ok is False
    assert "code import" in message
    assert "--repo" in message


def test_code_import_explicit_subcommand_keeps_legacy_bundle_position() -> None:
    mod = _load_check_docs_commands()

    ok, message = mod.validate_command_tokens(["code", "import", "from-code", "legacy-api", "--repo", "."])

    assert ok is True
    assert message == ""


def test_generated_contract_rejects_unknown_subcommand() -> None:
    mod = _load_check_docs_commands()

    ok, message = mod.validate_command_tokens(["generated-contract", "typo-subcmd", "--help"])

    assert ok is False
    assert "generated-contract" in message
    assert "typo-subcmd" in message


def test_command_contract_retries_parent_help_for_code_import_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = cast(_CommandContract, _load_script("check-command-contract"))
    calls: list[tuple[list[str], list[str]]] = []

    def fake_invoke(
        runner: object,
        apps: object,
        command_parts: list[str],
        suffix: list[str],
    ) -> tuple[int, str]:
        del runner, apps
        calls.append((command_parts, suffix))
        if command_parts == ["specfact", "code", "import", "from-bridge"]:
            return 2, "Usage: root import [OPTIONS] [BUNDLE] COMMAND [ARGS]...\nNo such command '--help'."
        if command_parts == ["specfact", "code", "import"]:
            return 0, "Usage: root import [OPTIONS] [BUNDLE] COMMAND [ARGS]...\nCommands:\n  from-bridge\n"
        raise AssertionError(command_parts)

    monkeypatch.setattr(mod, "_invoke", fake_invoke)

    failures = mod._check_help(
        runner=object(),
        apps={("specfact",): (object(), ())},
        record={"command": "specfact code import from-bridge", "subcommands": []},
    )

    assert failures == []
    assert calls == [
        (["specfact", "code", "import", "from-bridge"], ["--help"]),
        (["specfact", "code", "import"], ["--help"]),
    ]


def test_placeholder_command_examples_are_ignored() -> None:
    mod = _load_check_docs_commands()

    ok, message = mod.validate_command_tokens(["<command>", "--help"])

    assert ok is True
    assert message == ""


def test_core_cli_modes_page_is_not_excluded_from_command_validation() -> None:
    mod = _load_check_docs_commands()

    assert "docs/core-cli/modes.md" not in mod._EXCLUDED_DOC_PATHS


def test_github_prompt_library_is_excluded_from_command_validation() -> None:
    mod = _load_check_docs_commands()

    assert mod._should_skip_guidance_path(Path(".github/prompts/specfact.02-plan.prompt.md")) is True


def test_tokens_skip_leading_global_options_before_subcommand() -> None:
    mod = _load_check_docs_commands()
    text = """
```bash
specfact --mode copilot import from-code legacy-api --repo . --confidence 0.7
```
"""
    cmds = mod.collect_specfact_commands_from_text(text)
    assert ["import", "from-code", "legacy-api", "--repo", ".", "--confidence", "0.7"] in cmds


def test_collect_specfact_commands_from_inline_and_yaml_guidance() -> None:
    mod = _load_check_docs_commands()
    text = """
guidance: "Run `specfact module list --show-origin` before editing."
steps:
  - specfact project sync bridge --help
"""
    cmds = mod.collect_specfact_commands_from_guidance_text(text)
    assert ["module", "list", "--show-origin"] in cmds
    assert ["project", "sync", "bridge", "--help"] in cmds


def test_scan_guidance_templates_validates_resource_templates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_check_docs_commands()
    monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod, "_ADDITIONAL_GUIDANCE_ROOTS", (tmp_path / "resources",))
    monkeypatch.setattr(
        mod, "validate_command_tokens", lambda tokens: (tokens != ["sync", "bridge", "--help"], "stale")
    )

    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    template = tmp_path / "resources" / "templates" / "protocol.yaml.j2"
    template.parent.mkdir(parents=True)
    template.write_text('command: "specfact sync bridge --help"\n', encoding="utf-8")

    seen, failures = mod._scan_guidance_templates_for_command_validation(docs_root)

    assert ("sync", "bridge", "--help") in seen
    assert failures == ["resources/templates/protocol.yaml.j2: specfact sync bridge --help — stale"]


def test_cross_site_url_stops_at_markdown_delimiters() -> None:
    mod = cast(_CrossSiteLinks, _load_script("check-cross-site-links"))
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
