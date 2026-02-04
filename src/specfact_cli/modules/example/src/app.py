"""Example module package app - one command group 'example'."""

from __future__ import annotations

import typer


app = typer.Typer(
    name="example",
    help="Example module package (discovered from src/specfact_cli/modules/)",
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Example command group."""
    if ctx.invoked_subcommand is None:
        typer.echo("Example module package. Use --help for subcommands.")


@app.command()
def hello() -> None:
    """Say hello from the example package."""
    typer.echo("Hello from example module package.")
