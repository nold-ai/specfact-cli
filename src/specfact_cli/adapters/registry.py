"""
Adapter registry for plugin-based bridge adapters.

This module provides a registry pattern for registering and retrieving bridge adapters,
enabling extensible plugin-based architecture.
"""

from __future__ import annotations

from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.adapters.base import BridgeAdapter


class AdapterRegistry:
    """
    Registry for bridge adapters (plugin-based).

    This registry allows adapters to be registered at runtime, enabling
    external plugins and built-in adapters to coexist.
    """

    _adapters: dict[str, type[BridgeAdapter]] = {}

    @classmethod
    @beartype
    @require(
        lambda adapter_type: isinstance(adapter_type, str) and len(adapter_type) > 0, "Adapter type must be non-empty"
    )
    @require(
        lambda adapter_class: issubclass(adapter_class, BridgeAdapter), "Adapter class must implement BridgeAdapter"
    )
    @ensure(lambda result: result is None, "Must return None")
    def register(cls, adapter_type: str, adapter_class: type[BridgeAdapter]) -> None:
        """
        Register a new adapter (can be called from external plugins).

        Args:
            adapter_type: Adapter type identifier (e.g., "github", "speckit")
            adapter_class: Adapter class implementing BridgeAdapter interface
        """
        cls._adapters[adapter_type.lower()] = adapter_class

    @classmethod
    @beartype
    @require(
        lambda adapter_type: isinstance(adapter_type, str) and len(adapter_type) > 0, "Adapter type must be non-empty"
    )
    @ensure(lambda result: isinstance(result, BridgeAdapter), "Must return BridgeAdapter instance")
    def get_adapter(cls, adapter_type: str, **kwargs: Any) -> BridgeAdapter:
        """
        Get adapter instance (supports built-in and external adapters).

        Args:
            adapter_type: Adapter type identifier (e.g., "github", "speckit")
            **kwargs: Additional arguments to pass to adapter constructor

        Returns:
            BridgeAdapter instance

        Raises:
            ValueError: If adapter type is not registered
        """
        adapter_type_lower = adapter_type.lower()
        if adapter_type_lower not in cls._adapters:
            msg = f"Adapter '{adapter_type}' not found. Registered adapters: {', '.join(cls._adapters.keys())}"
            raise ValueError(msg)

        adapter_class = cls._adapters[adapter_type_lower]
        return adapter_class(**kwargs)

    @classmethod
    @beartype
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def list_adapters(cls) -> list[str]:
        """
        List all registered adapter types.

        Returns:
            List of registered adapter type identifiers
        """
        return list(cls._adapters.keys())

    @classmethod
    @beartype
    @require(
        lambda adapter_type: isinstance(adapter_type, str) and len(adapter_type) > 0, "Adapter type must be non-empty"
    )
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def is_registered(cls, adapter_type: str) -> bool:
        """
        Check if adapter type is registered.

        Args:
            adapter_type: Adapter type identifier

        Returns:
            True if adapter is registered, False otherwise
        """
        return adapter_type.lower() in cls._adapters
