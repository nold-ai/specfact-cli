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
import json
import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import requests
from beartype import beartype
from icontract import ViolationError, require

from specfact_cli.registry.marketplace_client import get_modules_branch, resolve_download_url


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


class BundleCheckResult:
    """Lightweight container for per-bundle verification results."""

    def __init__(
        self,
        module_name: str,
        bundle_id: str,
        version: str | None,
        signature_ok: bool,
        download_ok: bool | None,
        status: str,
        message: str = "",
    ) -> None:
        self.module_name = module_name
        self.bundle_id = bundle_id
        self.version = version
        self.signature_ok = signature_ok
        self.download_ok = download_ok
        self.status = status
        self.message = message


@beartype
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
@require(lambda module_names: len([m for m in module_names if m.strip()]) > 0, "module_names must not be empty")
def verify_bundle_published(
    module_names: list[str],
    index_path: Path,
    *,
    modules_root: Path = _DEFAULT_MODULES_ROOT,
    skip_download_check: bool = False,
) -> list[BundleCheckResult]:
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

        version = str(entry.get("latest_version", "") or None)
        signature_ok = bool(entry.get("signature_ok", True))

        download_ok: bool | None = None
        if not skip_download_check:
            full_download_url = resolve_download_url(entry, index_payload, index_payload.get("_registry_index_url"))
            if full_download_url:
                download_ok = verify_bundle_download_url(full_download_url)

        status = "PASS"
        message = ""
        if not signature_ok:
            status = "FAIL"
            message = "SIGNATURE INVALID"
        elif download_ok is False:
            status = "FAIL"
            message = "DOWNLOAD ERROR"

        results.append(
            BundleCheckResult(
                module_name=module_key,
                bundle_id=bundle_id,
                version=version or None,
                signature_ok=signature_ok,
                download_ok=download_ok,
                status=status,
                message=message,
            )
        )

    return results


def _print_results(results: list[BundleCheckResult]) -> int:
    """Render results as a simple text table and return exit code."""
    print("module | bundle | version | signature | download | status | message")
    for result in results:
        signature_col = "OK" if result.signature_ok else "FAIL"
        if result.status == "MISSING":
            signature_col = "N/A"
        if result.message == "SIGNATURE INVALID":
            signature_col = "FAIL"
        download_col = "SKIP" if result.download_ok is None else ("OK" if result.download_ok else "FAIL")
        print(
            f"{result.module_name} | {result.bundle_id} | {result.version or '-'} | "
            f"{signature_col} | {download_col} | {result.status} | {result.message}"
        )

    has_failure = any(r.status != "PASS" for r in results)
    return 1 if has_failure else 0


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
    print(f"Using registry branch: {effective_branch}")

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
        print(f"Registry index not found: {exc}")
        return 1
    except ViolationError as exc:
        print(f"Precondition failed: {exc}")
        return 1
    except Exception as exc:
        print(f"Error while verifying bundles: {exc}")
        return 1

    return _print_results(results)


if __name__ == "__main__":
    raise SystemExit(main())
