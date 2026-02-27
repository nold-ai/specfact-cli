"""Marketplace registry client for module discovery and downloads."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

import requests
from beartype import beartype
from icontract import ensure, require

from specfact_cli.common import get_bridge_logger


REGISTRY_INDEX_URL = "https://raw.githubusercontent.com/nold-ai/specfact-cli-modules/main/registry/index.json"


class SecurityError(RuntimeError):
    """Raised when downloaded module integrity verification fails."""


@beartype
@ensure(lambda result: result is None or isinstance(result, dict), "Result must be dict or None")
def fetch_registry_index(
    index_url: str | None = None, registry_id: str | None = None, timeout: float = 10.0
) -> dict | None:
    """Fetch and parse marketplace registry index."""
    logger = get_bridge_logger(__name__)
    url = index_url
    if url is None and registry_id is not None:
        from specfact_cli.registry.custom_registries import list_registries

        for reg in list_registries():
            if str(reg.get("id", "")) == registry_id:
                url = str(reg.get("url", "")).strip()
                break
        if not url:
            logger.warning("Registry %r not found", registry_id)
            return None
    if url is None:
        url = REGISTRY_INDEX_URL
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except Exception as exc:
        logger.warning("Registry unavailable, using offline mode: %s", exc)
        return None

    try:
        payload = response.json()
    except (ValueError, json.JSONDecodeError) as exc:
        logger.error("Failed to parse registry index JSON: %s", exc)
        raise ValueError("Invalid registry index format") from exc

    if not isinstance(payload, dict):
        raise ValueError("Invalid registry index format")

    return payload


@beartype
@require(lambda module_id: "/" in module_id and len(module_id.split("/")) == 2, "module_id must be namespace/name")
@ensure(lambda result: result.exists(), "Downloaded module archive must exist")
def download_module(
    module_id: str,
    *,
    version: str | None = None,
    download_dir: Path | None = None,
    index: dict | None = None,
    timeout: float = 20.0,
) -> Path:
    """Download module tarball and verify SHA-256 checksum from registry metadata."""
    logger = get_bridge_logger(__name__)
    if index is not None:
        registry_index = index
    else:
        from specfact_cli.registry.custom_registries import fetch_all_indexes

        registry_index = None
        for _reg_id, idx in fetch_all_indexes(timeout=timeout):
            if not isinstance(idx, dict):
                continue
            mods = idx.get("modules") or []
            if not isinstance(mods, list):
                continue
            for c in mods:
                if isinstance(c, dict) and c.get("id") == module_id:
                    if version and c.get("latest_version") != version:
                        continue
                    registry_index = idx
                    break
            if registry_index is not None:
                break
        if registry_index is None:
            registry_index = fetch_registry_index()
    if not registry_index:
        raise ValueError("Cannot install from marketplace (offline)")

    modules = registry_index.get("modules", [])
    if not isinstance(modules, list):
        raise ValueError("Invalid registry index format")

    entry = None
    for candidate in modules:
        if isinstance(candidate, dict) and candidate.get("id") == module_id:
            if version and candidate.get("latest_version") != version:
                continue
            entry = candidate
            break

    if entry is None:
        raise ValueError(f"Module '{module_id}' not found in registry")

    download_url = str(entry.get("download_url", "")).strip()
    expected_checksum = str(entry.get("checksum_sha256", "")).strip().lower()
    if not download_url or not expected_checksum:
        raise ValueError("Invalid registry index format")

    response = requests.get(download_url, timeout=timeout)
    response.raise_for_status()
    content = response.content

    actual_checksum = hashlib.sha256(content).hexdigest()
    if actual_checksum != expected_checksum:
        raise SecurityError(f"Checksum mismatch for module {module_id}")

    target_dir = download_dir or (Path.home() / ".specfact" / "downloads")
    target_dir.mkdir(parents=True, exist_ok=True)
    parsed = urlparse(download_url)
    file_name = Path(parsed.path).name or f"{module_id.replace('/', '-')}.tar.gz"
    target_path = target_dir / file_name
    target_path.write_bytes(content)
    logger.debug("Downloaded module '%s' to '%s'", module_id, target_path)
    return target_path
