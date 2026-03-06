"""E2E tests for first-run init and category group availability."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.registry import CommandRegistry
from specfact_cli.registry.bootstrap import register_builtin_commands


@pytest.fixture(autouse=True)
def _category_grouping_enabled() -> None:
    """Ensure category grouping is enabled for E2E (default; set explicitly for isolation)."""
    os.environ.setdefault("SPECFACT_CATEGORY_GROUPING_ENABLED", "true")


runner = CliRunner()


def test_init_profile_solo_developer_completes_in_temp_workspace(tmp_path: Path) -> None:
    """specfact init --profile solo-developer in a temp workspace completes without error."""
    with patch(
        "specfact_cli.modules.init.src.commands.install_bundles_for_init",
        return_value=None,
    ):
        result = runner.invoke(
            app,
            ["init", "--repo", str(tmp_path), "--profile", "solo-developer"],
            catch_exceptions=False,
        )
    assert result.exit_code == 0, (
        f"Expected exit 0, got {result.exit_code}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_after_solo_developer_init_code_analyze_help_available(tmp_path: Path) -> None:
    """After init --profile solo-developer, mocked installed code bundle mounts the code group."""
    with patch(
        "specfact_cli.modules.init.src.commands.install_bundles_for_init",
        return_value=None,
    ):
        init_result = runner.invoke(
            app,
            ["init", "--repo", str(tmp_path), "--profile", "solo-developer"],
            catch_exceptions=False,
        )
    assert init_result.exit_code == 0

    CommandRegistry._clear_for_testing()
    with patch(
        "specfact_cli.registry.module_packages.get_installed_bundles",
        lambda _packages, _enabled: ["specfact-codebase"],
    ):
        register_builtin_commands()
    assert "code" in CommandRegistry.list_commands()
