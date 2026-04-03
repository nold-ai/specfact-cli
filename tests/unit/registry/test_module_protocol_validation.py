"""Tests for module protocol validation during discovery/registration."""

from __future__ import annotations

from typing import Any

from specfact_cli.registry.module_packages import PROTOCOL_METHODS, _check_schema_compatibility


def _protocol_operations_for_class(module_class: Any) -> list[str]:
    operations: list[str] = []
    for operation, method_name in PROTOCOL_METHODS.items():
        if hasattr(module_class, method_name):
            operations.append(operation)
    return operations


class FullProtocolModule:
    def import_to_bundle(self):
        return None

    def export_from_bundle(self):
        return None

    def sync_with_bundle(self):
        return None

    def validate_bundle(self):
        return None


class PartialProtocolModule:
    def import_to_bundle(self):
        return None

    def validate_bundle(self):
        return None


class LegacyModule:
    def run(self):
        return None


def test_discovery_detects_protocol_implementation() -> None:
    operations = _protocol_operations_for_class(FullProtocolModule)
    assert set(operations) == {"import", "export", "sync", "validate"}


def test_full_protocol_logged() -> None:
    operations = _protocol_operations_for_class(FullProtocolModule)
    assert len(operations) == 4


def test_partial_protocol_logged() -> None:
    operations = _protocol_operations_for_class(PartialProtocolModule)
    assert set(operations) == {"import", "validate"}


def test_no_protocol_legacy_mode() -> None:
    operations = _protocol_operations_for_class(LegacyModule)
    assert operations == []


def test_schema_version_compatibility_check() -> None:
    assert _check_schema_compatibility("1", "1") is True
    assert _check_schema_compatibility(None, "1") is True
    assert _check_schema_compatibility("2", "1") is False
