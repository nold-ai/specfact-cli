"""
Command registry for lazy-loaded CLI command groups.

This module provides CommandRegistry and CommandMetadata for dynamic command
registration without top-level imports of command modules.
"""

from specfact_cli.registry.metadata import CommandMetadata
from specfact_cli.registry.registry import CommandRegistry


__all__ = ["CommandMetadata", "CommandRegistry"]
