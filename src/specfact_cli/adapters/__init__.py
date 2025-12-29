"""
Bridge adapters for external tool integration.

This module provides adapter implementations for various external tools
(e.g., GitHub, Spec-Kit, Linear, Jira) that implement the BridgeAdapter interface.
"""

from __future__ import annotations

from specfact_cli.adapters.base import BridgeAdapter
from specfact_cli.adapters.github import GitHubAdapter
from specfact_cli.adapters.registry import AdapterRegistry


# Auto-register built-in adapters
AdapterRegistry.register("github", GitHubAdapter)

__all__ = ["AdapterRegistry", "BridgeAdapter", "GitHubAdapter"]
