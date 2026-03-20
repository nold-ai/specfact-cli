"""Governance category group (enforce, patch)."""

from __future__ import annotations

import typer
from beartype import beartype
from icontract import ensure, require

from specfact_cli.registry.registry import CommandRegistry


_MEMBERS = [
    ("enforce", "enforce"),
    ("patch", "patch"),
]


@require(lambda app: app is not None)
@ensure(lambda result: result is None)
@beartype
def _register_members(app: typer.Typer) -> None:
    """Register member module sub-apps (called when group is first used)."""
    for display_name, cmd_name in _MEMBERS:
        try:
            member_app = CommandRegistry.get_module_typer(cmd_name)
            if member_app is not None:
                app.add_typer(member_app, name=display_name)
        except ValueError:
            pass


@ensure(lambda result: result is not None, "Must return Typer app")
def build_app() -> typer.Typer:
    """Build the govern group Typer with members (lazy; registry must be populated)."""
    app = typer.Typer(
        name="govern",
        help="Governance and quality gates: enforce, patch.",
        no_args_is_help=True,
    )
    _register_members(app)
    return app


app = build_app()
