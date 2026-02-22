"""Backlog core Typer apps."""

from __future__ import annotations

import click
import typer
from typer.core import TyperGroup

from backlog_core.commands import (
    add,
    analyze_deps,
    diff,
    generate_release_notes,
    promote,
    sync,
    trace_impact,
    verify_readiness,
)
from backlog_core.commands.delta import delta_app as _delta_app


class _BacklogCoreCommandGroup(TyperGroup):
    """Impact-oriented ordering for backlog-core commands."""

    _ORDER_PRIORITY: dict[str, int] = {
        # Command groups first for discoverability.
        "delta": 10,
        # High-impact flow commands next.
        "add": 20,
        "sync": 30,
        "verify-readiness": 40,
        "analyze-deps": 50,
        "diff": 60,
        "promote": 70,
        "generate-release-notes": 80,
        "trace-impact": 90,
    }

    def list_commands(self, ctx: click.Context) -> list[str]:
        commands = list(super().list_commands(ctx))
        return sorted(commands, key=lambda name: (self._ORDER_PRIORITY.get(name, 1000), name))


backlog_app = typer.Typer(
    name="backlog",
    help="Backlog dependency analysis and sync",
    cls=_BacklogCoreCommandGroup,
)
backlog_app.command("add")(add)
backlog_app.command("analyze-deps")(analyze_deps)
backlog_app.command("trace-impact")(trace_impact)
backlog_app.command("sync")(sync)
backlog_app.command("diff")(diff)
backlog_app.command("promote")(promote)
backlog_app.command("verify-readiness")(verify_readiness)
backlog_app.command("generate-release-notes")(generate_release_notes)
backlog_app.add_typer(_delta_app, name="delta", help="Backlog delta analysis and impact tracking")

# Backward-compatible module package loader expects an `app` attribute.
app = backlog_app
