"""Integration tests for category group routing when grouping is enabled."""

from __future__ import annotations

import os
from collections.abc import Generator
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.registry import CommandRegistry
from specfact_cli.registry.bootstrap import register_builtin_commands


@pytest.fixture(autouse=True)
def _category_grouping_enabled() -> Generator[None, None, None]:
    """Ensure category grouping is enabled and registry is fresh for routing tests."""
    with patch.dict(os.environ, {"SPECFACT_CATEGORY_GROUPING_ENABLED": "true"}, clear=False):
        CommandRegistry._clear_for_testing()
        register_builtin_commands()
        yield
    with patch.dict(os.environ, {"SPECFACT_CATEGORY_GROUPING_ENABLED": "true"}, clear=False):
        CommandRegistry._clear_for_testing()
        register_builtin_commands()


runner = CliRunner()


def test_code_analyze_help_exits_zero() -> None:
    """specfact code analyze --help returns non-error exit (CLI integration)."""
    result = runner.invoke(app, ["code", "analyze", "--help"])
    assert result.exit_code == 0, (
        f"Expected exit 0, got {result.exit_code}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "analyze" in (result.stdout or "").lower() or "usage" in (result.stdout or "").lower()


def test_backlog_help_lists_subcommands() -> None:
    """specfact backlog --help lists backlog and policy sub-commands."""
    result = runner.invoke(app, ["backlog", "--help"])
    assert result.exit_code == 0, (
        f"Expected exit 0, got {result.exit_code}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    out = (result.stdout or "").lower()
    assert "backlog" in out
    assert "policy" in out or "ceremony" in out


def test_validate_flat_command_is_not_available() -> None:
    """Flat command `specfact validate --help` is unavailable after shim removal."""
    result = runner.invoke(app, ["validate", "--help"])
    assert result.exit_code != 0
    output = ((result.stdout or "") + (result.output or "")).lower()
    assert "not installed" in output or "no such command" in output
