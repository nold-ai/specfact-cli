"""Tests for module lifecycle bridge registration flow."""

from __future__ import annotations

from pathlib import Path

from specfact_cli.models.module_package import ModulePackageMetadata, ServiceBridgeMetadata
from specfact_cli.registry import CommandRegistry, module_packages
from specfact_cli.registry.bridge_registry import BridgeRegistry


class _TestConverter:
    """Converter used for bridge registration tests."""

    def to_bundle(self, external_data: dict) -> dict:
        return external_data

    def from_bundle(self, bundle_data: dict) -> dict:
        return bundle_data


def _metadata_with_bridges(*, converter_class: str) -> ModulePackageMetadata:
    return ModulePackageMetadata(
        name="backlog",
        version="0.1.0",
        commands=["backlog"],
        service_bridges=[ServiceBridgeMetadata(id="ado", converter_class=converter_class)],
    )


def test_register_module_package_commands_registers_declared_bridges(monkeypatch, tmp_path: Path) -> None:
    """Lifecycle registration should load and register manifest service bridges."""
    CommandRegistry._clear_for_testing()
    registry = BridgeRegistry()
    converter_path = f"{__name__}._TestConverter"

    packages = [(tmp_path, _metadata_with_bridges(converter_class=converter_path))]
    monkeypatch.setattr(module_packages, "discover_all_package_metadata", lambda: packages)
    monkeypatch.setattr(module_packages, "verify_module_artifact", lambda _dir, _meta, allow_unsigned=False: True)
    monkeypatch.setattr(module_packages, "read_modules_state", dict)
    monkeypatch.setattr(module_packages, "_make_package_loader", lambda *_args: object)
    monkeypatch.setattr(module_packages, "_load_package_module", lambda *_args: object())
    monkeypatch.setattr(module_packages, "BRIDGE_REGISTRY", registry, raising=False)

    module_packages.register_module_package_commands()

    assert registry.get_converter("ado") is not None


def test_invalid_bridge_declaration_is_non_fatal(monkeypatch, tmp_path: Path) -> None:
    """Invalid bridge declarations should be skipped with warnings."""
    CommandRegistry._clear_for_testing()
    registry = BridgeRegistry()
    packages = [(tmp_path, _metadata_with_bridges(converter_class="invalid.path.MissingConverter"))]
    monkeypatch.setattr(module_packages, "discover_all_package_metadata", lambda: packages)
    monkeypatch.setattr(module_packages, "verify_module_artifact", lambda _dir, _meta, allow_unsigned=False: True)
    monkeypatch.setattr(module_packages, "read_modules_state", dict)
    monkeypatch.setattr(module_packages, "_make_package_loader", lambda *_args: object)
    monkeypatch.setattr(module_packages, "_load_package_module", lambda *_args: object())
    monkeypatch.setattr(module_packages, "BRIDGE_REGISTRY", registry, raising=False)

    module_packages.register_module_package_commands()

    assert registry.list_bridge_ids() == []
    assert "backlog" in CommandRegistry.list_commands()
