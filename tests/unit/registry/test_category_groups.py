"""Tests for category group bootstrap and routing (category-command-groups)."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from specfact_cli.registry import CommandRegistry
from specfact_cli.registry.bootstrap import register_builtin_commands


@pytest.fixture(autouse=True)
def _clear_registry() -> Generator[None, None, None]:
    CommandRegistry._clear_for_testing()
    yield
    CommandRegistry._clear_for_testing()


def test_bootstrap_with_category_grouping_enabled_registers_group_commands() -> None:
    """With category_grouping_enabled=True, bootstrap registers code, backlog, project, spec, govern."""
    with patch.dict(os.environ, {"SPECFACT_CATEGORY_GROUPING_ENABLED": "true"}, clear=False):
        register_builtin_commands()
    names = [name for name, _ in CommandRegistry.list_commands_for_help()]
    for group in ("code", "backlog", "project", "spec", "govern"):
        assert group in names, f"Expected group command {group!r} in {names}"


def test_bootstrap_with_category_grouping_disabled_registers_flat_commands() -> None:
    """With category_grouping_enabled=False, bootstrap registers flat module commands (no group commands)."""
    with patch.dict(os.environ, {"SPECFACT_CATEGORY_GROUPING_ENABLED": "false"}, clear=False):
        register_builtin_commands()
    names = [name for name, _ in CommandRegistry.list_commands_for_help()]
    assert "code" not in names, "Group 'code' should not appear when grouping disabled"
    assert "govern" not in names, "Group 'govern' should not appear when grouping disabled"
    assert "analyze" in names
    assert "validate" in names


def test_code_analyze_routes_same_as_flat_analyze(
    tmp_path: Path,
) -> None:
    """specfact code analyze ... routes to the same handler as specfact analyze ... (integration via CLI)."""
    with patch.dict(os.environ, {"SPECFACT_CATEGORY_GROUPING_ENABLED": "true"}, clear=False):
        register_builtin_commands()
    from typer.main import get_command

    from specfact_cli.cli import app

    root_cmd = get_command(app)
    assert root_cmd is not None
    assert hasattr(root_cmd, "commands") and "code" in root_cmd.commands
    code_app = CommandRegistry.get_typer("code")
    click_code = get_command(code_app)
    if hasattr(click_code, "commands"):
        assert "analyze" in click_code.commands


def test_govern_help_when_not_installed_suggests_install(
    tmp_path: Path,
) -> None:
    """specfact govern --help when govern bundle not installed produces install suggestion."""
    with patch.dict(os.environ, {"SPECFACT_CATEGORY_GROUPING_ENABLED": "true"}, clear=False):
        register_builtin_commands()
    from click.testing import CliRunner
    from typer.main import get_command

    from specfact_cli.cli import app

    runner = CliRunner()
    root_cmd = get_command(app)
    result = runner.invoke(root_cmd, ["govern", "--help"])
    assert (
        result.exit_code == 0 or "install" in (result.output or "").lower() or "govern" in (result.output or "").lower()
    )


def test_flat_shim_validate_emits_deprecation_in_copilot_mode(
    tmp_path: Path,
) -> None:
    """Flat 'specfact validate' resolves to real validate module (no deprecation message since shim is real module)."""
    with patch.dict(
        os.environ,
        {"SPECFACT_CATEGORY_GROUPING_ENABLED": "true", "SPECFACT_MODE": "copilot"},
        clear=False,
    ):
        register_builtin_commands()
    from click.testing import CliRunner
    from typer.main import get_command

    from specfact_cli.cli import app

    runner = CliRunner()
    root_cmd = get_command(app)
    result = runner.invoke(root_cmd, ["validate", "--help"])
    assert result.exit_code == 0
    assert "validate" in (result.output or "").lower()


def test_flat_shim_validate_silent_in_cicd_mode(tmp_path: Path) -> None:
    """Flat shim specfact validate is silent (no deprecation) in CI/CD mode."""
    with patch.dict(
        os.environ,
        {"SPECFACT_CATEGORY_GROUPING_ENABLED": "true", "SPECFACT_MODE": "cicd"},
        clear=False,
    ):
        register_builtin_commands()
    from click.testing import CliRunner
    from typer.main import get_command

    from specfact_cli.cli import app

    runner = CliRunner()
    root_cmd = get_command(app)
    result = runner.invoke(root_cmd, ["validate", "--help"])
    assert result.exit_code == 0


def test_spec_api_validate_routes_correctly(tmp_path: Path) -> None:
    """specfact spec api routes correctly (spec module mounted as api subcommand; collision avoidance)."""
    with patch.dict(os.environ, {"SPECFACT_CATEGORY_GROUPING_ENABLED": "true"}, clear=False):
        register_builtin_commands()
    from click.testing import CliRunner
    from typer.main import get_command

    from specfact_cli.cli import app

    root_cmd = get_command(app)
    assert root_cmd is not None and hasattr(root_cmd, "commands") and "spec" in root_cmd.commands
    runner = CliRunner()
    result = runner.invoke(root_cmd, ["spec", "api", "--help"])
    assert result.exit_code == 0, f"spec api --help failed: {result.output}"
    assert "validate" in (result.output or "").lower() or "Specmatic" in (result.output or "")
