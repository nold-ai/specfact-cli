"""E2E checks for the canonical wow entry path (solo-developer init in a temp git repo).

Full `code review run` execution requires bundled marketplace modules; here we verify the
documented first step (init) succeeds in a real temp git workspace and that the registry
surface expected for the second step is consistent with the README/docs contract.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.registry import CommandRegistry
from specfact_cli.registry.bootstrap import register_builtin_commands


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    CommandRegistry._clear_for_testing()
    yield
    CommandRegistry._clear_for_testing()


runner = CliRunner()


def test_init_solo_developer_exits_zero_in_temp_git_repo(tmp_path: Path) -> None:
    """Documented path step 1: init --profile solo-developer in a repo (git init like a real user)."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    with (
        patch("specfact_cli.modules.init.src.commands.install_bundles_for_init", lambda *a, **k: None),
        patch(
            "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
            lambda **_: [{"id": "init", "enabled": True}],
        ),
        patch("specfact_cli.modules.init.src.commands.write_modules_state", lambda _: None),
        patch("specfact_cli.modules.init.src.commands.run_discovery_and_write_cache", lambda _: None),
        patch("specfact_cli.modules.init.src.commands.is_first_run", lambda **_: True),
    ):
        result = runner.invoke(
            app,
            ["init", "--repo", str(tmp_path), "--profile", "solo-developer"],
            catch_exceptions=False,
        )
    assert result.exit_code == 0, result.stdout + result.stderr


def test_after_wow_profile_mock_bundles_registry_lists_code_for_step_two(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Step 2 needs code + code-review bundles; registry exposes `code` group when both are 'installed'."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.install_bundles_for_init",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
        lambda **_: [{"id": "init", "enabled": True}],
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.write_modules_state", lambda _: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.run_discovery_and_write_cache", lambda _: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.is_first_run", lambda **_: True)
    init_r = runner.invoke(
        app,
        ["init", "--repo", str(tmp_path), "--profile", "solo-developer"],
        catch_exceptions=False,
    )
    assert init_r.exit_code == 0

    CommandRegistry._clear_for_testing()
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.get_installed_bundles",
        lambda _p, _e: ["specfact-codebase", "specfact-code-review"],
    )
    register_builtin_commands()
    names = CommandRegistry.list_commands()
    assert "code" in names, f"Expected code group when codebase+code-review bundles present; got {names}"
