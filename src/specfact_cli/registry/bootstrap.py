"""
Bootstrap: register all CLI commands from module packages with CommandRegistry.

Commands are discovered from configured module-package roots.
Loaders import each package's src on first use and return its .app (Typer).
cli.py must not import command modules at top level; it uses the registry.
When category_grouping_enabled is True, mounts category groups (code, backlog, project, spec, govern)
and compat shims for flat commands; otherwise mounts all modules flat.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from beartype import beartype
from icontract import ensure

from specfact_cli.registry.module_packages import register_module_package_commands


_SPECFACT_CONFIG_PATH = Path.home() / ".specfact" / "config.yaml"


@beartype
@ensure(lambda result: isinstance(result, bool), "Must return a bool")
def _get_category_grouping_enabled() -> bool:
    """Read category_grouping_enabled from env then config file; default True."""
    env_val = __import__("os").environ.get("SPECFACT_CATEGORY_GROUPING_ENABLED", "").strip().lower()
    if env_val in ("1", "true", "yes"):
        return True
    if env_val in ("0", "false", "no"):
        return False
    if not _SPECFACT_CONFIG_PATH.exists():
        return True
    try:
        raw = yaml.safe_load(_SPECFACT_CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "category_grouping_enabled" in raw:
            val = raw["category_grouping_enabled"]
            if isinstance(val, bool):
                return val
            if isinstance(val, str):
                return val.strip().lower() in ("1", "true", "yes")
    except (OSError, ValueError):
        pass
    return True


@beartype
@ensure(lambda: isinstance(_SPECFACT_CONFIG_PATH, Path), "Config path must be a Path")
def register_builtin_commands() -> None:
    """Register all command groups from discovered module packages with CommandRegistry."""
    category_grouping_enabled = _get_category_grouping_enabled()
    register_module_package_commands(category_grouping_enabled=category_grouping_enabled)
