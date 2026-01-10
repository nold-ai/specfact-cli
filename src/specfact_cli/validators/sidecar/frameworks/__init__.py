"""
Framework extractors for sidecar validation.

This package provides framework-specific extractors for route and schema extraction.
"""

from __future__ import annotations

from specfact_cli.validators.sidecar.frameworks.base import BaseFrameworkExtractor, RouteInfo


__all__ = ["BaseFrameworkExtractor", "RouteInfo"]
