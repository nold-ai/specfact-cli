"""Generic category group builder for bundle-owned command surfaces."""

from __future__ import annotations

from collections.abc import Sequence

import typer
from beartype import beartype
from icontract import ensure, require

from specfact_cli.registry.registry import CommandRegistry


@require(lambda app: app is not None)
@beartype
def _register_members(app: typer.Typer, members: Sequence[tuple[str, str]]) -> int:
    """Register member module sub-apps and return how many were added."""
    added = 0
    for display_name, cmd_name in members:
        try:
            member_app = CommandRegistry.get_module_typer(cmd_name)
            if member_app is not None:
                app.add_typer(member_app, name=display_name)
                added += 1
        except ValueError:
            continue
    return added


@require(lambda name: isinstance(name, str) and len(name) > 0)
@require(lambda help_text: isinstance(help_text, str) and len(help_text) > 0)
@ensure(lambda result: isinstance(result, typer.Typer))
@beartype
def build_member_group(
    *,
    name: str,
    help_text: str,
    members: Sequence[tuple[str, str]],
    flatten_same_name: str | None = None,
    install_hint_module: str | None = None,
) -> typer.Typer:
    """Build a lazy category group from registered member modules."""
    app = typer.Typer(name=name, help=help_text, no_args_is_help=True)
    added = _register_members(app, members)

    if added == 0 and install_hint_module:
        placeholder = typer.Typer(help=f"{help_text} (module not loaded).")

        @placeholder.command("install")
        def _install_hint() -> None:
            from specfact_cli.utils.prompts import print_warning

            print_warning(f"No {name} module loaded. Install with: specfact module install {install_hint_module}")

        app.add_typer(placeholder, name=name)

    if flatten_same_name:
        app._specfact_flatten_same_name = flatten_same_name

    return app
