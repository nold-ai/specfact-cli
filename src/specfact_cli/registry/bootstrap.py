"""
Bootstrap: register all CLI commands from module packages with CommandRegistry.

All commands are discovered from src/specfact_cli/modules/ (module-package.yaml).
Loaders import the package's src on first use and return its .app (Typer).
cli.py must not import command modules at top level; it uses the registry.
"""

from __future__ import annotations

from specfact_cli.registry.module_packages import register_module_package_commands


def register_builtin_commands() -> None:
    """Register all command groups from discovered module packages with CommandRegistry."""
    register_module_package_commands()
