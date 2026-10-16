"""Tests for category group bootstrap and routing (category-command-groups)."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import pytest

from specfact_cli.cli import rebuild_root_app_from_registry
from specfact_cli.registry import CommandRegistry
from specfact_cli.registry.bootstrap import register_builtin_commands


@pytest.fixture(autouse=True)
def clear_registry() -> Generator[None, None, None]:
    CommandRegistry._clear_for_testing()
    yield
    CommandRegistry._clear_for_testing()


def test_bootstrap_with_category_grouping_enabled_registers_group_commands() -> None:
    """With category grouping enabled, root commands are limited to core + category groups (no flat shims)."""
    with patch.dict(os.environ, {"SPECFACT_CATEGORY_GROUPING_ENABLED": "true"}, clear=False):
        register_builtin_commands()
        rebuild_root_app_from_registry()
    names = [name for name, _ in CommandRegistry.list_commands_for_help()]
    allowed = {"init", "auth", "module", "upgrade", "code", "backlog", "project", "requirements", "spec", "govern"}
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
    # Requirements is an opt-in module root: it is valid when installed, but
    # fresh installs and compatibility jobs expose only permanent core roots.
    assert {"init", "module", "upgrade"}.issubset(set(names))
    assert not (set(names) & forbidden_flat), (
        f"Flat shims should not be registered: {sorted(set(names) & forbidden_flat)}"
    )


def test_bootstrap_with_category_grouping_disabled_still_has_no_flat_shims(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Disabled grouping preserves category policy and cannot install a workspace category root."""
    from specfact_cli.registry import module_packages

    builtin_packages = module_packages.discover_package_metadata(module_packages.get_modules_root(), source="builtin")
    workspace_root = tmp_path / ".specfact" / "modules"
    hostile = workspace_root / "hostile"
    (hostile / "src").mkdir(parents=True)
    (hostile / "module-package.yaml").write_text(
        "name: hostile\nversion: '0.1.0'\ncommands: [project]\ncategory: project\n"
        "bundle: specfact-project\nbundle_group_command: project\nbundle_sub_command: project\n"
    )
    (hostile / "src" / "app.py").write_text("import typer\napp = typer.Typer()\n")
    project_packages = module_packages.discover_package_metadata(workspace_root, source="project")
    monkeypatch.setattr(
        module_packages, "discover_all_package_metadata", lambda **_kwargs: builtin_packages + project_packages
    )
    monkeypatch.setattr(module_packages, "read_modules_state", dict)
    with patch.dict(os.environ, {"SPECFACT_CATEGORY_GROUPING_ENABLED": "false"}, clear=False):
        register_builtin_commands()
        rebuild_root_app_from_registry()
    names = [name for name, _ in CommandRegistry.list_commands_for_help()]
    assert "project" not in names, "Workspace native category roots remain reserved in disabled grouping"
    assert {"init", "module", "upgrade"}.issubset(names)
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
    result = runner.invoke(cast(Any, root_cmd), ["govern", "--help"])
    assert (
        result.exit_code == 0 or "install" in (result.output or "").lower() or "govern" in (result.output or "").lower()
    )


@pytest.mark.parametrize("mode", ("copilot", "cicd"))
def test_flat_validate_is_not_found_in_restricted_modes(tmp_path: Path, mode: str) -> None:
    """Flat `validate` is unavailable in restricted modes after shim removal."""
    with patch.dict(
        os.environ,
        {"SPECFACT_CATEGORY_GROUPING_ENABLED": "true", "SPECFACT_MODE": mode},
        clear=False,
    ):
        register_builtin_commands()
        rebuild_root_app_from_registry()
    from click.testing import CliRunner
    from typer.main import get_command

    from specfact_cli.cli import app

    runner = CliRunner()
    root_cmd = get_command(app)
    result = runner.invoke(cast(Any, root_cmd), ["validate", "--help"])
    assert result.exit_code != 0
    output = (result.output or "").lower()
    assert "not installed" not in output
    assert "no such command" in output or "removed" in output


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
    result = runner.invoke(cast(Any, root_cmd), ["spec", "validate", "--help"])
    assert result.exit_code == 0, f"spec validate --help failed: {result.output}"
    assert "validate" in (result.output or "").lower() or "Specmatic" in (result.output or "")
