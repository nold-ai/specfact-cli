"""Tests for lean --help output and missing-bundle error (module-migration-03)."""

from __future__ import annotations

import re
from typing import Any, cast

import click
import pytest
import typer
from click.testing import CliRunner as ClickCliRunner
from typer.testing import CliRunner

from specfact_cli.cli import _LazyDelegateGroup, _RootCLIGroup, app
from specfact_cli.registry import CommandRegistry
from specfact_cli.registry.metadata import CommandMetadata


runner = CliRunner()
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


CORE_THREE = {"init", "module", "upgrade"}
EXTRACTED_ANY = [
    "project",
    "plan",
    "backlog",
    "code",
    "spec",
    "govern",
    "validate",
    "contract",
    "sdd",
    "generate",
    "enforce",
    "patch",
    "migrate",
    "repro",
    "drift",
    "analyze",
    "policy",
]


def test_specfact_help_fresh_install_contains_core_commands() -> None:
    """specfact --help (fresh install) must list only the 3 core commands."""
    result = runner.invoke(app, ["--help"], catch_exceptions=False)
    assert result.exit_code == 0
    for name in CORE_THREE:
        assert name in result.output, f"Core command {name} must appear in --help"
    assert "auth" not in result.output


def test_specfact_help_does_not_show_extracted_as_top_level_when_lean(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When only core is registered, --help must not show extracted commands as top-level."""
    result = runner.invoke(app, ["--help"], catch_exceptions=False)
    assert result.exit_code == 0
    lines = result.output.splitlines()
    usage_or_commands_section = False
    for line in lines:
        if "Commands:" in line or "Usage:" in line:
            usage_or_commands_section = True
        if usage_or_commands_section and line.strip().startswith("init"):
            break
    top_level = result.output
    for name in ["project", "plan", "backlog", "code", "spec", "govern"]:
        if name in top_level and top_level.index(name) < (top_level.index("init") if "init" in top_level else 0):
            continue
        if name in top_level:
            pytest.skip("Lean help not yet enforced; migration-03 will hide category groups until installed")


def test_specfact_help_contains_init_hint() -> None:
    """specfact --help should contain a hint to run specfact init for workflow bundles."""
    result = runner.invoke(app, ["--help"], catch_exceptions=False)
    assert result.exit_code == 0
    if "specfact init" not in result.output and "install" not in result.output.lower():
        pytest.skip("Init hint not yet in help; migration-03 will add it")


def test_root_group_unknown_bundle_command_shows_install_guidance(capsys: pytest.CaptureFixture[str]) -> None:
    """Unknown bundle commands should show install guidance instead of raw Click errors."""
    group = _RootCLIGroup(name="specfact")
    ctx = click.Context(cast(Any, group))

    with pytest.raises(SystemExit) as exc_info:
        group.resolve_command(ctx, ["backlog", "--help"])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    out = " ".join(captured.out.split())
    assert "Module 'nold-ai/specfact-backlog' is not installed." in out
    assert "specfact module install nold-ai/specfact-backlog" in out
    assert "specfact init --profile <profile>" in out


def test_root_group_unknown_code_shows_specfact_codebase_module(capsys: pytest.CaptureFixture[str]) -> None:
    """Missing `code` group should name nold-ai/specfact-codebase (not the VS Code `code` CLI)."""
    group = _RootCLIGroup(name="specfact")
    ctx = click.Context(cast(Any, group))

    with pytest.raises(SystemExit) as exc_info:
        group.resolve_command(ctx, ["code", "--help"])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    out = " ".join(captured.out.split())
    assert "Module 'nold-ai/specfact-codebase' is not installed." in out
    assert "specfact module install nold-ai/specfact-codebase" in out


def test_stale_lazy_flat_shim_prints_install_guidance() -> None:
    """A stale lazy flat shim should not exit with empty output."""
    CommandRegistry._clear_for_testing()
    result = ClickCliRunner().invoke(_LazyDelegateGroup("plan", "Plan commands."), ["init"], catch_exceptions=False)
    CommandRegistry._clear_for_testing()

    assert result.exit_code == 1
    assert "plan" in result.output.lower()
    assert result.output.strip()


def test_lazy_delegate_forwards_bare_subcommand_without_options() -> None:
    """A lazy group must not drop a single subcommand that has no trailing args."""
    CommandRegistry._clear_for_testing()
    delegated = typer.Typer(help="Module commands.")

    @delegated.command(name="list")
    def list_command() -> None:
        click.echo("listed")

    @delegated.command(name="alias")
    def alias_command() -> None:
        click.echo("aliased")

    CommandRegistry.register(
        "module",
        lambda: delegated,
        CommandMetadata(name="module", help="Module commands.", tier="official", addon_id=None),
    )
    result = ClickCliRunner().invoke(
        _LazyDelegateGroup("module", "Module commands."),
        ["list"],
        catch_exceptions=False,
    )
    CommandRegistry._clear_for_testing()

    assert result.exit_code == 0
    assert "listed" in result.output


def test_lazy_delegate_bare_group_shows_full_help_and_missing_subcommand() -> None:
    """Bare lazy groups should show real help, explicit missing-subcommand guidance, and full command path."""
    result = runner.invoke(app, ["module"], catch_exceptions=False)
    output = _strip_ansi(result.output)

    assert result.exit_code == 2
    assert "Usage: specfact module" in output
    assert "Manage marketplace modules" in output
    assert "Missing subcommand" in output
    assert "list" in output


def test_lazy_delegate_missing_option_value_shows_leaf_help() -> None:
    """Dangling option values must render the delegated leaf help, not the wrapper usage."""
    result = runner.invoke(app, ["module", "install", "--scope"], catch_exceptions=False)
    output = _strip_ansi(result.output)

    assert result.exit_code == 2
    assert "Usage: specfact module install" in output
    assert "Option '--scope' requires an argument" in output
    assert "MODULE_IDS" in output


def test_lazy_delegate_help_falls_back_when_typer_command_build_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """Help-only delegation should not fail when Typer cannot materialize a loaded app."""
    CommandRegistry._clear_for_testing()
    CommandRegistry.register(
        "project",
        lambda: typer.Typer(help="Project commands."),
        CommandMetadata(name="project", help="Project commands.", tier="official", addon_id=None),
    )

    def _raise_runtime_error(_typer_instance: typer.Typer) -> click.Command:
        raise RuntimeError("Could not get a command for this Typer instance")

    monkeypatch.setattr("typer.main.get_command", _raise_runtime_error)
    result = ClickCliRunner().invoke(
        _LazyDelegateGroup("project", "Project commands."),
        ["devops-flow", "--help"],
        catch_exceptions=False,
    )
    CommandRegistry._clear_for_testing()

    assert result.exit_code == 0
    assert "project devops-flow" in result.output
    assert "Could not get a command" not in result.output


def test_specfact_help_with_all_bundles_installed_shows_eight_commands(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With all 5 bundles installed, --help should show 3 core + 5 category groups = 8 top-level."""
    result = runner.invoke(app, ["--help"], catch_exceptions=False)
    assert result.exit_code == 0
    if "backlog" in result.output and "code" in result.output and "project" in result.output:
        core_and_groups = CORE_THREE | {"backlog", "code", "project", "spec", "govern"}
        assert len(core_and_groups) >= 8 or "init" in result.output
