"""Backlog category group (backlog, policy).

CrossHair: skip (Typer app wiring and lazy registry lookups are side-effectful by design)
"""

from __future__ import annotations

import typer
from beartype import beartype
from icontract import ensure, require

from specfact_cli.common import get_bridge_logger
from specfact_cli.registry.registry import CommandRegistry


_MEMBERS = [
    ("backlog", "backlog"),
    ("policy", "policy"),
]


@require(lambda app: app is not None)
@ensure(lambda result: result is None)
@beartype
def _register_members(app: typer.Typer) -> None:
    """Register member module sub-apps (called when group is first used)."""
    logger = get_bridge_logger(__name__)
    added = 0
    for display_name, cmd_name in _MEMBERS:
        try:
            member_app = CommandRegistry.get_module_typer(cmd_name)
            if member_app is not None:
                app.add_typer(member_app, name=display_name)
                added += 1
        except ValueError as exc:
            logger.debug("Backlog group: skipping %s (%s)", cmd_name, exc)
        except Exception as exc:
            logger.debug("Backlog group: failed to load %s: %s", cmd_name, exc)
    if added == 0:
        placeholder = typer.Typer(help="Backlog and policy commands (module not loaded).")

        @placeholder.command("install")
        def _install_hint() -> None:
            from specfact_cli.utils.prompts import print_warning

            print_warning("No backlog module loaded. Install with: specfact module install nold-ai/specfact-backlog")

        app.add_typer(placeholder, name="backlog")


def build_app() -> typer.Typer:
    """Build the backlog group Typer with members (lazy; registry must be populated)."""
    app = typer.Typer(
        name="backlog",
        help="Backlog and policy commands.",
        no_args_is_help=True,
    )
    _register_members(app)
    app._specfact_flatten_same_name = "backlog"
    return app


app = build_app()
