"""Exercise Click context injection through Typer's command runner."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click
import typer
from typer import utils as typer_utils
from typer.testing import CliRunner


def test_cli_imports_without_the_legacy_typer_converter() -> None:
    script = """
import sys

from typer import main as typer_main

sys.path.insert(0, sys.argv[1])
legacy_converter = "get_params_convertors_ctx_param_name_from_function"
if hasattr(typer_main, legacy_converter):
    delattr(typer_main, legacy_converter)

from specfact_cli.cli import cli_main

assert callable(cli_main)
"""
    source_root = Path(__file__).resolve().parents[3] / "src"
    result = subprocess.run(
        [sys.executable, "-", str(source_root)], input=script, capture_output=True, text=True, check=False, timeout=30
    )
    assert result.returncode == 0, result.stderr


def test_registered_callback_receives_click_context_and_options() -> None:
    from specfact_cli.cli import app

    command_app = typer.Typer()

    @command_app.command()
    def command(ctx: click.Context, name: str = "default") -> None:
        typer.echo(f"{ctx.info_name}: {name}")

    assert typer_utils.get_params_from_function(command)["ctx"].annotation is typer.Context
    runner = CliRunner()
    assert runner.invoke(app, ["--version"], catch_exceptions=False).exit_code == 0

    result = runner.invoke(command_app, ["--name", "specfact"], prog_name="compatibility", catch_exceptions=False)
    assert result.exit_code == 0
    assert result.output.strip() == "compatibility: specfact"
