"""Spec category group (contract, api, sdd, generate) — spec module mounted as 'api' to avoid collision."""

from __future__ import annotations

import typer
from beartype import beartype
from icontract import ensure, require

from specfact_cli.registry.registry import CommandRegistry


_MEMBERS = [
    ("contract", "contract"),
    ("api", "spec"),
    ("sdd", "sdd"),
    ("generate", "generate"),
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


def build_app() -> typer.Typer:
    """Build the spec group Typer with members (lazy; registry must be populated)."""
    app = typer.Typer(
        name="spec",
        help="Spec and contract commands: contract, api, sdd, generate.",
        no_args_is_help=True,
    )
    _register_members(app)
    return app


app = build_app()
