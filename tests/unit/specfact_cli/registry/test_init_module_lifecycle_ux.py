"""Tests for init module lifecycle UX: listing and interactive/non-interactive selection."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from specfact_cli.cli import app
from specfact_cli.registry.module_packages import ModulePackageMetadata


runner = CliRunner()


def test_init_list_modules_shows_enabled_disabled(tmp_path: Path, monkeypatch) -> None:
    """`specfact init --list-modules` prints discovered module statuses and exits."""

    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
        lambda enable_ids=None, disable_ids=None: [
            {"id": "sync", "version": "0.1.0", "enabled": True},
            {"id": "generate", "version": "0.1.0", "enabled": False},
        ],
    )

    result = runner.invoke(app, ["init", "--repo", str(tmp_path), "--list-modules"])

    assert result.exit_code == 0
    assert "sync" in result.stdout
    assert "generate" in result.stdout
    assert "enabled" in result.stdout.lower()
    assert "disabled" in result.stdout.lower()


def test_init_non_interactive_bare_enable_module_requires_id(tmp_path: Path, monkeypatch) -> None:
    """Non-interactive mode rejects bare --enable-module and requires explicit id."""

    monkeypatch.setattr("specfact_cli.modules.init.src.commands.is_non_interactive", lambda: True)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands._select_module_ids_interactive",
        lambda action, modules: (_ for _ in ()).throw(AssertionError("must not prompt in non-interactive mode")),
    )

    result = runner.invoke(app, ["--no-interactive", "init", "--repo", str(tmp_path), "--enable-module"])
    assert result.exit_code == 1
    assert "--enable-module <id>" in result.stdout or "--disable-module <id>" in result.stdout


def test_init_enable_module_bare_interactive_adds_selected_module(tmp_path: Path, monkeypatch) -> None:
    """Bare --enable-module in interactive mode triggers selector and applies selected ids."""

    monkeypatch.setattr("specfact_cli.modules.init.src.commands.is_non_interactive", lambda: False)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands._select_module_ids_interactive",
        lambda action, modules: ["generate"],
    )

    observed_enable_ids: list[str] = []

    def _fake_get_discovered_modules_for_state(enable_ids=None, disable_ids=None):
        nonlocal observed_enable_ids
        observed_enable_ids = list(enable_ids or [])
        return [
            {"id": "sync", "version": "0.1.0", "enabled": True},
            {"id": "generate", "version": "0.1.0", "enabled": True},
        ]

    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
        _fake_get_discovered_modules_for_state,
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.write_modules_state", lambda modules: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.run_discovery_and_write_cache", lambda version: None)

    result = runner.invoke(app, ["init", "--repo", str(tmp_path), "--enable-module"])

    assert result.exit_code == 0
    assert "generate" in observed_enable_ids


def test_init_disable_module_does_not_run_ide_setup(tmp_path: Path, monkeypatch) -> None:
    """Module state updates should not trigger template copy or IDE setup side effects."""

    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
        lambda enable_ids=None, disable_ids=None: [
            {"id": "upgrade", "version": "0.1.0", "enabled": False},
        ],
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.write_modules_state", lambda modules: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.run_discovery_and_write_cache", lambda version: None)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.validate_disable_safe",
        lambda disable_ids, packages, enabled_map: {},
    )
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.discover_package_metadata",
        lambda modules_root: [],
    )

    def _fail_copy(*args, **kwargs):
        raise AssertionError("copy_templates_to_ide must not be called for module-state-only operations")

    monkeypatch.setattr("specfact_cli.modules.init.src.commands.copy_templates_to_ide", _fail_copy)

    result = runner.invoke(app, ["init", "--repo", str(tmp_path), "--disable-module", "upgrade"])

    assert result.exit_code == 0


def test_init_bootstrap_only_does_not_run_ide_setup(tmp_path: Path, monkeypatch) -> None:
    """Top-level init should not run template copy; it should stay bootstrap-only."""

    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
        lambda enable_ids=None, disable_ids=None: [
            {"id": "sync", "version": "0.1.0", "enabled": True},
        ],
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.write_modules_state", lambda modules: None)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.run_discovery_and_write_cache", lambda version: None)

    def _fail_copy(*args, **kwargs):
        raise AssertionError("copy_templates_to_ide must not be called by top-level init")

    monkeypatch.setattr("specfact_cli.modules.init.src.commands.copy_templates_to_ide", _fail_copy)

    result = runner.invoke(app, ["init", "--repo", str(tmp_path)])
    assert result.exit_code == 0
    assert "Use `specfact init ide`" in result.stdout


def test_init_force_disable_cascades_to_dependents(tmp_path: Path, monkeypatch) -> None:
    """Force-disabling a dependency provider should cascade-disable dependents."""

    monkeypatch.setattr("specfact_cli.modules.init.src.commands.is_non_interactive", lambda: True)
    packages = [
        (
            Path("/tmp/plan"),
            ModulePackageMetadata(name="plan", version="0.1.0", commands=["plan"], module_dependencies=["sync"]),
        ),
        (
            Path("/tmp/sync"),
            ModulePackageMetadata(name="sync", version="0.1.0", commands=["sync"], module_dependencies=[]),
        ),
    ]
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.discover_package_metadata", lambda root: packages)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.read_modules_state", dict)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.run_discovery_and_write_cache", lambda version: None)

    observed_disable_ids: list[str] = []

    def _fake_get_discovered_modules_for_state(enable_ids=None, disable_ids=None):
        nonlocal observed_disable_ids
        observed_disable_ids = list(disable_ids or [])
        return [
            {"id": "plan", "version": "0.1.0", "enabled": False},
            {"id": "sync", "version": "0.1.0", "enabled": False},
        ]

    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
        _fake_get_discovered_modules_for_state,
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.write_modules_state", lambda modules: None)

    result = runner.invoke(app, ["init", "--repo", str(tmp_path), "--disable-module", "sync", "--force"])
    assert result.exit_code == 0
    assert "sync" in observed_disable_ids
    assert "plan" in observed_disable_ids


def test_init_force_enable_cascades_to_dependencies(tmp_path: Path, monkeypatch) -> None:
    """Force-enabling a module should auto-enable transitive dependencies."""

    monkeypatch.setattr("specfact_cli.modules.init.src.commands.is_non_interactive", lambda: True)
    packages = [
        (
            Path("/tmp/plan"),
            ModulePackageMetadata(name="plan", version="0.1.0", commands=["plan"], module_dependencies=["sync"]),
        ),
        (
            Path("/tmp/sync"),
            ModulePackageMetadata(name="sync", version="0.1.0", commands=["sync"], module_dependencies=[]),
        ),
    ]
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.discover_package_metadata", lambda root: packages)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.read_modules_state", dict)
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.run_discovery_and_write_cache", lambda version: None)

    observed_enable_ids: list[str] = []

    def _fake_get_discovered_modules_for_state(enable_ids=None, disable_ids=None):
        nonlocal observed_enable_ids
        observed_enable_ids = list(enable_ids or [])
        return [
            {"id": "plan", "version": "0.1.0", "enabled": True},
            {"id": "sync", "version": "0.1.0", "enabled": True},
        ]

    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.get_discovered_modules_for_state",
        _fake_get_discovered_modules_for_state,
    )
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.write_modules_state", lambda modules: None)

    result = runner.invoke(app, ["init", "--repo", str(tmp_path), "--enable-module", "plan", "--force"])
    assert result.exit_code == 0
    assert "plan" in observed_enable_ids
    assert "sync" in observed_enable_ids


def test_init_enable_without_force_blocks_when_dependency_disabled(tmp_path: Path, monkeypatch) -> None:
    """Enable should fail without force when required dependency is disabled."""

    monkeypatch.setattr("specfact_cli.modules.init.src.commands.is_non_interactive", lambda: True)
    packages = [
        (
            Path("/tmp/plan"),
            ModulePackageMetadata(name="plan", version="0.1.0", commands=["plan"], module_dependencies=["sync"]),
        ),
        (
            Path("/tmp/sync"),
            ModulePackageMetadata(name="sync", version="0.1.0", commands=["sync"], module_dependencies=[]),
        ),
    ]
    monkeypatch.setattr("specfact_cli.modules.init.src.commands.discover_package_metadata", lambda root: packages)
    monkeypatch.setattr(
        "specfact_cli.modules.init.src.commands.read_modules_state", lambda: {"sync": {"enabled": False}}
    )

    result = runner.invoke(app, ["init", "--repo", str(tmp_path), "--enable-module", "plan"])

    assert result.exit_code == 1
    assert "Cannot enable 'plan'" in result.stdout
    assert "--force" in result.stdout
