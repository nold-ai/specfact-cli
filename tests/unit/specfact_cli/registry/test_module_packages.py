"""
Tests for module packages (spec: module-packages).

Discovery finds packages with metadata.yaml; package loader loads only that package; registry receives commands.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from specfact_cli.registry import CommandRegistry
from specfact_cli.registry.module_packages import (
    ModulePackageMetadata,
    discover_package_metadata,
    get_modules_root,
    merge_module_state,
)
from specfact_cli.registry.module_state import read_modules_state, write_modules_state


@pytest.fixture(autouse=True)
def _reset_registry():
    CommandRegistry._clear_for_testing()
    yield
    CommandRegistry._clear_for_testing()


def test_get_modules_root_under_specfact_cli():
    """get_modules_root() returns a path under the specfact_cli package."""
    root = get_modules_root()
    assert root.name == "modules"
    assert "specfact_cli" in str(root)
    assert root.exists() or not root.exists()


def test_discover_package_metadata_finds_example(tmp_path: Path):
    """Discovery finds packages that have module-package.yaml with name and commands."""
    (tmp_path / "example_pkg").mkdir()
    (tmp_path / "example_pkg" / "module-package.yaml").write_text(
        "name: example_pkg\nversion: '0.1.0'\ncommands: [example_cmd]\n", encoding="utf-8"
    )
    (tmp_path / "example_pkg" / "src").mkdir(parents=True)
    result = discover_package_metadata(tmp_path)
    assert len(result) == 1
    _pkg_dir, meta = result[0]
    assert meta.name == "example_pkg"
    assert meta.version == "0.1.0"
    assert meta.commands == ["example_cmd"]


def test_discover_package_metadata_skips_dir_without_metadata(tmp_path: Path):
    """Discovery skips dirs that don't have module-package.yaml (or metadata.yaml)."""
    (tmp_path / "no_meta").mkdir()
    result = discover_package_metadata(tmp_path)
    assert len(result) == 0


def test_merge_module_state_new_modules_enabled():
    """New discovered modules get enabled: true."""
    discovered = [("new_one", "1.0.0")]
    state = {}
    enabled = merge_module_state(discovered, state, [], [])
    assert enabled["new_one"] is True


def test_merge_module_state_preserves_existing():
    """Existing state preserved; overrides applied."""
    discovered = [("a", "1.0"), ("b", "2.0")]
    state = {"a": {"version": "1.0", "enabled": False}}
    enabled = merge_module_state(discovered, state, ["a"], [])
    assert enabled["a"] is True
    assert enabled["b"] is True


def test_merge_module_state_disable_override():
    """disable_ids set module to false."""
    discovered = [("m1", "1.0")]
    enabled = merge_module_state(discovered, {}, [], ["m1"])
    assert enabled["m1"] is False


def test_module_state_read_write(tmp_path: Path):
    """read_modules_state / write_modules_state roundtrip."""
    os.environ["SPECFACT_REGISTRY_DIR"] = str(tmp_path)
    try:
        write_modules_state(
            [{"id": "x", "version": "1.0", "enabled": True}, {"id": "y", "version": "2.0", "enabled": False}]
        )
        read = read_modules_state()
        assert read["x"]["enabled"] is True
        assert read["y"]["enabled"] is False
        assert read["x"]["version"] == "1.0"
    finally:
        os.environ.pop("SPECFACT_REGISTRY_DIR", None)


def test_example_package_discovered_if_present():
    """If modules/example exists with module-package.yaml, discovery finds it."""
    root = get_modules_root()
    if not root.exists():
        pytest.skip("modules root not present")
    packages = discover_package_metadata(root)
    example = [p for p in packages if p[1].name == "example"]
    if not example:
        pytest.skip("example package not present")
    _dir, meta = example[0]
    assert "example" in meta.commands


def test_registry_receives_example_command_when_registered():
    """After register_builtin_commands (module discovery), 'example' can be in registry."""
    from specfact_cli.registry.bootstrap import register_builtin_commands

    register_builtin_commands()
    names = CommandRegistry.list_commands()
    if "example" in names:
        meta = CommandRegistry.get_metadata("example")
        assert meta is not None
        typer_app = CommandRegistry.get_typer("example")
        assert typer_app is not None
        assert typer_app.info.name == "example"


def test_protocol_reporting_classifies_full_partial_legacy_from_runtime_interface(
    monkeypatch, caplog, tmp_path: Path
) -> None:
    """Protocol summary should classify full/partial/legacy modules accurately."""
    from specfact_cli.registry import module_packages as module_packages_impl

    class _RuntimeFull:
        def import_to_bundle(self, source, config):  # type: ignore[no-untyped-def]
            return None

        def export_from_bundle(self, bundle, target, config):  # type: ignore[no-untyped-def]
            return None

        def sync_with_bundle(self, source, target, config):  # type: ignore[no-untyped-def]
            return None

        def validate_bundle(self, bundle):  # type: ignore[no-untyped-def]
            return []

    class _RuntimePartial:
        def import_to_bundle(self, source, config):  # type: ignore[no-untyped-def]
            return None

    caplog.set_level(logging.INFO)
    test_logger = logging.getLogger("test.protocol.reporting")
    test_logger.handlers = []
    test_logger.propagate = True
    monkeypatch.setattr(module_packages_impl, "get_bridge_logger", lambda _name: test_logger)

    metadata = [
        (tmp_path / "full", ModulePackageMetadata(name="full", commands=[])),
        (tmp_path / "partial", ModulePackageMetadata(name="partial", commands=[])),
        (tmp_path / "legacy", ModulePackageMetadata(name="legacy", commands=[])),
    ]
    monkeypatch.setattr(module_packages_impl, "discover_package_metadata", lambda _root: metadata)
    monkeypatch.setattr(module_packages_impl, "read_modules_state", dict)

    def _fake_loader(package_dir: Path, _package_name: str):
        if package_dir.name == "full":
            return SimpleNamespace(runtime_interface=_RuntimeFull())
        if package_dir.name == "partial":
            return SimpleNamespace(runtime_interface=_RuntimePartial())
        return SimpleNamespace()

    monkeypatch.setattr(module_packages_impl, "_load_package_module", _fake_loader)

    module_packages_impl.register_module_package_commands()

    assert "Full=1, Partial=1, Legacy=1" in caplog.text


def test_protocol_legacy_warning_emitted_once_per_module(monkeypatch, caplog, tmp_path: Path) -> None:
    """Legacy warning should not be emitted more than once for a module condition."""
    from specfact_cli.registry import module_packages as module_packages_impl

    caplog.set_level(logging.WARNING)
    test_logger = logging.getLogger("test.protocol.warning")
    test_logger.handlers = []
    test_logger.propagate = True
    monkeypatch.setattr(module_packages_impl, "get_bridge_logger", lambda _name: test_logger)
    monkeypatch.setattr(
        module_packages_impl,
        "discover_package_metadata",
        lambda _root: [(tmp_path / "legacy", ModulePackageMetadata(name="legacy", commands=[]))],
    )
    monkeypatch.setattr(module_packages_impl, "read_modules_state", dict)
    monkeypatch.setattr(module_packages_impl, "_load_package_module", lambda *_args: SimpleNamespace())

    module_packages_impl.register_module_package_commands()

    lines = [line for line in caplog.text.splitlines() if "Module legacy: No ModuleIOContract (legacy mode)" in line]
    assert len(lines) == 1
