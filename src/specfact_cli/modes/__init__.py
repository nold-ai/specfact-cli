"""
Mode detection and routing for SpecFact CLI.

This package provides operational mode detection (CI/CD vs CoPilot) and command routing.
"""

from __future__ import annotations

from specfact_cli.modes.detector import OperationalMode, detect_mode
from specfact_cli.modes.router import CommandRouter, RoutingResult, get_router


__all__ = [
    "CommandRouter",
    "OperationalMode",
    "RoutingResult",
    "detect_mode",
    "get_router",
]
