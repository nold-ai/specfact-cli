"""
Module state: persist enabled/disabled per module under ~/.specfact/registry/modules.json.

Read/merge on init; only enabled modules' commands are registered.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from beartype import beartype

from specfact_cli.registry.help_cache import get_registry_dir


def get_modules_state_path() -> Path:
    """Return path to modules state file (modules.json)."""
    return get_registry_dir() / "modules.json"


@beartype
def read_modules_state() -> dict[str, dict[str, Any]]:
    """
    Read modules.json if present. Returns dict mapping module_id -> {version, enabled}.
    Missing or invalid file returns {}.
    """
    path = get_modules_state_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    modules = data.get("modules")
    if not isinstance(modules, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for item in modules:
        if isinstance(item, dict) and "id" in item:
            mid = str(item["id"])
            out[mid] = {
                "version": str(item.get("version", "")),
                "enabled": bool(item.get("enabled", True)),
            }
    return out


@beartype
def write_modules_state(modules: list[dict[str, Any]]) -> None:
    """
    Write modules.json with list of {id, version, enabled}.
    Creates registry dir if missing.
    """
    get_registry_dir().mkdir(parents=True, exist_ok=True)
    path = get_modules_state_path()
    path.write_text(json.dumps({"modules": modules}, indent=2), encoding="utf-8")
