#!/usr/bin/env python3
"""Pre-deletion gate: verify that bundles for given modules are published and installable.

This script is intended to be run before deleting in-repo module source for the
17 non-core modules. It checks that each module's bundle:

- Resolves from module name -> bundle id using the `bundle` field in module-package.yaml
- Has an entry in the marketplace registry index.json
- Has a passing signature flag
- Optionally has a reachable download URL (HTTP HEAD), unless `--skip-download-check` is set

Registry index resolution (when --registry-index is omitted) supports both formats:

  a) SPECFACT_MODULES_REPO: set to the specfact-cli-modules repo root; index used is
     <SPECFACT_MODULES_REPO>/registry/index.json. Use for CI or when the modules repo
     is not next to this checkout.

  b) Sibling search (fallback when SPECFACT_MODULES_REPO is not set): from repo/worktree
     root (SPECFACT_REPO_ROOT or script location), search for sibling specfact-cli-modules
     at (base / "specfact-cli-modules") and (base.parent / "specfact-cli-modules") so
     both primary repo and worktree layouts work without env vars.

Download URL resolution uses specfact-cli-modules registry on GitHub (branch main or dev).
Use --branch to force main or dev; otherwise the script auto-detects from the current git
branch of specfact-cli (main → main, any other branch → dev). Keeps dev/feature in sync with
specfact-cli-modules dev; main with main.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
import os
import tarfile
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import requests
import yaml
from beartype import beartype
from icontract import ViolationError, ensure, require


logger = logging.getLogger(__name__)

from specfact_cli.models.module_package import ModulePackageMetadata  # noqa: E402
from specfact_cli.registry.marketplace_client import get_modules_branch, resolve_download_url  # noqa: E402
from specfact_cli.registry.module_installer import verify_module_artifact  # noqa: E402


_DEFAULT_INDEX_PATH = Path("../specfact-cli-modules/registry/index.json")
_DEFAULT_MODULES_ROOT = Path("src/specfact_cli/modules")


def _resolve_registry_index_path() -> Path:
    """Resolve registry index path: (a) SPECFACT_MODULES_REPO, else (b) sibling search.

    a) If SPECFACT_MODULES_REPO is set, return <that_path>/registry/index.json.
    b) Otherwise, from repo/worktree root (SPECFACT_REPO_ROOT or script dir), search
       for sibling specfact-cli-modules (base/specfact-cli-modules or base.parent/specfact-cli-modules)
       and return the first existing registry/index.json.
    """
    configured = os.environ.get("SPECFACT_MODULES_REPO")
    if configured:
        return Path(configured).expanduser().resolve() / "registry" / "index.json"
    repo_root = (
        Path(os.environ.get("SPECFACT_REPO_ROOT", str(Path(__file__).resolve().parent.parent))).expanduser().resolve()
    )
    for candidate_base in (repo_root, *repo_root.parents):
        for sibling_dir in (
            candidate_base / "specfact-cli-modules",
            candidate_base.parent / "specfact-cli-modules",
        ):
            index_path = sibling_dir / "registry" / "index.json"
            if index_path.exists():
                return index_path
    return repo_root / "specfact-cli-modules" / "registry" / "index.json"


@dataclass
class BundleCheckResult:
    """Lightweight container for per-bundle verification results."""

    module_name: str
    bundle_id: str
    version: str | None
    signature_ok: bool
    download_ok: bool | None
    status: str
    message: str = ""


@beartype
@require(
    lambda module_names: any(cast(str, name).strip() for name in module_names),
    "module_names must contain at least one value",
)
@ensure(lambda result: isinstance(result, dict), "returns mapping dictionary")
def load_module_bundle_mapping(module_names: list[str], modules_root: Path) -> dict[str, str]:
    """Resolve module name -> bundle id from module-package.yaml manifests."""
    mapping: dict[str, str] = {}
    for name in module_names:
        if not name:
            continue
        manifest = modules_root / name / "module-package.yaml"
        bundle_id = None
        if manifest.exists():
            # Minimal YAML parsing without pulling in ruamel; manifests are small.
            text = manifest.read_text(encoding="utf-8")
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("bundle:"):
                    _, value = stripped.split("bundle:", 1)
                    candidate = value.strip()
                    if candidate:
                        bundle_id = candidate
                        break
        if bundle_id is None:
            # Fallback: derive from module name
            bundle_id = f"specfact-{name.replace('_', '-')}"
        mapping[name] = bundle_id
    return mapping


@beartype
@require(lambda download_url: bool(cast(str, download_url).strip()), "download_url must be non-empty")
def verify_bundle_download_url(download_url: str) -> bool:
    """Return True when a HEAD request to download_url succeeds."""
    try:
        response = requests.head(download_url, allow_redirects=True, timeout=5)
    except Exception:
        return False
    return 200 <= response.status_code < 400


@beartype
def _iter_module_entries(index_payload: dict[str, Any]) -> Iterable[dict[str, Any]]:
    modules = index_payload.get("modules", [])
    if not isinstance(modules, list):
        return []
    return (entry for entry in modules if isinstance(entry, dict))


@beartype
def _resolve_local_download_path(download_url: str, index_path: Path) -> Path | None:
    """Resolve local tarball path from absolute/file URL/relative index path."""
    if download_url.startswith("file://"):
        return Path(download_url[len("file://") :]).expanduser().resolve()
    maybe_path = Path(download_url)
    if maybe_path.is_absolute():
        return maybe_path.resolve()
    # Relative URL/path in index resolves against index.json parent.
    return (index_path.parent / download_url).resolve()


@beartype
def _read_bundle_bytes(
    entry: dict[str, Any],
    index_payload: dict[str, Any],
    index_path: Path,
    *,
    allow_remote: bool,
) -> bytes | None:
    """Read bundle bytes from local path when available; optionally remote fallback."""
    full_download_url = resolve_download_url(entry, index_payload, index_payload.get("_registry_index_url"))
    if not full_download_url:
        return None
    local_path = _resolve_local_download_path(full_download_url, index_path)
    if local_path is None:
        return None
    if local_path.exists():
        try:
            return local_path.read_bytes()
        except OSError:
            return None
    if not allow_remote:
        return None
    try:
        response = requests.get(full_download_url, timeout=10)
        response.raise_for_status()
    except Exception:
        return None
    return response.content


@beartype
@ensure(lambda result: result is None or isinstance(result, bool), "returns verification result or None")
def verify_bundle_signature(
    entry: dict[str, Any],
    index_payload: dict[str, Any],
    index_path: Path,
    *,
    skip_download_check: bool,
) -> bool | None:
    """Verify artifact checksum+signature from bundle tarball when retrievable.

    Returns:
    - True/False when verification was executed.
    - None when verification was not possible (e.g., no local tarball in skip mode).
    """
    bundle_bytes = _read_bundle_bytes(
        entry,
        index_payload,
        index_path,
        allow_remote=not skip_download_check,
    )
    if bundle_bytes is None:
        return None

    checksum_expected = str(entry.get("checksum_sha256", "")).strip().lower()
    if not checksum_expected:
        return False
    checksum_actual = hashlib.sha256(bundle_bytes).hexdigest()
    if checksum_actual != checksum_expected:
        return False

    try:
        with tempfile.TemporaryDirectory(prefix="specfact-bundle-gate-") as tmp_dir:
            tmp_root = Path(tmp_dir)
            with tarfile.open(fileobj=io.BytesIO(bundle_bytes), mode="r:gz") as archive:
                archive.extractall(tmp_root)
            manifests = list(tmp_root.rglob("module-package.yaml"))
            if not manifests:
                return False
            manifest_path = manifests[0]
            raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return False
            metadata = ModulePackageMetadata(**raw)
            return verify_module_artifact(
                package_dir=manifest_path.parent,
                meta=metadata,
                allow_unsigned=False,
                require_signature=True,
            )
    except Exception:
        return False


def _registry_entry_missing_fields(entry: dict[str, Any]) -> list[str]:
    """Return sorted list of missing required registry fields for an entry."""
    required_fields = {"latest_version", "download_url", "checksum_sha256"}
    missing = sorted(field for field in required_fields if not str(entry.get(field, "")).strip())
    tier = str(entry.get("tier", "")).strip().lower()
    has_signature_hint = bool(str(entry.get("signature_url", "")).strip()) or "signature_ok" in entry
    if tier == "official" and not has_signature_hint:
        missing.append("signature_url/signature_ok")
    return missing


def _bundle_check_status_after_verification(
    signature_ok: bool,
    download_ok: bool | None,
) -> tuple[str, str]:
    """Return (status, message) from signature and optional download result."""
    if not signature_ok:
        return "FAIL", "SIGNATURE INVALID"
    if download_ok is False:
        return "FAIL", "DOWNLOAD ERROR"
    return "PASS", ""


@beartype
@ensure(lambda result: isinstance(result, BundleCheckResult), "returns BundleCheckResult")
def check_bundle_in_registry(
    module_name: str,
    bundle_id: str,
    entry: dict[str, Any],
    index_payload: dict[str, Any],
    index_path: Path,
    *,
    skip_download_check: bool,
) -> BundleCheckResult:
    """Validate one bundle entry and return normalized status."""
    missing = _registry_entry_missing_fields(entry)
    if missing:
        return BundleCheckResult(
            module_name=module_name,
            bundle_id=bundle_id,
            version=str(entry.get("latest_version", "") or None),
            signature_ok=False,
            download_ok=None,
            status="FAIL",
            message=f"Missing required fields: {', '.join(missing)}",
        )

    signature_result = verify_bundle_signature(
        entry=entry,
        index_payload=index_payload,
        index_path=index_path,
        skip_download_check=skip_download_check,
    )
    signature_ok = signature_result if signature_result is not None else bool(entry.get("signature_ok", True))

    download_ok: bool | None = None
    if not skip_download_check:
        full_download_url = resolve_download_url(entry, index_payload, index_payload.get("_registry_index_url"))
        if full_download_url:
            download_ok = verify_bundle_download_url(full_download_url)

    status, message = _bundle_check_status_after_verification(signature_ok, download_ok)

    return BundleCheckResult(
        module_name=module_name,
        bundle_id=bundle_id,
        version=str(entry.get("latest_version", "") or None),
        signature_ok=signature_ok,
        download_ok=download_ok,
        status=status,
        message=message,
    )


@beartype
@require(
    lambda module_names: len([m for m in module_names if cast(str, m).strip()]) > 0,
    "module_names must not be empty",
)
@ensure(lambda result: isinstance(result, list), "returns result list")
def verify_bundle_published(
    module_names: list[str],
    index_path: Path,
    *,
    modules_root: Path = _DEFAULT_MODULES_ROOT,
    skip_download_check: bool = False,
) -> list[Any]:
    """Verify that bundles for all given module names are present and valid in registry index."""
    if not index_path.exists():
        raise FileNotFoundError(f"Registry index not found at {index_path}")

    try:
        index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError(f"Unable to parse registry index at {index_path}: {exc}") from exc

    mapping = load_module_bundle_mapping(module_names, modules_root)
    results: list[BundleCheckResult] = []

    entries = list(_iter_module_entries(index_payload))
    for module_name in module_names:
        module_key = module_name.strip()
        if not module_key:
            continue
        bundle_id = mapping.get(module_key, f"specfact-{module_key}")
        expected_full_id = bundle_id if "/" in bundle_id else f"nold-ai/{bundle_id}"

        entry = next((e for e in entries if str(e.get("id")) == expected_full_id), None)
        if entry is None:
            results.append(
                BundleCheckResult(
                    module_name=module_key,
                    bundle_id=bundle_id,
                    version=None,
                    signature_ok=False,
                    download_ok=None,
                    status="MISSING",
                    message="Bundle not found in registry index",
                )
            )
            continue

        results.append(
            check_bundle_in_registry(
                module_name=module_key,
                bundle_id=bundle_id,
                entry=entry,
                index_payload=index_payload,
                index_path=index_path,
                skip_download_check=skip_download_check,
            )
        )

    return results


def _print_results(results: list[BundleCheckResult]) -> int:
    """Render results as a simple text table and return exit code."""
    logger.info("module | bundle | version | signature | download | status | message")
    for result in results:
        signature_col = "OK" if result.signature_ok else "FAIL"
        if result.status == "MISSING":
            signature_col = "N/A"
        if result.message == "SIGNATURE INVALID":
            signature_col = "FAIL"
        download_col = "SKIP" if result.download_ok is None else ("OK" if result.download_ok else "FAIL")
        logger.info(
            "%s | %s | %s | %s | %s | %s | %s",
            result.module_name,
            result.bundle_id,
            result.version or "-",
            signature_col,
            download_col,
            result.status,
            result.message,
        )

    has_failure = any(r.status != "PASS" for r in results)
    return 1 if has_failure else 0


@beartype
@require(lambda argv: argv is None or isinstance(argv, list), "argv must be a list or None")
@ensure(lambda result: result >= 0, "exit code must be non-negative")
def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--modules",
        required=True,
        help="Comma-separated list of module names (e.g. project,plan,backlog,...)",
    )
    parser.add_argument(
        "--registry-index",
        default=None,
        help="Path to registry index.json (default: resolved from SPECFACT_MODULES_REPO or worktree/sibling specfact-cli-modules)",
    )
    parser.add_argument(
        "--skip-download-check",
        action="store_true",
        help="Skip HTTP HEAD download URL verification (signature and presence only).",
    )
    parser.add_argument(
        "--branch",
        choices=["dev", "main"],
        default=None,
        help="Registry branch for download URLs (main or dev). Default: auto-detect from current git branch (main → main, else dev).",
    )
    args = parser.parse_args(argv)

    if args.branch is not None:
        os.environ["SPECFACT_MODULES_BRANCH"] = args.branch
        get_modules_branch.cache_clear()
    effective_branch = args.branch if args.branch is not None else get_modules_branch()
    logger.info("Using registry branch: %s", effective_branch)

    raw_modules = [m.strip() for m in args.modules.split(",")]
    module_names = [m for m in raw_modules if m]
    index_path = Path(args.registry_index) if args.registry_index else _resolve_registry_index_path()

    try:
        results = verify_bundle_published(
            module_names=module_names,
            index_path=index_path,
            modules_root=_DEFAULT_MODULES_ROOT,
            skip_download_check=args.skip_download_check,
        )
    except FileNotFoundError as exc:
        logger.error("Registry index not found: %s", exc)
        return 1
    except ViolationError as exc:
        logger.error("Precondition failed: %s", exc)
        return 1
    except Exception as exc:
        logger.error("Error while verifying bundles: %s", exc)
        return 1

    return _print_results(results)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    raise SystemExit(main())
