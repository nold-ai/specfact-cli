"""
Template loading and generation modules.

This package provides template loading functionality, including bridge-based
template resolution for dynamic template loading from bridge configuration.
"""

from specfact_cli.templates.bridge_templates import BridgeTemplateLoader


__all__ = [
    "BridgeTemplateLoader",
]
