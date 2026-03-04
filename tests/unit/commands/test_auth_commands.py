"""Unit tests for auth command migration behavior."""

from __future__ import annotations

from typer.testing import CliRunner

from specfact_cli.cli import app


runner = CliRunner()


def test_top_level_auth_command_is_removed() -> None:
    """Top-level `specfact auth` command is removed from core after migration-03 task 10.6."""
    result = runner.invoke(app, ["auth", "status"])

    assert result.exit_code != 0
    assert "No such command" in result.output or "not installed" in result.output
