"""Bridge registry for service schema converters.

CrossHair: skip (missing-lookup behavior intentionally raises LookupError by design)
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from beartype import beartype
from icontract import ensure, require


@runtime_checkable
class SchemaConverter(Protocol):
    """Protocol for bidirectional schema conversion."""

    def to_bundle(self, external_data: dict) -> dict:
        """Convert external service payload into bundle-compatible payload."""
        ...

    def from_bundle(self, bundle_data: dict) -> dict:
        """Convert bundle payload into service-specific payload."""
        ...


@beartype
class BridgeRegistry:
    """In-memory registry for service bridge converters."""

    def __init__(self) -> None:
        self._converters: dict[str, SchemaConverter] = {}
        self._owners: dict[str, str] = {}

    @beartype
    @require(lambda bridge_id: bridge_id.strip() != "", "Bridge ID must not be empty")
    @require(lambda owner: owner.strip() != "", "Bridge owner must not be empty")
    @require(lambda converter: isinstance(converter, SchemaConverter), "Converter must satisfy SchemaConverter")
    @ensure(lambda self, bridge_id: bridge_id in self._converters, "Registered bridge must be present in registry")
    def register_converter(self, bridge_id: str, converter: SchemaConverter, owner: str) -> None:
        """Register converter for a bridge ID."""
        if bridge_id in self._converters:
            existing_owner = self._owners.get(bridge_id, "unknown")
            raise ValueError(
                f"Duplicate bridge ID '{bridge_id}' declared by '{owner}'. "
                f"Already registered by '{existing_owner}'. "
                "Choose a unique bridge ID or update module declarations to avoid conflicts."
            )
        self._converters[bridge_id] = converter
        self._owners[bridge_id] = owner

    @beartype
    @require(lambda bridge_id: bridge_id.strip() != "", "Bridge ID must not be empty")
    @ensure(lambda result: isinstance(result, SchemaConverter), "Lookup result must satisfy SchemaConverter")
    def get_converter(self, bridge_id: str) -> SchemaConverter:
        """Return converter for bridge ID or raise LookupError for missing registrations."""
        if bridge_id not in self._converters:
            raise LookupError(f"No converter registered for bridge ID '{bridge_id}'.")
        return self._converters[bridge_id]

    @beartype
    def get_owner(self, bridge_id: str) -> str | None:
        """Return module owner for a bridge ID."""
        return self._owners.get(bridge_id)

    @beartype
    def list_bridge_ids(self) -> list[str]:
        """Return sorted bridge IDs currently registered."""
        return sorted(self._converters.keys())

    @beartype
    def as_mapping(self) -> Mapping[str, SchemaConverter]:
        """Expose read-only mapping for introspection/tests."""
        return dict(self._converters)


@beartype
class BridgeProtocolRegistry:
    """In-memory registry for optional adapter protocol bindings."""

    def __init__(self) -> None:
        self._protocols: dict[str, type[Any]] = {}
        self._implementations: dict[str, dict[str, type[Any]]] = {}

    @beartype
    @require(lambda protocol_id: protocol_id.strip() != "", "Protocol ID must not be empty")
    @require(lambda protocol_type: isinstance(protocol_type, type), "Protocol type must be a class")
    def register_protocol(self, protocol_id: str, protocol_type: type[Any]) -> None:
        """Register a protocol type under a protocol ID."""
        self._protocols[protocol_id] = protocol_type

    @beartype
    @require(lambda protocol_id: protocol_id.strip() != "", "Protocol ID must not be empty")
    @require(lambda adapter_id: adapter_id.strip() != "", "Adapter ID must not be empty")
    @require(lambda implementation_type: isinstance(implementation_type, type), "Implementation must be a class")
    def register_implementation(self, protocol_id: str, adapter_id: str, implementation_type: type[Any]) -> None:
        """Register adapter implementation type for a protocol."""
        self._implementations.setdefault(protocol_id, {})[adapter_id] = implementation_type

    @beartype
    @require(lambda protocol_id: protocol_id.strip() != "", "Protocol ID must not be empty")
    def get_protocol(self, protocol_id: str) -> type[Any]:
        """Resolve protocol class for a protocol ID."""
        if protocol_id not in self._protocols:
            raise LookupError(f"No protocol registered for protocol ID '{protocol_id}'.")
        return self._protocols[protocol_id]

    @beartype
    @require(lambda protocol_id: protocol_id.strip() != "", "Protocol ID must not be empty")
    @require(lambda adapter_id: adapter_id.strip() != "", "Adapter ID must not be empty")
    def get_implementation(self, protocol_id: str, adapter_id: str) -> type[Any]:
        """Resolve registered adapter implementation type for a protocol."""
        adapter_map = self._implementations.get(protocol_id, {})
        if adapter_id not in adapter_map:
            raise LookupError(f"No implementation registered for protocol '{protocol_id}' and adapter '{adapter_id}'.")
        return adapter_map[adapter_id]

    @beartype
    @require(lambda protocol_id: protocol_id.strip() != "", "Protocol ID must not be empty")
    def list_implementations(self, protocol_id: str) -> list[str]:
        """List adapter IDs that implement a registered protocol."""
        return sorted(self._implementations.get(protocol_id, {}).keys())


BRIDGE_PROTOCOL_REGISTRY = BridgeProtocolRegistry()
