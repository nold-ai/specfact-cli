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


def test_code_group_is_registered_when_codebase_bundle_is_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Code group is mounted only when the codebase bundle is installed."""
    CommandRegistry._clear_for_testing()
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.get_installed_bundles",
        lambda _packages, _enabled: ["specfact-codebase"],
    )
    register_builtin_commands()
    assert "code" in CommandRegistry.list_commands()


def test_backlog_help_lists_subcommands() -> None:
    """specfact backlog --help shows subcommands when installed, otherwise actionable install guidance."""
    result = runner.invoke(app, ["backlog", "--help"])
    out = (result.stdout or "").lower()
    if result.exit_code == 0:
        assert "backlog" in out
        assert "policy" in out or "ceremony" in out
        return
    assert "command 'backlog' is not installed." in out
    assert "specfact init --profile <profile>" in out
    assert "module install <bundle>" in out


def test_validate_flat_command_is_not_available() -> None:
    """Flat command `specfact validate --help` is unavailable after shim removal."""
    result = runner.invoke(app, ["validate", "--help"])
    assert result.exit_code != 0
    output = ((result.stdout or "") + (result.output or "")).lower()
    assert "not installed" in output or "no such command" in output
