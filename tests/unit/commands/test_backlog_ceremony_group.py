"""Tests for backlog ceremony command group aliases."""

from __future__ import annotations

from typer.testing import CliRunner

from specfact_cli.modules.backlog.src import commands as backlog_commands


runner = CliRunner()


def test_backlog_ceremony_group_exposes_standup_and_refinement() -> None:
    """`specfact backlog ceremony -h` lists ceremony-focused subcommands."""
    result = runner.invoke(backlog_commands.app, ["ceremony", "-h"])
    assert result.exit_code == 0
    assert "standup" in result.stdout
    assert "refinement" in result.stdout
    assert "planning" in result.stdout
    assert "flow" in result.stdout
    assert "pi-summary" in result.stdout


def test_ceremony_standup_delegates_to_backlog_daily(monkeypatch) -> None:
    """`backlog ceremony standup` delegates to daily behavior."""
    monkeypatch.setattr(backlog_commands, "_fetch_backlog_items", lambda *args, **kwargs: [])
    result = runner.invoke(backlog_commands.app, ["ceremony", "standup", "github"])
    assert result.exit_code == 0
    assert "No backlog items found." in result.stdout


def test_ceremony_refinement_delegates_to_backlog_refine(monkeypatch) -> None:
    """`backlog ceremony refinement` delegates to refine behavior."""
    monkeypatch.setattr(backlog_commands, "_fetch_backlog_items", lambda *args, **kwargs: [])
    result = runner.invoke(backlog_commands.app, ["ceremony", "refinement", "github"])
    assert result.exit_code == 0
    assert "No backlog items found." in result.stdout


def test_ceremony_planning_shows_clear_message_when_target_command_missing() -> None:
    """`backlog ceremony planning` fails clearly when delegated command is unavailable."""
    result = runner.invoke(backlog_commands.app, ["ceremony", "planning", "github"])
    assert result.exit_code != 0
    assert "requires an installed backlog module" in result.stdout
    assert "sprint-summary" in result.stdout
