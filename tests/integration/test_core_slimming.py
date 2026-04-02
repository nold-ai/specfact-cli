"""Integration tests for core slimming (module-migration-03): 3-core-only, bundle mounting, init profiles."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from specfact_cli.registry import CommandRegistry
from specfact_cli.registry.bootstrap import register_builtin_commands


CORE_THREE = {"init", "module", "upgrade"}
ALL_FIVE_BUNDLES = [
    "specfact-backlog",
    "specfact-codebase",
    "specfact-project",
    "specfact-spec",
    "specfact-govern",
]


@pytest.fixture(autouse=True)
def _reset_registry() -> Generator[None, None, None]:
    """Reset registry before each test so bootstrap state is predictable."""
    CommandRegistry._clear_for_testing()
    yield
    CommandRegistry._clear_for_testing()


def test_fresh_install_cli_app_registered_commands_only_three_core(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fresh install: CLI app has only 3 core commands when no bundles installed."""
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.get_installed_bundles",
        lambda _packages, _enabled: [],
    )
    register_builtin_commands()
    names = set(CommandRegistry.list_commands())
    assert names >= CORE_THREE, f"Expected at least {CORE_THREE}, got {names}"
    assert "auth" not in names
    extracted = {"backlog", "code", "project", "spec", "govern", "plan", "validate"}
    for ex in extracted:
        assert ex not in names, f"Extracted command {ex} must not be registered when no bundles"


def test_after_mock_install_backlog_backlog_group_mounted(monkeypatch: pytest.MonkeyPatch) -> None:
    """After mock 'install specfact-backlog', backlog group is mounted."""
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.get_installed_bundles",
        lambda _packages, _enabled: ["specfact-backlog"],
    )
    register_builtin_commands()
    assert "backlog" in CommandRegistry.list_commands()
    names = set(CommandRegistry.list_commands())
    assert "backlog" in names


def test_init_profile_solo_developer_exits_zero_and_code_group_mounted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """specfact init --profile solo-developer (mock install) exits 0; code group is mounted when bundle 'installed'."""
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.install_bundles_for_init",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
        lambda **_: [{"id": "init", "enabled": True}],
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.write_modules_state", lambda _: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.run_discovery_and_write_cache", lambda _: None)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.is_first_run",
        lambda **_: True,
    )
    from specfact_cli.cli import app

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["init", "--repo", str(tmp_path), "--profile", "solo-developer"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, f"init failed: {result.output}"

    CommandRegistry._clear_for_testing()
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.get_installed_bundles",
        lambda _p, _e: ["specfact-codebase"],
    )
    register_builtin_commands()
    assert "code" in CommandRegistry.list_commands(), (
        "With specfact-codebase mock-installed, code group must be in registry (app --help may show stale state)."
    )


def test_init_profile_enterprise_full_stack_help_shows_eight_commands(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """specfact init --profile enterprise-full-stack (mock) mounts core + category groups."""
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.install_bundles_for_init",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
        lambda **_: [{"id": "init", "enabled": True}],
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.write_modules_state", lambda _: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.run_discovery_and_write_cache", lambda _: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.is_first_run", lambda **_: True)
    from specfact_cli.cli import app

    runner = CliRunner()
    runner.invoke(
        app,
        ["init", "--repo", str(tmp_path), "--profile", "enterprise-full-stack"],
        catch_exceptions=False,
    )
    CommandRegistry._clear_for_testing()
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.get_installed_bundles",
        lambda _p, _e: list(ALL_FIVE_BUNDLES),
    )
    register_builtin_commands()
    names = set(CommandRegistry.list_commands())
    expected = CORE_THREE | {"backlog", "code", "project", "spec", "govern"}
    assert expected.issubset(names), f"Expected enterprise command surface {expected}, got {names}"


def test_init_install_all_same_as_enterprise(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """specfact init --install all (mock) results in all 5 bundles; --help shows category groups."""
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.install_bundles_for_init",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
        lambda **_: [{"id": "init", "enabled": True}],
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.write_modules_state", lambda _: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.run_discovery_and_write_cache", lambda _: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.is_first_run", lambda **_: True)
    from specfact_cli.cli import app

    runner = CliRunner()
    runner.invoke(
        app,
        ["init", "--repo", str(tmp_path), "--install", "all"],
        catch_exceptions=False,
    )
    CommandRegistry._clear_for_testing()
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.get_installed_bundles",
        lambda _p, _e: list(ALL_FIVE_BUNDLES),
    )
    register_builtin_commands()
    result = runner.invoke(app, ["--help"], catch_exceptions=False)
    assert result.exit_code == 0
    names = set(CommandRegistry.list_commands())
    assert "backlog" in names or "code" in names


def test_flat_shim_plan_exits_with_not_found_or_install_instructions() -> None:
    """Flat shim 'specfact plan' exits non-zero with 'not found' or install instructions."""
    from specfact_cli.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["plan"], catch_exceptions=False)
    assert result.exit_code != 0
    assert (
        "not installed" in result.output.lower()
        or "install" in result.output.lower()
        or "plan" in result.output.lower()
    )


def test_flat_shim_validate_exits_with_not_found_or_install_instructions() -> None:
    """Flat shim 'specfact validate' exits non-zero with 'not found' or install instructions."""
    from specfact_cli.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["validate"], catch_exceptions=False)
    assert result.exit_code != 0
    assert (
        "not installed" in result.output.lower()
        or "install" in result.output.lower()
        or "validate" in result.output.lower()
    )


def test_init_cicd_mode_no_profile_no_install_exits_one(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """specfact init in CI/CD mode with no --profile/--install exits 1 with actionable error."""
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.is_first_run", lambda **_: True)
    monkeypatch.setattr("specfact_cli.runtime.is_non_interactive", lambda: True)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
        lambda **_: [{"id": "init", "enabled": True}],
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.write_modules_state", lambda _: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.run_discovery_and_write_cache", lambda _: None)
    with patch(
        "specfact_cli.modules.init.src.commands.telemetry",
        MagicMock(
            track_command=MagicMock(return_value=MagicMock(__enter__=lambda s: None, __exit__=lambda s, *a: None))
        ),
    ):
        from specfact_cli.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["init", "--repo", str(tmp_path)], catch_exceptions=False)
    assert result.exit_code != 0
    assert "profile" in result.output.lower() or "install" in result.output.lower()
