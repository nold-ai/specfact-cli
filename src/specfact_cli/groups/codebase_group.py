"""Codebase quality category group (analyze, drift, validate, repro)."""

from __future__ import annotations

import typer
from beartype import beartype
from icontract import ensure, require

from specfact_cli.registry.registry import CommandRegistry


_MEMBERS = ("analyze", "drift", "validate", "repro")


@require(lambda app: app is not None)
@ensure(lambda result: result is None)
@beartype
def _register_members(app: typer.Typer) -> None:
    """Register member module sub-apps (called when group is first used)."""
    for name in _MEMBERS:
        try:
            member_app = CommandRegistry.get_module_typer(name)
            if member_app is not None:
                app.add_typer(member_app, name=name)
        except ValueError:
            pass


def build_app() -> typer.Typer:
    """Build the code group Typer with members (lazy; registry must be populated)."""
    app = typer.Typer(
        name="code",
        help="Codebase quality commands: analyze, drift, validate, repro.",
        no_args_is_help=True,
    )
    _register_members(app)
    return app


app = build_app()
