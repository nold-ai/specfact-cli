"""
Module state: persist enabled/disabled per module under ~/.specfact/registry/modules.json.

Read/merge on init; only enabled modules' commands are registered.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.registry.help_cache import get_registry_dir


@beartype
@ensure(lambda result: isinstance(result, Path))
def get_modules_state_path() -> Path:
    """Return path to modules state file (modules.json)."""
    return get_registry_dir() / "modules.json"


@beartype
@ensure(lambda result: isinstance(result, dict))
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
@require(lambda modules: isinstance(modules, list))
def write_modules_state(modules: list[dict[str, Any]]) -> None:
    """
    Write modules.json with list of {id, version, enabled}.
    Creates registry dir if missing.
    """
    get_registry_dir().mkdir(parents=True, exist_ok=True)
    path = get_modules_state_path()
    path.write_text(json.dumps({"modules": modules}, indent=2), encoding="utf-8")


@require(lambda module_id: isinstance(module_id, str) and len(module_id) > 0, "module_id must be non-empty")
@beartype
def find_dependents(
    module_id: str,
    packages: list[tuple[Path, Any]],
    enabled_map: dict[str, bool],
) -> list[str]:
    """
    Find enabled modules that depend on the given module ID.

    Args:
        module_id: Candidate module to disable.
        packages: Discovered package tuples (package_dir, metadata).
        enabled_map: Effective enabled state map.

    Returns:
        Sorted dependent module IDs currently enabled.
    """
    dependents: list[str] = []
    for _package_dir, meta in packages:
        name = str(getattr(meta, "name", ""))
        if not name or name == module_id:
            continue
        if not enabled_map.get(name, True):
            continue
        module_dependencies = list(getattr(meta, "module_dependencies", []))
        if module_id in module_dependencies:
            dependents.append(name)
    return sorted(dependents)
