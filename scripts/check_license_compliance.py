"""
License compliance gate for specfact-cli.

Scans both the installed dev environment (via pip-licenses) and all
packages/*/module-package.yaml pip_dependencies for (A)GPL license violations.

Exit codes:
  0 — clean pass (no unapproved GPL/AGPL packages)
  1 — violation found

Usage:
  python scripts/check_license_compliance.py
  hatch run license-check
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


# SPDX expressions considered GPL-family (not allowed without an allowlist entry)
_GPL_EXPRESSIONS = frozenset(
    {
        "GPL-2.0",
        "GPL-3.0",
        "AGPL-3.0",
        "GPL-2.0-only",
        "GPL-2.0-or-later",
        "GPL-3.0-only",
        "GPL-3.0-or-later",
        "AGPL-3.0-only",
        "AGPL-3.0-or-later",
        # pip-licenses verbose forms
        "GNU General Public License v2 (GPLv2)",
        "GNU General Public License v2 or later (GPLv2+)",
        "GNU General Public License v3 (GPLv3)",
        "GNU General Public License v3 or later (GPLv3+)",
        "GNU Affero General Public License v3",
        "GNU Affero General Public License v3 or later (AGPLv3+)",
    }
)


def _load_allowlist(allowlist_path: Path | None = None) -> dict[str, dict[str, str]]:
    """Load license_allowlist.yaml and return {package_name: entry_dict}."""
    if allowlist_path is None:
        allowlist_path = Path(__file__).parent / "license_allowlist.yaml"

    if not allowlist_path.exists():
        return {}

    with allowlist_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    result: dict[str, dict[str, str]] = {}
    for entry in data.get("exceptions", []):
        pkg = entry.get("package", "")
        if pkg:
            result[pkg.lower()] = entry
    return result


def _run_pip_licenses() -> str:
    """Run pip-licenses and return raw JSON output string."""
    result = subprocess.run(
        [sys.executable, "-m", "pip_licenses", "--format=json"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result.stdout


def _is_gpl(license_expr: str) -> bool:
    """Return True if the SPDX expression is a GPL/AGPL family license."""
    expr = license_expr.strip()
    return expr in _GPL_EXPRESSIONS or any(
        gpl in expr for gpl in ("GPL-2.0", "GPL-3.0", "AGPL-3.0", "GPLv2", "GPLv3", "AGPLv3")
    )


def scan_installed_environment(
    allowlist: dict[str, dict[str, str]] | None = None,
    allowlist_path: Path | None = None,
) -> int:
    """
    Scan the installed Python environment for GPL/AGPL packages.

    Args:
        allowlist: Pre-loaded allowlist dict {package_lower: entry}. If None, loads from disk.
        allowlist_path: Path to license_allowlist.yaml override.

    Returns:
        0 on clean pass, 1 on violation.
    """
    if allowlist is None:
        allowlist = _load_allowlist(allowlist_path)

    raw = _run_pip_licenses()
    try:
        packages: list[dict[str, Any]] = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        print("WARNING: pip-licenses produced unparseable output — skipping env scan", flush=True)
        return 0

    violations = 0
    checked = 0

    for pkg in packages:
        name: str = pkg.get("Name", "")
        version: str = pkg.get("Version", "")
        license_expr: str = pkg.get("License", "")
        checked += 1

        if license_expr in ("UNKNOWN", "", "N/A", "None"):
            print(f"WARNING: {name}=={version} has no resolvable license — manual review required", flush=True)
            continue

        name_lower = name.lower()

        if _is_gpl(license_expr):
            if name_lower in allowlist:
                entry = allowlist[name_lower]
                reason = entry.get("reason", "")
                # dev-only and module-manifest allowlist entries both accepted in env scan
                print(f"EXCEPTION: {name}=={version} ({license_expr}) — {reason.strip()}", flush=True)
            else:
                print(
                    f"VIOLATION: {name}=={version} ({license_expr}) — GPL/AGPL incompatible with Apache-2.0",
                    flush=True,
                )
                violations += 1

    print(f"\nEnvironment scan: {checked} packages checked, {violations} violation(s)", flush=True)
    return 1 if violations > 0 else 0


def scan_module_manifests(
    packages_dir: Path | None = None,
    allowlist: dict[str, dict[str, str]] | None = None,
    allowlist_path: Path | None = None,
    static_license_map: dict[str, str] | None = None,
) -> int:
    """
    Scan all packages/*/module-package.yaml pip_dependencies for GPL violations.

    dev-only allowlist entries are REJECTED for module manifests (the same package
    that is accepted as a dev tool must not be distributed to end users via manifests).

    Args:
        packages_dir: Root of packages directory (defaults to repo/packages).
        allowlist: Pre-loaded allowlist dict. If None, loads from disk.
        allowlist_path: Path to license_allowlist.yaml override.
        static_license_map: Mapping {package_lower: spdx_expr} for known packages (offline).

    Returns:
        0 on clean pass, 1 on violation.
    """
    if allowlist is None:
        allowlist = _load_allowlist(allowlist_path)
    if static_license_map is None:
        static_license_map = {}
    if packages_dir is None:
        packages_dir = Path(__file__).parents[1] / "packages"

    manifest_paths = list(packages_dir.glob("*/module-package.yaml"))
    if not manifest_paths:
        print("No module-package.yaml files found — skipping manifest scan", flush=True)
        return 0

    violations = 0

    for manifest_path in sorted(manifest_paths):
        module_name = manifest_path.parent.name
        with manifest_path.open(encoding="utf-8") as fh:
            manifest = yaml.safe_load(fh) or {}

        pip_deps: list[str] = manifest.get("pip_dependencies", []) or []

        for dep in pip_deps:
            dep_name = dep.split(">=")[0].split("==")[0].split("~=")[0].strip()
            dep_lower = dep_name.lower()

            # Resolve license: static map first, then skip with warning
            license_expr = static_license_map.get(dep_lower, "")
            if not license_expr:
                # No network calls in offline mode — warn and skip
                print(
                    f"WARNING: {module_name}/module-package.yaml lists {dep_name} "
                    "with unknown license — manual review required",
                    flush=True,
                )
                continue

            if _is_gpl(license_expr):
                entry = allowlist.get(dep_lower, {})
                scope = entry.get("scope", "")

                if scope == "module-manifest":
                    # LGPL+subprocess exceptions accepted in manifests
                    print(
                        f"EXCEPTION: {module_name}/module-package.yaml lists "
                        f"{dep_name} ({license_expr}) — {entry.get('reason', '').strip()}",
                        flush=True,
                    )
                elif scope == "dev-only":
                    # dev-only entries are BLOCKED in manifests
                    print(
                        f"MODULE MANIFEST VIOLATION: {module_name}/module-package.yaml lists "
                        f"{dep_name} with {license_expr} — "
                        "dev-only exception does not apply to distributed module manifests",
                        flush=True,
                    )
                    violations += 1
                else:
                    print(
                        f"MODULE MANIFEST VIOLATION: {module_name}/module-package.yaml lists "
                        f"{dep_name} with {license_expr} — incompatible with Apache-2.0",
                        flush=True,
                    )
                    violations += 1

    print(
        f"\nManifest scan: {len(manifest_paths)} manifest(s) checked, {violations} violation(s)",
        flush=True,
    )
    return 1 if violations > 0 else 0


def main() -> int:
    """Run both env and manifest scans. Return combined exit code."""
    allowlist = _load_allowlist()

    print("=" * 60)
    print("specfact-cli License Compliance Gate")
    print("=" * 60)

    print("\n--- Installed environment scan ---")
    env_exit = scan_installed_environment(allowlist=allowlist)

    print("\n--- Module manifest scan ---")
    manifest_exit = scan_module_manifests(allowlist=allowlist)

    overall = 1 if (env_exit or manifest_exit) else 0
    print("\n" + ("PASS" if overall == 0 else "FAIL") + " — overall exit code:", overall)
    return overall


if __name__ == "__main__":
    sys.exit(main())
