"""Integration tests for auth command migration behavior."""

from __future__ import annotations

from typer.testing import CliRunner

from specfact_cli.cli import app


runner = CliRunner()


def test_top_level_auth_command_not_available_after_core_slimming() -> None:
    """`specfact auth` should fail once auth is moved to backlog bundle."""
    result = runner.invoke(app, ["auth", "status"])

    assert result.exit_code != 0
    assert "No such command" in result.output or "not installed" in result.output
