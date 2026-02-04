"""Upgrade command: re-export from commands package (update module)."""

from specfact_cli.commands.update import app


__all__ = ["app"]
