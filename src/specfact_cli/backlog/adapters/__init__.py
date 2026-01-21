"""
Backlog adapter implementations.

This module provides backlog adapter implementations for various providers.
"""

from __future__ import annotations

from specfact_cli.backlog.adapters.base import BacklogAdapter
from specfact_cli.backlog.adapters.local_yaml_adapter import LocalYAMLBacklogAdapter


__all__ = ["BacklogAdapter", "LocalYAMLBacklogAdapter"]
