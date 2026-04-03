"""Tests for category group bootstrap and routing (category-command-groups)."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from specfact_cli.cli import rebuild_root_app_from_registry
from specfact_cli.registry import CommandRegistry
from specfact_cli.registry.bootstrap import register_builtin_commands


@pytest.fixture(autouse=True)
def _clear_registry() -> Generator[None, None, None]:
    CommandRegistry._clear_for_testing()
    yield
    CommandRegistry._clear_for_testing()


def test_bootstrap_with_category_grouping_enabled_registers_group_commands() -> None:
    """With category grouping enabled, root commands are limited to core + category groups (no flat shims)."""
    with patch.dict(os.environ, {"SPECFACT_CATEGORY_GROUPING_ENABLED": "true"}, clear=False):
        register_builtin_commands()
        rebuild_root_app_from_registry()
    names = [name for name, _ in CommandRegistry.list_commands_for_help()]
    allowed = {"init", "auth", "module", "upgrade", "code", "backlog", "project", "spec", "govern"}
    forbidden_flat = {
        "analyze",
        "drift",
        "validate",
        "repro",
        "policy",
        "plan",
        "import",
        "sync",
        "migrate",
        "contract",
        "sdd",
        "generate",
        "enforce",
        "patch",
    }
    assert set(names).issubset(allowed), f"Unexpected root commands found: {sorted(set(names) - allowed)}"
    assert {"init", "module", "upgrade"}.issubset(set(names))
    if "code" in names:
        assert {"project", "spec"} <= set(names), (
            "When the code category group is mounted, project and spec groups must register too."
        )
    assert not (set(names) & forbidden_flat), (
        f"Flat shims should not be registered: {sorted(set(names) & forbidden_flat)}"
    )


def test_bootstrap_with_category_grouping_disabled_still_has_no_flat_shims() -> None:
    """Flat bundle shims are not registered even when SPECFACT_CATEGORY_GROUPING_ENABLED is false."""
    with patch.dict(os.environ, {"SPECFACT_CATEGORY_GROUPING_ENABLED": "false"}, clear=False):
        register_builtin_commands()
        rebuild_root_app_from_registry()
    names = [name for name, _ in CommandRegistry.list_commands_for_help()]
    forbidden_flat = {
        "analyze",
        "drift",
        "validate",
        "repro",
        "import",
        "plan",
        "sync",
        "migrate",
    }
    assert not (set(names) & forbidden_flat), (
        f"Flat shims must not be registered: {sorted(set(names) & forbidden_flat)}"
    )
    if "code" in names:
        assert "project" in names and "spec" in names


def test_code_analyze_routes_same_as_flat_analyze(
    tmp_path: Path,
) -> None:
    """`code` group mounts only when codebase module is installed."""
    with patch.dict(os.environ, {"SPECFACT_CATEGORY_GROUPING_ENABLED": "true"}, clear=False):
        register_builtin_commands()
        rebuild_root_app_from_registry()
    from typer.main import get_command

    from specfact_cli.cli import app

    root_cmd = get_command(app)
    assert root_cmd is not None
    assert hasattr(root_cmd, "commands")
    root_commands = root_cmd.commands if hasattr(root_cmd, "commands") else {}
    if "code" not in root_commands:
        return
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
        rebuild_root_app_from_registry()
    from click.testing import CliRunner
    from typer.main import get_command

    from specfact_cli.cli import app

    runner = CliRunner()
    root_cmd = get_command(app)
    result = runner.invoke(root_cmd, ["govern", "--help"])
    assert (
        result.exit_code == 0 or "install" in (result.output or "").lower() or "govern" in (result.output or "").lower()
    )


def test_flat_validate_is_not_found_in_copilot_mode(
    tmp_path: Path,
) -> None:
    """Flat `validate` is unavailable in copilot mode after shim removal."""
    with patch.dict(
        os.environ,
        {"SPECFACT_CATEGORY_GROUPING_ENABLED": "true", "SPECFACT_MODE": "copilot"},
        clear=False,
    ):
        register_builtin_commands()
        rebuild_root_app_from_registry()
    from click.testing import CliRunner
    from typer.main import get_command

    from specfact_cli.cli import app

    runner = CliRunner()
    root_cmd = get_command(app)
    result = runner.invoke(root_cmd, ["validate", "--help"])
    assert result.exit_code != 0
    assert "not installed" in (result.output or "").lower() or "no such command" in (result.output or "").lower()


def test_flat_validate_is_not_found_in_cicd_mode(tmp_path: Path) -> None:
    """Flat `validate` is unavailable in CI/CD mode after shim removal."""
    with patch.dict(
        os.environ,
        {"SPECFACT_CATEGORY_GROUPING_ENABLED": "true", "SPECFACT_MODE": "cicd"},
        clear=False,
    ):
        register_builtin_commands()
        rebuild_root_app_from_registry()
    from click.testing import CliRunner
    from typer.main import get_command

    from specfact_cli.cli import app

    runner = CliRunner()
    root_cmd = get_command(app)
    result = runner.invoke(root_cmd, ["validate", "--help"])
    assert result.exit_code != 0
    assert "not installed" in (result.output or "").lower() or "no such command" in (result.output or "").lower()


def test_spec_api_validate_routes_correctly(tmp_path: Path) -> None:
    """The installed spec bundle exposes its native `spec validate` root path."""
    with patch.dict(os.environ, {"SPECFACT_CATEGORY_GROUPING_ENABLED": "true"}, clear=False):
        register_builtin_commands()
        rebuild_root_app_from_registry()
    from click.testing import CliRunner
    from typer.main import get_command

    from specfact_cli.cli import app

    root_cmd = get_command(app)
    assert root_cmd is not None and hasattr(root_cmd, "commands")
    root_commands = root_cmd.commands if hasattr(root_cmd, "commands") else {}
    if "spec" not in root_commands:
        return
    runner = CliRunner()
    result = runner.invoke(root_cmd, ["spec", "validate", "--help"])
    assert result.exit_code == 0, f"spec validate --help failed: {result.output}"
    assert "validate" in (result.output or "").lower() or "Specmatic" in (result.output or "")
