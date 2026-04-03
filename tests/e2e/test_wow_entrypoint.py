"""E2E checks for the canonical wow entry path (solo-developer init in a temp git repo).

Full `code review run` execution requires bundled marketplace modules; here we verify the
documented first step (init) succeeds in a real temp git workspace and that the registry
surface expected for the second step is consistent with the README/docs contract.
"""

from __future__ import annotations

import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.registry import CommandRegistry
from specfact_cli.registry.bootstrap import register_builtin_commands


@pytest.fixture(autouse=True)
def _reset_registry() -> Iterator[None]:
    CommandRegistry._clear_for_testing()
    yield
    CommandRegistry._clear_for_testing()


runner = CliRunner()


@pytest.fixture
def patch_init_wow_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub init side effects so profile install can be exercised without real bundle I/O."""
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.install_bundles_for_init",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
        lambda **_: [{"id": "init", "enabled": True}],
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.write_modules_state", lambda _: None)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.run_discovery_and_write_cache",
        lambda _: None,
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.is_first_run", lambda **_: True)


def test_init_solo_developer_exits_zero_in_temp_git_repo(tmp_path: Path, patch_init_wow_dependencies: None) -> None:
    """Documented path step 1: init --profile solo-developer in a repo (git init like a real user)."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    result = runner.invoke(
        app,
        ["init", "--repo", str(tmp_path), "--profile", "solo-developer"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stdout + result.stderr


def test_after_wow_profile_mock_bundles_registry_lists_code_for_step_two(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, patch_init_wow_dependencies: None
) -> None:
    """Step 2 needs code + code-review bundles; registry exposes `code` group when both are 'installed'."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
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


def test_after_wow_profile_only_code_review_does_not_expose_code_command(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, patch_init_wow_dependencies: None
) -> None:
    """Category groups map specfact-codebase -> `code`; code-review alone must not mount that group."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    init_r = runner.invoke(
        app,
        ["init", "--repo", str(tmp_path), "--profile", "solo-developer"],
        catch_exceptions=False,
    )
    assert init_r.exit_code == 0

    CommandRegistry._clear_for_testing()
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.get_installed_bundles",
        lambda _p, _e: ["specfact-code-review"],
    )
    register_builtin_commands()
    names = CommandRegistry.list_commands()
    assert "code" not in names, f"Expected no `code` group when only specfact-code-review is installed; got {names}"
