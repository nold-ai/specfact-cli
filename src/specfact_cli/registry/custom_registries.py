"""Custom registry management: YAML config and multi-registry index fetching."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import yaml
from beartype import beartype
from icontract import ensure, require

from specfact_cli.common import get_bridge_logger
from specfact_cli.registry.marketplace_client import REGISTRY_INDEX_URL, get_registry_index_url


logger = get_bridge_logger(__name__)

_REGISTRIES_FILENAME = "registries.yaml"
OFFICIAL_REGISTRY_ID = "official"
TRUST_LEVELS = frozenset({"always", "prompt", "never"})


def _is_crosshair_runtime() -> bool:
    """Return True when running under CrossHair symbolic exploration."""
    if os.getenv("SPECFACT_CROSSHAIR_ANALYSIS") == "true":
        return True
    return "crosshair" in sys.modules


@beartype
@ensure(lambda result: result.name == _REGISTRIES_FILENAME, "Must return a path ending in the registries filename")
def get_registries_config_path() -> Path:
    """Return path to registries.yaml under ~/.specfact/config/."""
    return Path.home() / ".specfact" / "config" / _REGISTRIES_FILENAME


def _default_official_entry() -> dict[str, Any]:
    """Return the built-in official registry entry (branch-aware: main vs dev)."""
    url = REGISTRY_INDEX_URL if _is_crosshair_runtime() else get_registry_index_url()
    return {
        "id": OFFICIAL_REGISTRY_ID,
        "url": url,
        "priority": 1,
        "trust": "always",
    }


@beartype
@require(lambda id: id.strip() != "", "id must be non-empty")
@require(lambda url: url.strip().startswith("http"), "url must be http(s)")
@require(lambda trust: trust in TRUST_LEVELS, "trust must be always, prompt, or never")
@ensure(lambda: True, "no postcondition on void")
def add_registry(
    id: str,
    url: str,
    priority: int | None = None,
    trust: str = "prompt",
) -> None:
    """Add a registry to config. Assigns next priority if priority is None."""
    id = id.strip()
    url = url.strip()
    path = get_registries_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    registries: list[dict[str, Any]] = []
    if path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        registries = list(data.get("registries") or [])
    existing_ids = {r.get("id") for r in registries if isinstance(r, dict) and r.get("id")}
    if id in existing_ids:
        registries = [r for r in registries if isinstance(r, dict) and r.get("id") != id]
    if priority is None:
        priorities = [
            p
            for r in registries
            if isinstance(r, dict) and (p := r.get("priority")) is not None and isinstance(p, (int, float))
        ]
        priority = int(max(priorities, default=0)) + 1
    registries.append({"id": id, "url": url, "priority": int(priority), "trust": trust})
    registries.sort(key=lambda r: (r.get("priority", 999), r.get("id", "")))
    path.write_text(yaml.dump({"registries": registries}, default_flow_style=False, sort_keys=False), encoding="utf-8")


@beartype
@ensure(lambda result: isinstance(result, list), "returns list")
def list_registries() -> list[dict[str, Any]]:
    """Return all registries: official first, then custom from config, sorted by priority."""
    if _is_crosshair_runtime():
        return [_default_official_entry()]
    result: list[dict[str, Any]] = []
    path = get_registries_config_path()
    if path.exists():
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            custom = [r for r in (data.get("registries") or []) if isinstance(r, dict) and r.get("id")]
            has_official = any(r.get("id") == OFFICIAL_REGISTRY_ID for r in custom)
            if not has_official:
                result.append(_default_official_entry())
            for r in custom:
                result.append({k: v for k, v in r.items() if k in ("id", "url", "priority", "trust")})
            result.sort(key=lambda r: (r.get("priority", 999), r.get("id", "")))
        except Exception as exc:
            logger.warning("Failed to load registries config: %s", exc)
            result = [_default_official_entry()]
    else:
        result = [_default_official_entry()]
    return result


@beartype
@require(lambda id: id.strip() != "", "id must be non-empty")
@ensure(lambda: True, "no postcondition on void")
def remove_registry(id: str) -> None:
    """Remove a registry by id from config. Cannot remove official (no-op if official)."""
    id = id.strip()
    if id == OFFICIAL_REGISTRY_ID:
        logger.debug("Cannot remove built-in official registry")
        return
    path = get_registries_config_path()
    if not path.exists():
        return
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    registries = [r for r in (data.get("registries") or []) if isinstance(r, dict) and r.get("id") != id]
    if not registries:
        path.unlink()
        return
    path.write_text(yaml.dump({"registries": registries}, default_flow_style=False, sort_keys=False), encoding="utf-8")


@beartype
@ensure(lambda result: isinstance(result, list), "returns list")
def fetch_all_indexes(timeout: float = 10.0) -> list[tuple[str, dict[str, Any]]]:
    """Fetch index from each registry in priority order. Returns list of (registry_id, index_dict)."""
    from specfact_cli.registry.marketplace_client import fetch_registry_index

    if _is_crosshair_runtime():
        return []

    registries = list_registries()
    result: list[tuple[str, dict[str, Any]]] = []
    for reg in registries:
        reg_id = str(reg.get("id", ""))
        url = str(reg.get("url", "")).strip()
        if not url:
            continue
        payload = fetch_registry_index(index_url=url, timeout=timeout)
        if isinstance(payload, dict):
            result.append((reg_id, payload))
    return result
