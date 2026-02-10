"""Tests for module protocol validation during discovery/registration."""

from __future__ import annotations

from specfact_cli.registry.module_packages import _check_protocol_compliance, _check_schema_compatibility


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
    operations = _check_protocol_compliance(FullProtocolModule)
    assert set(operations) == {"import", "export", "sync", "validate"}


def test_full_protocol_logged() -> None:
    operations = _check_protocol_compliance(FullProtocolModule)
    assert len(operations) == 4


def test_partial_protocol_logged() -> None:
    operations = _check_protocol_compliance(PartialProtocolModule)
    assert set(operations) == {"import", "validate"}


def test_no_protocol_legacy_mode() -> None:
    operations = _check_protocol_compliance(LegacyModule)
    assert operations == []


def test_schema_version_compatibility_check() -> None:
    assert _check_schema_compatibility("1", "1") is True
    assert _check_schema_compatibility(None, "1") is True
    assert _check_schema_compatibility("2", "1") is False
