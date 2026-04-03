"""Tests for module-not-found error including corrective command.

Spec: openspec/changes/docs-new-user-onboarding/specs/docs-vibecoder-entry-path/spec.md
Tasks: 6.1 - 6.3
"""

from __future__ import annotations

import click
from typer.testing import CliRunner

from specfact_cli.cli import app


runner = CliRunner()


def _unstyled(text: str) -> str:
    return click.unstyle(text)


def test_module_not_found_error_includes_init_command() -> None:
    """When a known command group is not installed, error must include the init command."""
    result = runner.invoke(app, ["code", "review", "run"])

    output = _unstyled(result.output)

    # Must fail
    assert result.exit_code != 0

    # Must include the corrective init command
    assert "init" in output, f"Error must mention 'init' command: {output!r}"
    assert "--profile" in output or "profile" in output, f"Error must suggest --profile option: {output!r}"


def test_module_not_found_error_includes_uvx_command() -> None:
    """Module-not-found error must include uvx-compatible init command for uvx users."""
    result = runner.invoke(app, ["code", "review", "run"])

    output = _unstyled(result.output)

    assert result.exit_code != 0
    assert "specfact init" in output or "uvx" in output or "--profile" in output, (
        f"Error must include actionable init/profile guidance: {output!r}"
    )


def test_no_flat_import_in_missing_bundle_map() -> None:
    """Flat `import` is not supported; hints use `code` / `project` groups only."""
    from specfact_cli.cli import _INVOKED_TO_MARKETPLACE_MODULE

    assert "import" not in _INVOKED_TO_MARKETPLACE_MODULE
    assert _INVOKED_TO_MARKETPLACE_MODULE["project"] == "nold-ai/specfact-project"


def test_module_not_found_error_includes_init_profile_placeholder() -> None:
    """Module-not-found error for 'code' command must include init --profile guidance."""
    result = runner.invoke(app, ["code"])

    output = _unstyled(result.output)

    assert result.exit_code != 0
    assert "specfact init" in output, f"Error must mention specfact init: {output!r}"
    assert "--profile" in output or "<profile>" in output, f"Error must suggest a profile: {output!r}"
