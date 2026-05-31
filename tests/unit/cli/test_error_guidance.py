from __future__ import annotations

from typing import Any, cast

import pytest
import typer
from click.testing import CliRunner
from typer.main import get_command
from typer.testing import CliRunner as TyperCliRunner

from specfact_cli.cli import app


def test_unknown_root_command_shows_help_and_recovery_guidance() -> None:
    runner = CliRunner()
    result = runner.invoke(cast(Any, get_command(app)), ["hello"])

    assert result.exit_code != 0
    output = result.output.lower()
    assert "usage: specfact" in output
    assert "hello" in output
    assert "not a valid command" in output or "no such command" in output
    assert "try" in output
    assert "specfact --help" in output or "specfact -h" in output


def _sample_app() -> typer.Typer:
    sample = typer.Typer(name="sample")
    widgets = typer.Typer(help="Manage widgets.")

    @widgets.command("list")
    def list_widgets() -> None:
        typer.echo("listed")

    @widgets.command("deploy")
    def deploy_widget(target: str) -> None:
        typer.echo(target)

    sample.add_typer(widgets, name="widgets")
    return sample


def test_global_group_without_subcommand_shows_help_and_missing_subcommand() -> None:
    result = CliRunner().invoke(cast(Any, get_command(_sample_app())), ["widgets"])

    assert result.exit_code == 2
    output = result.output.lower()
    assert "usage:" in output
    assert "manage widgets" in output
    assert "list" in output
    assert "deploy" in output
    assert "missing subcommand" in output


def test_global_leaf_missing_argument_shows_help_and_missing_parameter() -> None:
    result = CliRunner().invoke(cast(Any, get_command(_sample_app())), ["widgets", "deploy"])

    assert result.exit_code == 2
    output = result.output.lower()
    assert "usage:" in output
    assert "deploy" in output
    assert "target" in output
    assert "missing" in output


def test_global_nested_unknown_command_shows_group_help_and_invalid_command() -> None:
    result = CliRunner().invoke(cast(Any, get_command(_sample_app())), ["widgets", "remove"])

    assert result.exit_code == 2
    output = result.output.lower()
    assert "usage:" in output
    assert "manage widgets" in output
    assert "remove" in output
    assert "not a valid command" in output or "no such command" in output


@pytest.mark.parametrize(
    ("name", "args"),
    [
        ("root typo", ["modul"]),
        ("bare module", ["module"]),
        ("module typo", ["module", "instal"]),
        ("module missing arg", ["module", "install"]),
        ("module missing option value", ["module", "install", "--scope"]),
        ("module leaf missing arg", ["module", "show"]),
        ("module bad option", ["module", "show", "--bad-option"]),
        ("module subgroup missing subcommand", ["module", "alias"]),
        ("module subgroup typo", ["module", "alias", "creat"]),
        ("module subgroup leaf missing arg", ["module", "alias", "create"]),
        ("init subgroup missing option value", ["init", "ide", "--repo"]),
        ("upgrade bad option", ["upgrade", "--bad-option"]),
        ("code missing subcommand", ["code"]),
        ("code typo", ["code", "impor"]),
        ("code import missing option value", ["code", "import", "--repo"]),
        ("backlog auth missing subcommand", ["backlog", "auth"]),
        ("backlog delta status missing context", ["backlog", "delta", "status"]),
        ("project sync typo", ["project", "sync", "brdge"]),
        ("project sync bridge missing option value", ["project", "sync", "bridge", "--repo"]),
    ],
)
def test_cli_misuse_matrix_shows_contextual_help_once(name: str, args: list[str]) -> None:
    result = TyperCliRunner().invoke(app, args)
    output = result.output.lower()

    assert result.exit_code != 0, name
    assert "usage:" in output, name
    assert any(
        token in output
        for token in ["error:", "missing", "no such command", "no such option", "requires an argument", "did you mean"]
    ), name
    assert output.count("usage:") == 1, name
    if args[:1] == ["module"]:
        assert "usage: module " not in output, name
