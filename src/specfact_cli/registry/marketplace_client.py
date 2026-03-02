"""Marketplace registry client for module discovery and downloads."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

import requests
from beartype import beartype
from icontract import ensure, require

from specfact_cli.common import get_bridge_logger


# Official registry URL template: {branch} is main or dev so specfact-cli and specfact-cli-modules stay in sync.
OFFICIAL_REGISTRY_INDEX_TEMPLATE = (
    "https://raw.githubusercontent.com/nold-ai/specfact-cli-modules/{branch}/registry/index.json"
)
REGISTRY_INDEX_URL = OFFICIAL_REGISTRY_INDEX_TEMPLATE.format(branch="main")
# Base URL for resolving relative download_url in index (registry root; matches list-registries).
# specfact-cli-modules layout: registry/index.json, registry/modules/*.tar.gz; index entries use
# relative download_url (e.g. "modules/specfact-project-0.40.1.tar.gz") resolved against this base.
REGISTRY_BASE_URL = REGISTRY_INDEX_URL.rsplit("/", 1)[0]


@lru_cache(maxsize=1)
def get_modules_branch() -> str:
    """Return branch to use for official registry (main or dev). Keeps specfact-cli and specfact-cli-modules in sync.

    - specfact-cli on main → use specfact-cli-modules main.
    - specfact-cli on dev / feature/* / bugfix/* / hotfix/* → use specfact-cli-modules dev.
    Override with env SPECFACT_MODULES_BRANCH (e.g. main or dev). When not in git or git fails, returns main.
    """
    configured = os.environ.get("SPECFACT_MODULES_BRANCH", "").strip()
    if configured:
        return configured or "main"
    start = Path(__file__).resolve()
    for parent in [start, *start.parents]:
        if (parent / ".git").exists():
            try:
                out = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=parent,
                    capture_output=True,
                    text=True,
                    timeout=2,
                    check=False,
                )
                if out.returncode != 0 or not out.stdout:
                    return "main"
                branch = out.stdout.strip()
                return "main" if branch == "main" else "dev"
            except (OSError, subprocess.TimeoutExpired):
                return "main"
    return "main"


@beartype
def get_registry_index_url() -> str:
    """Return official registry index URL for the current branch (main or dev)."""
    return OFFICIAL_REGISTRY_INDEX_TEMPLATE.format(branch=get_modules_branch())


@beartype
def get_registry_base_url() -> str:
    """Return official registry base URL (for resolving relative download_url) for the current branch."""
    return get_registry_index_url().rsplit("/", 1)[0]


@beartype
def resolve_download_url(
    entry: dict[str, object],
    index_payload: dict[str, object],
    registry_index_url: str | None = None,
) -> str:
    """Return full download URL for an index entry (same logic as module install).

    If entry['download_url'] contains '://', return it. Otherwise resolve against registry base:
    index registry_base_url or download_base_url, else registry_index_url with /index.json stripped,
    else env SPECFACT_REGISTRY_BASE_URL, else get_registry_base_url() (branch-aware). Used by download_module and
    verify-bundle-published gate so URLs are built identically.
    """
    raw = str(entry.get("download_url", "")).strip()
    if not raw:
        return ""
    if "://" in raw:
        return raw
    base = None
    for key in ("registry_base_url", "download_base_url"):
        val = index_payload.get(key)
        if isinstance(val, str) and val.strip():
            base = val.strip().rstrip("/")
            break
    if base is None and isinstance(registry_index_url, str) and registry_index_url.strip():
        base = registry_index_url.strip().rstrip("/").rsplit("/", 1)[0]
    if base is None:
        base = (os.environ.get("SPECFACT_REGISTRY_BASE_URL") or "").strip().rstrip("/")
    if not base:
        base = get_registry_base_url().rstrip("/")
    return f"{base}/{raw.lstrip('/')}"


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
        url = get_registry_index_url()
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except Exception as exc:
        logger.warning("Registry unavailable, using offline mode: %s", exc)
        return None

    try:
        payload = json.loads(content.decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        logger.error("Failed to parse registry index JSON: %s", exc)
        raise ValueError("Invalid registry index format") from exc

    if not isinstance(payload, dict):
        raise ValueError("Invalid registry index format")

    payload["_registry_index_url"] = url
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

    full_download_url = resolve_download_url(entry, registry_index, registry_index.get("_registry_index_url"))
    expected_checksum = str(entry.get("checksum_sha256", "")).strip().lower()
    if not full_download_url or not expected_checksum:
        raise ValueError("Invalid registry index format")

    response = requests.get(full_download_url, timeout=timeout)
    response.raise_for_status()
    content = response.content

    actual_checksum = hashlib.sha256(content).hexdigest()
    if actual_checksum != expected_checksum:
        raise SecurityError(f"Checksum mismatch for module {module_id}")

    target_dir = download_dir or (Path.home() / ".specfact" / "downloads")
    target_dir.mkdir(parents=True, exist_ok=True)
    parsed = urlparse(full_download_url)
    file_name = Path(parsed.path).name or f"{module_id.replace('/', '-')}.tar.gz"
    target_path = target_dir / file_name
    target_path.write_bytes(content)
    logger.debug("Downloaded module '%s' to '%s'", module_id, target_path)
    return target_path
