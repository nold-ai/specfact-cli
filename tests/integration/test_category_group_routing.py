"""Integration tests for category group routing when grouping is enabled."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.models.module_package import ModulePackageMetadata
from specfact_cli.registry import CommandRegistry
from specfact_cli.registry.bootstrap import register_builtin_commands
from specfact_cli.registry.module_discovery import DiscoveredModule


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


def _install_shadowed_module_fixture(
    monkeypatch: pytest.MonkeyPatch,
    *,
    module_id: str,
    flat_command: str,
    grouped_command: str,
) -> None:
    project_entry = DiscoveredModule(
        Path(f"/repo/.specfact/modules/{module_id.rsplit('/', 1)[-1]}"),
        ModulePackageMetadata(
            name=module_id,
            version="0.2.0",
            commands=[flat_command],
            category="validation",
            bundle_group_command=grouped_command,
        ),
        "project",
    )
    user_entry = DiscoveredModule(
        Path(f"/home/user/.specfact/modules/{module_id.rsplit('/', 1)[-1]}"),
        ModulePackageMetadata(
            name=module_id,
            version="0.1.0",
            commands=[flat_command],
            category="validation",
            bundle_group_command=grouped_command,
        ),
        "user",
    )
    monkeypatch.setattr(
        "specfact_cli.registry.module_availability.discover_all_modules_for_project_with_shadowed",
        lambda _: [project_entry, user_entry],
    )
    monkeypatch.setattr("specfact_cli.registry.module_availability.read_modules_state", dict)


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
    merged = " ".join(out.split())
    assert "module 'nold-ai/specfact-backlog' is not installed." in merged
    assert "specfact module install nold-ai/specfact-backlog" in merged
    assert "specfact init --profile <profile>" in merged


def test_validate_flat_command_is_not_available() -> None:
    """Flat command `specfact validate --help` is unavailable after shim removal."""
    result = runner.invoke(app, ["validate", "--help"])
    assert result.exit_code != 0
    output = ((result.stdout or "") + (result.output or "")).lower()
    assert "not installed" in output or "no such command" in output


@pytest.mark.parametrize(
    ("flat_command", "module_id", "grouped_command"),
    [
        ("validate", "nold-ai/specfact-codebase", "code"),
        ("plan", "nold-ai/specfact-project", "project"),
        ("analyze", "nold-ai/specfact-codebase", "code"),
        ("drift", "nold-ai/specfact-codebase", "code"),
        ("repro", "nold-ai/specfact-codebase", "code"),
        ("sync", "nold-ai/specfact-project", "project"),
        ("migrate", "nold-ai/specfact-project", "project"),
    ],
)
def test_removed_flat_commands_do_not_report_shadowed_modules(
    monkeypatch: pytest.MonkeyPatch,
    flat_command: str,
    module_id: str,
    grouped_command: str,
) -> None:
    """Removed flat commands are unknown commands, not module availability diagnostics."""
    _install_shadowed_module_fixture(
        monkeypatch,
        module_id=module_id,
        flat_command=flat_command,
        grouped_command=grouped_command,
    )

    result = runner.invoke(app, [flat_command, "--help"])

    assert result.exit_code != 0
    output = ((result.stdout or "") + (result.output or "")).lower()
    assert "shadowed" not in output
    assert "not installed" not in output
    assert "disabled" not in output
    assert "skipped" not in output
    assert "no such command" in output
