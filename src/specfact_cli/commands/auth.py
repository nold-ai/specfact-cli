"""Backward-compatible app shim. Implementation moved to modules/auth/."""

from specfact_cli.modules.auth.src.commands import app


__all__ = ["app"]
