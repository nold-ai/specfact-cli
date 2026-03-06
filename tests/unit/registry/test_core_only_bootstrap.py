"""Tests for 3-core-only bootstrap and installed-bundle category mounting (module-migration-03)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from specfact_cli.registry import CommandRegistry
from specfact_cli.registry.bootstrap import register_builtin_commands


CORE_THREE = {"init", "module", "upgrade"}
EXTRACTED_17_NAMES = {
    "project",
    "plan",
    "backlog",
    "code",
    "spec",
    "govern",
    "validate",
    "contract",
    "sdd",
    "generate",
    "enforce",
    "patch",
    "migrate",
    "repro",
    "drift",
    "analyze",
    "policy",
}


def _make_core_metadata(name: str, commands: list[str] | None = None):
    from specfact_cli.models.module_package import ModulePackageMetadata

    cmd = commands or [name]
    return ModulePackageMetadata(
        name=name,
        version="0.40.0",
        commands=cmd,
        category="core",
        source="builtin",
    )


@pytest.fixture(autouse=True)
def _clear_registry():
    CommandRegistry._clear_for_testing()
    yield
    CommandRegistry._clear_for_testing()


def test_register_builtin_commands_registers_only_three_core_when_discovery_returns_three(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """After bootstrap with only 3 core modules discovered, list_commands has exactly init, module, upgrade."""
    from specfact_cli.registry.module_discovery import DiscoveredModule

    def _discover(*, builtin_root=None, user_root=None, **kwargs):
        root = builtin_root or tmp_path
        return [
            DiscoveredModule(root / "init", _make_core_metadata("init"), "builtin"),
            DiscoveredModule(root / "module_registry", _make_core_metadata("module_registry", ["module"]), "builtin"),
            DiscoveredModule(root / "upgrade", _make_core_metadata("upgrade"), "builtin"),
        ]

    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.discover_all_package_metadata",
        lambda: [
            (tmp_path / "init", _make_core_metadata("init")),
            (tmp_path / "module_registry", _make_core_metadata("module_registry", ["module"])),
            (tmp_path / "upgrade", _make_core_metadata("upgrade")),
        ],
    )
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.verify_module_artifact",
        lambda _dir, _meta, **kw: True,
    )
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.read_modules_state",
        dict,
    )
    register_builtin_commands()
    names = set(CommandRegistry.list_commands())
    assert names >= CORE_THREE
    assert "auth" not in names
    for extracted in EXTRACTED_17_NAMES:
        assert extracted not in names, (
            f"Extracted module {extracted} must not be registered when only core is discovered"
        )


def test_bootstrap_does_not_register_extracted_modules_when_only_core_discovered(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Bootstrap with only 3 core does NOT register project, plan, backlog, code, spec, govern, etc."""
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.discover_all_package_metadata",
        lambda: [
            (tmp_path / "init", _make_core_metadata("init")),
            (tmp_path / "module_registry", _make_core_metadata("module_registry", ["module"])),
            (tmp_path / "upgrade", _make_core_metadata("upgrade")),
        ],
    )
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.verify_module_artifact",
        lambda _dir, _meta, **kw: True,
    )
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.read_modules_state",
        dict,
    )
    register_builtin_commands()
    registered = CommandRegistry.list_commands()
    assert "auth" not in registered
    for name in EXTRACTED_17_NAMES:
        assert name not in registered, f"Must not register extracted command {name} in core-only mode"


def test_bootstrap_source_has_no_import_of_17_deleted_module_packages() -> None:
    """bootstrap.py must not import the 17 deleted module packages."""
    repo_root = Path(__file__).resolve().parents[3]
    bootstrap_path = repo_root / "src" / "specfact_cli" / "registry" / "bootstrap.py"
    text = bootstrap_path.read_text(encoding="utf-8")
    deleted_imports = [
        "specfact_project.project",
        "specfact_project.plan",
        "specfact_backlog.backlog",
        "specfact_codebase.analyze",
        "specfact_spec.contract",
    ]
    for imp in deleted_imports:
        assert imp not in text, f"bootstrap.py must not import {imp}"


def test_flat_shim_plan_produces_actionable_error_after_shim_removal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Invoking 'plan' when shims are removed should produce an actionable not-found error."""
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.discover_all_package_metadata",
        lambda: [
            (tmp_path / "init", _make_core_metadata("init")),
            (tmp_path / "module_registry", _make_core_metadata("module_registry", ["module"])),
            (tmp_path / "upgrade", _make_core_metadata("upgrade")),
        ],
    )
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.verify_module_artifact",
        lambda _dir, _meta, **kw: True,
    )
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.read_modules_state",
        dict,
    )
    register_builtin_commands()
    if "plan" in CommandRegistry.list_commands():
        pytest.skip("Flat shims still present; migration-03 will remove them")
    try:
        CommandRegistry.get_typer("plan")
    except (ValueError, KeyError) as e:
        msg = str(e).lower()
        assert "plan" in msg or "not found" in msg or "install" in msg


def test_bootstrap_calls_mount_installed_category_groups() -> None:
    """Bootstrap flow must call _mount_installed_category_groups (or equivalent) for installed bundles."""
    repo_root = Path(__file__).resolve().parents[3]
    module_packages_path = repo_root / "src" / "specfact_cli" / "registry" / "module_packages.py"
    text = module_packages_path.read_text(encoding="utf-8")
    assert "_mount_installed_category_groups" in text or "get_installed_bundles" in text


def test_mount_installed_category_groups_mounts_backlog_only_when_specfact_backlog_installed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When get_installed_bundles returns ['specfact-backlog'], backlog group should be registered."""
    CommandRegistry._clear_for_testing()
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.get_installed_bundles",
        MagicMock(return_value=["specfact-backlog"]),
    )
    register_builtin_commands()
    names = CommandRegistry.list_commands()
    assert "backlog" in names


def test_mount_installed_category_groups_does_not_mount_code_when_codebase_not_installed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """When get_installed_bundles returns [] (or no specfact-codebase), code group must not be registered."""
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.discover_all_package_metadata",
        lambda: [
            (tmp_path / "init", _make_core_metadata("init")),
            (tmp_path / "module_registry", _make_core_metadata("module_registry", ["module"])),
            (tmp_path / "upgrade", _make_core_metadata("upgrade")),
        ],
    )
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.verify_module_artifact",
        lambda _dir, _meta, **kw: True,
    )
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.read_modules_state",
        dict,
    )
    monkeypatch.setattr(
        "specfact_cli.registry.module_packages.get_installed_bundles",
        MagicMock(return_value=[]),
    )
    register_builtin_commands()
    names = CommandRegistry.list_commands()
    assert "code" not in names
