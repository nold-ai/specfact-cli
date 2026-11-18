"""Release inventory for official modules during the signing incident."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import TypedDict, cast


class FrozenArchive(TypedDict):
    archive: str
    tree: str


class _Inventory(TypedDict):
    modules_cutoff: str
    latest: dict[str, str]
    archives: dict[str, dict[str, FrozenArchive]]
    bundled: dict[str, dict[str, str]]


@lru_cache(maxsize=1)
def _inventory() -> _Inventory:
    return cast(
        _Inventory,
        json.loads(Path(__file__).with_name("official-module-cutoff.json").read_text(encoding="utf-8")),
    )


def frozen_archive(module_id: str, version: str | None) -> tuple[str, FrozenArchive]:
    """Resolve one allowed archive by ID and version."""
    inventory = _inventory()
    selected = version or inventory["latest"].get(module_id)
    releases = inventory["archives"].get(module_id, {})
    if selected is None or selected not in releases:
        raise ValueError(f"Module '{module_id}' is outside the approved release cutoff")
    return selected, releases[selected]


def frozen_archive_url(module_id: str, version: str) -> str:
    cutoff = _inventory()["modules_cutoff"]
    name = module_id.split("/", 1)[1]
    return f"https://raw.githubusercontent.com/nold-ai/specfact-cli-modules/{cutoff}/registry/modules/{name}-{version}.tar.gz"


def frozen_index_url() -> str:
    cutoff = _inventory()["modules_cutoff"]
    return f"https://raw.githubusercontent.com/nold-ai/specfact-cli-modules/{cutoff}/registry/index.json"


def is_official_module(module_id: str, publisher: str | None = None, tier: str | None = None) -> bool:
    name = module_id.strip().lower()
    return name.startswith("nold-ai/") or (publisher or "").strip().lower() == "nold-ai" or tier == "official"


def frozen_tree_matches(module_id: str, version: str, digest: str) -> bool:
    inventory = _inventory()
    archive = inventory["archives"].get(module_id, {}).get(version)
    return (archive is not None and digest == archive["tree"]) or (
        digest == inventory["bundled"].get(module_id, {}).get(version)
    )


def is_frozen_bundled_module(module_id: str) -> bool:
    return module_id in _inventory()["bundled"]
