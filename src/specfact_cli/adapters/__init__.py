"""
Bridge adapters for external tool integration.

This module provides adapter implementations for various external tools
(e.g., GitHub, Spec-Kit, Linear, Jira) that implement the BridgeAdapter interface.
"""

from __future__ import annotations

from specfact_cli.adapters.ado import AdoAdapter
from specfact_cli.adapters.base import BridgeAdapter
from specfact_cli.adapters.github import GitHubAdapter
from specfact_cli.adapters.openspec import OpenSpecAdapter
from specfact_cli.adapters.registry import AdapterRegistry
from specfact_cli.adapters.speckit import SpecKitAdapter


# Auto-register built-in adapters
AdapterRegistry.register("ado", AdoAdapter)
AdapterRegistry.register("github", GitHubAdapter)
AdapterRegistry.register("openspec", OpenSpecAdapter)
AdapterRegistry.register("speckit", SpecKitAdapter)

__all__ = ["AdapterRegistry", "AdoAdapter", "BridgeAdapter", "GitHubAdapter", "OpenSpecAdapter", "SpecKitAdapter"]
