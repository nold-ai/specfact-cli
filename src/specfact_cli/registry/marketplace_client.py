"""Marketplace registry client for module discovery and downloads."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlparse

import requests
from beartype import beartype
from icontract import ensure, require

from specfact_cli.common import get_bridge_logger


# Official registry URL template: {branch} is main or dev so specfact-cli and specfact-cli-modules stay in sync.
# Override with SPECFACT_REGISTRY_INDEX_URL to use a local registry (path or file:// URL) for list/install.
OFFICIAL_REGISTRY_INDEX_TEMPLATE = (
    "https://raw.githubusercontent.com/nold-ai/specfact-cli-modules/{branch}/registry/index.json"
)
REGISTRY_INDEX_URL = OFFICIAL_REGISTRY_INDEX_TEMPLATE.format(branch="main")
# Base URL for resolving relative download_url in index (registry root; matches list-registries).
# specfact-cli-modules layout: registry/index.json, registry/modules/*.tar.gz; index entries use
# relative download_url (e.g. "modules/specfact-project-0.40.1.tar.gz") resolved against this base.
REGISTRY_BASE_URL = REGISTRY_INDEX_URL.rsplit("/", 1)[0]


@beartype
def _is_mainline_ref(ref_name: str) -> bool:
    """Return True when a branch/ref should use main modules registry."""
    normalized = ref_name.strip().lower()
    return normalized == "main" or normalized.startswith("release/")


def _modules_branch_from_detached_ci() -> str:
    head_ref = os.environ.get("GITHUB_HEAD_REF", "").strip()
    base_ref = os.environ.get("GITHUB_BASE_REF", "").strip()
    ref_name = os.environ.get("GITHUB_REF_NAME", "").strip()
    pr_refs = [ref for ref in (head_ref, base_ref) if ref]
    if pr_refs:
        for ref in pr_refs:
            if _is_mainline_ref(ref):
                return "main"
        return "dev"
    ci_refs: list[str] = []
    github_ref = os.environ.get("GITHUB_REF", "").strip()
    if github_ref.startswith("refs/heads/"):
        ci_refs.append(github_ref[len("refs/heads/") :].strip())
    ci_refs.append(ref_name)
    for ref in ci_refs:
        if not ref:
            continue
        if _is_mainline_ref(ref):
            return "main"
    if any(ci_refs):
        return "dev"
    return "main"


def _modules_branch_from_git_parent(parent: Path) -> str | None:
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
        if branch != "HEAD":
            return "main" if _is_mainline_ref(branch) else "dev"
        return _modules_branch_from_detached_ci()
    except (OSError, subprocess.TimeoutExpired):
        return "main"


@lru_cache(maxsize=1)
@beartype
@ensure(
    lambda result: cast(str, result) in ("main", "dev") or len(cast(str, result)) > 0,
    "Must return a non-empty branch name",
)
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
            return _modules_branch_from_git_parent(parent) or "main"
    return "main"


@beartype
@ensure(lambda result: cast(str, result).strip() != "", "Must return a non-empty URL string")
def get_registry_index_url() -> str:
    """Return registry index URL (official remote or SPECFACT_REGISTRY_INDEX_URL for local)."""
    configured = os.environ.get("SPECFACT_REGISTRY_INDEX_URL", "").strip()
    if configured:
        return configured
    return OFFICIAL_REGISTRY_INDEX_TEMPLATE.format(branch=get_modules_branch())


@beartype
@ensure(lambda result: cast(str, result).strip() != "", "Must return a non-empty base URL string")
def get_registry_base_url() -> str:
    """Return official registry base URL (for resolving relative download_url) for the current branch."""
    return get_registry_index_url().rsplit("/", 1)[0]


@beartype
@require(lambda entry: isinstance(entry, dict), "entry must be a dict")
@require(lambda index_payload: isinstance(index_payload, dict), "index_payload must be a dict")
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


def _resolve_registry_index_url(
    index_url: str | None,
    registry_id: str | None,
    logger: Any,
) -> str | None:
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
    return url


def _load_registry_index_bytes(url: str | Any, url_str: str, timeout: float, logger: Any) -> bytes | None:
    if url_str.startswith("file://"):
        path = Path(urlparse(url_str).path)
        if not path.is_absolute():
            path = path.resolve()
        try:
            return path.read_bytes()
        except OSError as exc:
            logger.warning("Local registry index unavailable: %s", exc)
            return None
    if os.path.isfile(url_str):
        try:
            return Path(url_str).resolve().read_bytes()
        except OSError as exc:
            logger.warning("Local registry index unavailable: %s", exc)
            return None
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        content = response.content
        if not content and getattr(response, "text", ""):
            content = str(response.text).encode("utf-8")
        return content
    except Exception as exc:
        logger.warning("Registry unavailable, using offline mode: %s", exc)
        return None


def _parse_registry_index_payload(content: bytes, url: str | Any, logger: Any) -> dict:
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
@ensure(lambda result: result is None or isinstance(result, dict), "Result must be dict or None")
def fetch_registry_index(
    index_url: str | None = None, registry_id: str | None = None, timeout: float = 10.0
) -> dict | None:
    """Fetch and parse marketplace registry index."""
    logger = get_bridge_logger(__name__)
    url = _resolve_registry_index_url(index_url, registry_id, logger)
    if url is None:
        return None
    url_str = str(url).strip()
    content = _load_registry_index_bytes(url, url_str, timeout, logger)
    if content is None:
        return None
    return _parse_registry_index_payload(content, url, logger)


def _find_registry_index_for_module(
    module_id: str,
    version: str | None,
    timeout: float,
) -> dict | None:
    from specfact_cli.registry.custom_registries import fetch_all_indexes

    for _reg_id, idx in fetch_all_indexes(timeout=timeout):
        if not isinstance(idx, dict):
            continue
        idx_dict = cast(dict[str, Any], idx)
        mods = idx_dict.get("modules", [])
        if not isinstance(mods, list):
            continue
        for c in mods:
            if isinstance(c, dict) and cast(dict[str, Any], c).get("id") == module_id:
                cd = cast(dict[str, Any], c)
                if version and ("latest_version" not in cd or cd["latest_version"] != version):
                    continue
                return idx_dict
    return fetch_registry_index()


def _select_module_entry_from_index(
    registry_index: dict[str, Any],
    module_id: str,
    version: str | None,
) -> dict[str, Any]:
    modules = registry_index.get("modules", [])
    if not isinstance(modules, list):
        raise ValueError("Invalid registry index format")
    for candidate in modules:
        if isinstance(candidate, dict) and cast(dict[str, Any], candidate).get("id") == module_id:
            cand = cast(dict[str, Any], candidate)
            if version and ("latest_version" not in cand or cand["latest_version"] != version):
                continue
            return cand
    raise ValueError(f"Module '{module_id}' not found in registry")


def _download_bytes_from_url(full_download_url: str, timeout: float) -> bytes:
    if full_download_url.startswith("file://"):
        try:
            local_path = Path(urlparse(full_download_url).path)
            if not local_path.is_absolute():
                local_path = local_path.resolve()
            return local_path.read_bytes()
        except OSError as exc:
            raise ValueError(f"Cannot read module tarball from local registry: {exc}") from exc
    if os.path.isfile(full_download_url):
        return Path(full_download_url).resolve().read_bytes()
    response = requests.get(full_download_url, timeout=timeout)
    response.raise_for_status()
    return response.content


@beartype
@require(
    lambda module_id: "/" in cast(str, module_id) and len(cast(str, module_id).split("/")) == 2,
    "module_id must be namespace/name",
)
@ensure(lambda result: cast(Path, result).exists(), "Downloaded module archive must exist")
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
    registry_index = index if index is not None else _find_registry_index_for_module(module_id, version, timeout)
    if not registry_index:
        raise ValueError("Cannot install from marketplace (offline)")

    entry = _select_module_entry_from_index(registry_index, module_id, version)
    full_download_url = resolve_download_url(
        entry, registry_index, cast(dict[str, Any], registry_index).get("_registry_index_url")
    )
    expected_checksum = str(entry.get("checksum_sha256", "")).strip().lower()
    if not full_download_url or not expected_checksum:
        raise ValueError("Invalid registry index format")

    content = _download_bytes_from_url(full_download_url, timeout)
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
