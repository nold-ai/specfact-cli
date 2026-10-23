from __future__ import annotations

import importlib.util
import re
import textwrap
from pathlib import Path
from types import ModuleType

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_docs_json_gem_uses_the_patched_security_floor() -> None:
    """The documentation-site lock must not reintroduce the alerted json release."""
    gemfile = (REPO_ROOT / "docs" / "Gemfile").read_text(encoding="utf-8")
    lockfile = (REPO_ROOT / "docs" / "Gemfile.lock").read_text(encoding="utf-8")

    assert 'gem "json", ">= 2.19.9"' in gemfile
    match = re.search(r"^    json \(([^)]+)\)$", lockfile, re.MULTILINE)
    assert match is not None
    assert tuple(int(part) for part in match.group(1).split(".")) >= (2, 19, 9)


def _load_script(stem: str) -> ModuleType:
    path = REPO_ROOT / "scripts" / f"{stem}.py"
    spec = importlib.util.spec_from_file_location(stem.replace("-", "_"), path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize(
    ("text", "expected_commands"),
    [
        pytest.param(
            "\n```bash\n$ specfact backlog ceremony standup\n```\n",
            [["backlog", "ceremony", "standup"]],
            id="code-block",
        ),
        pytest.param(
            "\n```bash\nspecfact init && specfact module list\n```\n",
            [["init"], ["module", "list"]],
            id="chained-and",
        ),
        pytest.param(
            "\n```bash\nspecfact backlog analyze-deps --json\n```\n",
            [["backlog", "analyze-deps", "--json"]],
            id="flags",
        ),
        pytest.param(
            "\n```bash\nspecfact --mode copilot import from-code legacy-api --repo . --confidence 0.7\n```\n",
            [["import", "from-code", "legacy-api", "--repo", ".", "--confidence", "0.7"]],
            id="leading-global-options",
        ),
    ],
)
def test_collect_specfact_commands_from_markdown_code_block(text: str, expected_commands: list[list[str]]) -> None:
    mod = _load_script("check-docs-commands")
    commands = mod.collect_specfact_commands_from_text(text)
    for command in expected_commands:
        assert command in commands


def test_code_import_options_after_bundle_are_rejected() -> None:
    mod = _load_script("check-docs-commands")

    ok, message = mod.validate_command_tokens(["code", "import", "legacy-api", "--repo"])

    assert ok is False
    assert "code import" in message
    assert "--repo" in message


def test_code_import_explicit_subcommand_keeps_legacy_bundle_position() -> None:
    mod = _load_script("check-docs-commands")

    ok, message = mod.validate_command_tokens(["code", "import", "from-code", "legacy-api", "--repo", "."])

    assert ok is True
    assert message == ""


def test_generated_contract_rejects_unknown_subcommand() -> None:
    mod = _load_script("check-docs-commands")

    ok, message = mod.validate_command_tokens(["generated-contract", "typo-subcmd", "--help"])

    assert ok is False
    assert "generated-contract" in message
    assert "typo-subcmd" in message


def test_command_contract_retries_parent_help_for_code_import_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_script("check-command-contract")
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
    mod = _load_script("check-docs-commands")

    ok, message = mod.validate_command_tokens(["<command>", "--help"])

    assert ok is True
    assert message == ""


def test_core_cli_modes_page_is_not_excluded_from_command_validation() -> None:
    mod = _load_script("check-docs-commands")

    assert "docs/core-cli/modes.md" not in mod._EXCLUDED_DOC_PATHS


def test_github_prompt_library_is_excluded_from_command_validation() -> None:
    mod = _load_script("check-docs-commands")

    assert mod._should_skip_guidance_path(Path(".github/prompts/specfact.02-plan.prompt.md")) is True


def test_collect_specfact_commands_from_guidance_text_supports_inline_and_yaml() -> None:
    mod = _load_script("check-docs-commands")
    text = """
guidance: "Run `specfact module list --show-origin` before editing."
steps:
  - specfact project sync bridge --help
"""
    cmds = mod.collect_specfact_commands_from_guidance_text(text)
    assert ["module", "list", "--show-origin"] in cmds
    assert ["project", "sync", "bridge", "--help"] in cmds


def test_scan_guidance_templates_validates_resource_templates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_script("check-docs-commands")
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
    mod = _load_script("check-cross-site-links")
    line = "| `https://modules.specfact.io/foo/bar/` |"
    urls = mod._urls_from_line(line)
    assert urls == ["https://modules.specfact.io/foo/bar/"]


def test_validate_nav_targets_accepts_known_routes(tmp_path: Path) -> None:
    mod = _load_script("check-docs-commands")
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
    mod = _load_script("check-docs-commands")
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
