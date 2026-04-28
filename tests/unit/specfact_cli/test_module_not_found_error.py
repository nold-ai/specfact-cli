"""Tests for module-not-found error including corrective command.

Spec: openspec/changes/docs-new-user-onboarding/specs/docs-vibecoder-entry-path/spec.md
Tasks: 6.1 - 6.3
"""

from __future__ import annotations

import click
import pytest
from typer.testing import CliRunner

from specfact_cli.registry.module_availability import ModuleAvailability, ModuleAvailabilityStatus


runner = CliRunner()


def _unstyled(text: str) -> str:
    return click.unstyle(text)


@pytest.fixture
def absent_module(monkeypatch):
    monkeypatch.setattr(
        "specfact_cli.cli.classify_module_availability",
        lambda **kwargs: ModuleAvailability(
            status=ModuleAvailabilityStatus.ABSENT,
            module_id=kwargs.get("module_id"),
            reason="not installed",
            recovery_command=f"specfact module install {kwargs.get('module_id')}",
        ),
        raising=False,
    )


def test_module_not_found_error_includes_init_command(absent_module, capsys) -> None:
    """When a known command group is not installed, error must include the init command."""
    from specfact_cli.cli import _print_missing_bundle_command_help

    _print_missing_bundle_command_help("code")
    output = _unstyled(capsys.readouterr().out)

    # Must include the corrective init command
    assert "init" in output, f"Error must mention 'init' command: {output!r}"
    assert "--profile" in output or "profile" in output, f"Error must suggest --profile option: {output!r}"


def test_module_not_found_error_includes_uvx_command(absent_module, capsys) -> None:
    """Module-not-found error must include uvx-compatible init command for uvx users."""
    from specfact_cli.cli import _print_missing_bundle_command_help

    _print_missing_bundle_command_help("code")
    output = _unstyled(capsys.readouterr().out)

    assert "specfact init" in output or "uvx" in output or "--profile" in output, (
        f"Error must include actionable init/profile guidance: {output!r}"
    )


def test_no_flat_import_in_missing_bundle_map() -> None:
    """Flat `import` is not supported; hints use `code` / `project` groups only."""
    from specfact_cli.cli import _INVOKED_TO_MARKETPLACE_MODULE

    assert "import" not in _INVOKED_TO_MARKETPLACE_MODULE
    assert _INVOKED_TO_MARKETPLACE_MODULE["project"] == "nold-ai/specfact-project"


def test_module_not_found_error_includes_init_profile_placeholder(absent_module, capsys) -> None:
    """Module-not-found error for 'code' command must include init --profile guidance."""
    from specfact_cli.cli import _print_missing_bundle_command_help

    _print_missing_bundle_command_help("code")
    output = _unstyled(capsys.readouterr().out)

    assert "specfact init" in output, f"Error must mention specfact init: {output!r}"
    assert "--profile" in output or "<profile>" in output, f"Error must suggest a profile: {output!r}"


def test_module_not_found_error_reports_disabled_installed_module(monkeypatch, capsys) -> None:
    """Missing command UX must not call disabled installed modules uninstalled."""
    from specfact_cli.cli import _print_missing_bundle_command_help

    monkeypatch.setattr(
        "specfact_cli.cli.classify_module_availability",
        lambda **_: ModuleAvailability(
            status=ModuleAvailabilityStatus.DISABLED,
            module_id="nold-ai/specfact-codebase",
            source="user",
            reason="disabled in modules.json",
            recovery_command="specfact module enable nold-ai/specfact-codebase",
        ),
        raising=False,
    )

    _print_missing_bundle_command_help("code")
    output = _unstyled(capsys.readouterr().out)
    normalized_output = " ".join(output.split())

    assert "is installed but disabled" in output
    assert "specfact module enable nold-ai/specfact-codebase" in normalized_output
    assert "is not installed" not in output
