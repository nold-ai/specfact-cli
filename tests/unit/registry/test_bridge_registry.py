"""Unit tests for bridge registry behavior."""

from __future__ import annotations

import pytest

from specfact_cli.registry.bridge_registry import BridgeRegistry


class _ExampleConverter:
    """Simple converter used for registry tests."""

    def to_bundle(self, external_data: dict) -> dict:
        return {"kind": "bundle", **external_data}

    def from_bundle(self, bundle_data: dict) -> dict:
        return {"kind": "external", **bundle_data}


def test_register_and_get_converter() -> None:
    """Registered converters should be retrievable by bridge ID."""
    registry = BridgeRegistry()
    converter = _ExampleConverter()

    registry.register_converter("ado", converter, "backlog")

    assert registry.get_converter("ado") is converter


def test_duplicate_bridge_id_raises_clear_error() -> None:
    """Duplicate bridge IDs should fail deterministically."""
    registry = BridgeRegistry()
    registry.register_converter("ado", _ExampleConverter(), "backlog")

    with pytest.raises(ValueError, match="ado"):
        registry.register_converter("ado", _ExampleConverter(), "another-module")


def test_missing_bridge_lookup_error_contains_bridge_id() -> None:
    """Missing bridge lookup should include the bridge ID in the error."""
    registry = BridgeRegistry()

    with pytest.raises(LookupError, match="jira"):
        registry.get_converter("jira")


def test_list_bridge_ids_and_owner_tracking() -> None:
    """Bridge helper methods should expose owners and sorted IDs."""
    registry = BridgeRegistry()
    registry.register_converter("jira", _ExampleConverter(), "mod-b")
    registry.register_converter("ado", _ExampleConverter(), "mod-a")

    assert registry.list_bridge_ids() == ["ado", "jira"]
    assert registry.get_owner("ado") == "mod-a"
    assert registry.get_owner("missing") is None
