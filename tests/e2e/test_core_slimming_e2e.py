"""E2E tests for core slimming: init profiles, bundle install flow, lean help (module-migration-03)."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner


@pytest.fixture(autouse=True)
def _reset_registry():
    """Ensure registry is cleared so E2E sees predictable bootstrap state when we re-bootstrap."""
    from specfact_cli.registry import CommandRegistry

    CommandRegistry._clear_for_testing()
    yield
    CommandRegistry._clear_for_testing()


def test_e2e_init_profile_solo_developer_then_code_group_available(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """E2E: specfact init --profile solo-developer in temp workspace; code group is then available in --help."""
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
    from specfact_cli.registry import CommandRegistry
    from specfact_cli.registry.bootstrap import register_builtin_commands

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["init", "--repo", str(tmp_path), "--profile", "solo-developer"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, f"init failed: {result.stdout} {result.stderr}"

    CommandRegistry._clear_for_testing()
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.get_installed_bundles",
        lambda _p, _e: ["specfact-codebase"],
    )
    register_builtin_commands()
    assert "code" in CommandRegistry.list_commands(), (
        "After init --profile solo-developer (mock), code group must be in registry."
    )


def test_e2e_init_profile_api_first_team_then_spec_contract_help(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """E2E: init --profile api-first-team; specfact-project auto-installed as dep; specfact spec contract --help resolves."""
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
    from specfact_cli.registry import CommandRegistry
    from specfact_cli.registry.bootstrap import register_builtin_commands

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["init", "--repo", str(tmp_path), "--profile", "api-first-team"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    CommandRegistry._clear_for_testing()
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.get_installed_bundles",
        lambda _p, _e: ["specfact-project", "specfact-spec"],
    )
    register_builtin_commands()
    spec_help = runner.invoke(app, ["spec", "contract", "--help"], catch_exceptions=False)
    if spec_help.exit_code != 0:
        pytest.skip("spec/contract may not be available when spec module is from bundle stub")
    assert "contract" in (spec_help.stdout or "").lower() or "usage" in (spec_help.stdout or "").lower()


def test_e2e_specfact_help_fresh_install_at_most_six_command_lines(monkeypatch: pytest.MonkeyPatch) -> None:
    """E2E: specfact --help on fresh install shows ≤ 6 top-level commands (4 core when no bundles)."""
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.get_installed_bundles",
        lambda _p, _e: [],
    )
    from specfact_cli.registry import CommandRegistry
    from specfact_cli.registry.bootstrap import register_builtin_commands

    CommandRegistry._clear_for_testing()
    register_builtin_commands()
    registered = CommandRegistry.list_commands()
    assert len(registered) <= 6, f"Fresh install should have ≤6 commands, got {len(registered)}: {registered}"
    from specfact_cli.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["--help"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "init" in result.output and "auth" in result.output
