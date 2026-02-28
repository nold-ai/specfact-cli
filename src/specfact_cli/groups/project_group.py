"""Project lifecycle category group (project, plan, import, sync, migrate)."""

from __future__ import annotations

import typer
from beartype import beartype
from icontract import ensure, require

from specfact_cli.registry.registry import CommandRegistry


_MEMBERS = [
    ("project", "project"),
    ("plan", "plan"),
    ("import", "import"),
    ("sync", "sync"),
    ("migrate", "migrate"),
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
    """Build the project group Typer with members (lazy; registry must be populated)."""
    app = typer.Typer(
        name="project",
        help="Project lifecycle commands.",
        no_args_is_help=True,
    )
    _register_members(app)
    app._specfact_flatten_same_name = "project"
    return app


app = build_app()
