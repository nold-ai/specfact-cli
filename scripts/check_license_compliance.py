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
import re
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

_GPL_TOKEN_RE = re.compile(r"(?<![A-Za-z])(?:AGPL|GPL)", re.IGNORECASE)


def _load_allowlist(allowlist_path: Path | None = None) -> dict[str, dict[str, str]]:
    """Load license_allowlist.yaml and return {package_name: entry_dict}."""
    if allowlist_path is None:
        allowlist_path = Path(__file__).parent / "license_allowlist.yaml"

    if not allowlist_path.exists():
        raise RuntimeError(
            f"License allowlist not found: {allowlist_path} "
            "(expected scripts/license_allowlist.yaml or pass allowlist_path=)"
        )

    with allowlist_path.open(encoding="utf-8") as fh:
        try:
            data = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise RuntimeError(f"YAML parse error in license allowlist {allowlist_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise RuntimeError(f"License allowlist root must be a mapping: {allowlist_path}")

    exceptions = data.get("exceptions")
    if not isinstance(exceptions, list):
        raise RuntimeError(f"License allowlist must contain an 'exceptions' list: {allowlist_path}")

    result: dict[str, dict[str, str]] = {}
    for idx, entry in enumerate(exceptions):
        if not isinstance(entry, dict):
            raise RuntimeError(f"Allowlist exceptions[{idx}] must be a mapping in {allowlist_path}")
        pkg = entry.get("package")
        lic = entry.get("license")
        reason = entry.get("reason", "")
        if not isinstance(pkg, str) or not pkg.strip():
            raise RuntimeError(f"Allowlist exceptions[{idx}] must include non-empty 'package' in {allowlist_path}")
        if not isinstance(lic, str) or not lic.strip():
            raise RuntimeError(f"Allowlist exceptions[{idx}] must include non-empty 'license' for package {pkg!r}")
        if not isinstance(reason, str) or not reason.strip():
            raise RuntimeError(f"Allowlist exceptions[{idx}] must include non-empty 'reason' for package {pkg!r}")
        result[pkg.strip().lower()] = entry
    return result


def _load_manifest_license_map(map_path: Path | None = None) -> dict[str, str]:
    """Load ``module_pip_dependencies_licenses.yaml`` → ``{package_lower: spdx_expr}``."""
    if map_path is None:
        map_path = Path(__file__).parent / "module_pip_dependencies_licenses.yaml"
    if not map_path.exists():
        raise RuntimeError(
            f"Manifest license mapping not found: {map_path} (expected scripts/module_pip_dependencies_licenses.yaml)"
        )
    with map_path.open(encoding="utf-8") as fh:
        try:
            data = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise RuntimeError(f"YAML parse error in manifest license map {map_path}: {exc}") from exc
    if data is None:
        raise RuntimeError(f"Manifest license mapping is empty or invalid YAML: {map_path}")
    licenses = data.get("licenses")
    if not isinstance(licenses, dict):
        raise RuntimeError(f"Manifest license mapping must contain a 'licenses' mapping in {map_path}")
    out: dict[str, str] = {}
    for key, val in licenses.items():
        if not isinstance(key, str) or not isinstance(val, str):
            raise RuntimeError(f"Invalid licenses entry in {map_path}: {key!r}: {val!r}")
        out[key.strip().lower()] = val.strip()
    return out


def _run_pip_licenses() -> str:
    """Run pip-licenses and return raw JSON output string (empty if the subprocess fails)."""
    result = subprocess.run(
        [sys.executable, "-m", "pip_licenses", "--format=json"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        print(
            f"ERROR: pip-licenses subprocess failed (exit {result.returncode})",
            flush=True,
        )
        if detail:
            print(detail, flush=True)
        return ""
    return result.stdout


def _is_gpl(license_expr: str) -> bool:
    """Return True if the SPDX expression is a GPL/AGPL family license (not LGPL)."""
    expr = license_expr.strip()
    if not expr:
        return False
    if expr in _GPL_EXPRESSIONS:
        return True
    norm = expr.upper()
    if "LGPL" in norm:
        return False
    return bool(_GPL_TOKEN_RE.search(norm))


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
    if not raw.strip():
        print(
            "ERROR: pip-licenses produced no usable output — cannot verify licenses (fail closed)",
            flush=True,
        )
        return 1
    try:
        packages: list[dict[str, Any]] = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        print(
            "ERROR: pip-licenses produced unparseable output — cannot verify licenses (fail closed)",
            flush=True,
        )
        return 1

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


def _repo_root() -> Path:
    """Repository root (parent of ``scripts/``)."""
    return Path(__file__).resolve().parents[1]


def _collect_module_manifest_paths(repo_root: Path, packages_dir: Path | None) -> list[Path]:
    """Resolve ``module-package.yaml`` paths; explicit ``packages_dir`` keeps tests' layout."""
    if packages_dir is not None:
        return sorted(packages_dir.glob("*/module-package.yaml"))
    paths: list[Path] = []
    for base in (repo_root / "modules", repo_root / "src" / "specfact_cli" / "modules"):
        if base.is_dir():
            paths.extend(base.glob("*/module-package.yaml"))
    return sorted(set(paths))


def scan_module_manifests(
    packages_dir: Path | None = None,
    allowlist: dict[str, dict[str, str]] | None = None,
    allowlist_path: Path | None = None,
    static_license_map: dict[str, str] | None = None,
) -> int:
    """
    Scan module ``module-package.yaml`` files for GPL violations in ``pip_dependencies``.

    Default roots: ``modules/*/module-package.yaml`` and
    ``src/specfact_cli/modules/*/module-package.yaml`` (this repo does not use
    ``packages/`` for manifests).

    dev-only allowlist entries are REJECTED for module manifests (the same package
    that is accepted as a dev tool must not be distributed to end users via manifests).

    Args:
        packages_dir: If set, only ``<packages_dir>/*/module-package.yaml`` is scanned
            (used by tests). If None, the default repo manifest locations above are used.
        allowlist: Pre-loaded allowlist dict. If None, loads from disk.
        allowlist_path: Path to license_allowlist.yaml override.
        static_license_map: Mapping ``{package_lower: spdx_expr}`` for known packages (offline).
            When ``None``, loads ``scripts/module_pip_dependencies_licenses.yaml``.

    Returns:
        0 on clean pass, 1 on violation.
    """
    if allowlist is None:
        allowlist = _load_allowlist(allowlist_path)
    if static_license_map is None:
        static_license_map = _load_manifest_license_map()

    repo_root = _repo_root()
    manifest_paths = _collect_module_manifest_paths(repo_root, packages_dir)
    if not manifest_paths:
        if packages_dir is None:
            print(
                "ERROR: no module-package.yaml found under modules/ or "
                "src/specfact_cli/modules/ — manifest license gate cannot run",
                flush=True,
            )
            return 1
        print("No module-package.yaml files found under scan root — skipping manifest scan", flush=True)
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
                print(
                    f"MODULE MANIFEST VIOLATION: {module_name}/module-package.yaml lists {dep_name} "
                    "without an SPDX license entry in scripts/module_pip_dependencies_licenses.yaml — "
                    "add the package under 'licenses' after license review",
                    flush=True,
                )
                violations += 1
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
    try:
        allowlist = _load_allowlist()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", flush=True)
        return 1

    print("=" * 60)
    print("specfact-cli License Compliance Gate")
    print("=" * 60)

    print("\n--- Installed environment scan ---")
    env_exit = scan_installed_environment(allowlist=allowlist)

    print("\n--- Module manifest scan ---")
    try:
        manifest_exit = scan_module_manifests(allowlist=allowlist)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", flush=True)
        manifest_exit = 1

    overall = 1 if (env_exit or manifest_exit) else 0
    print("\n" + ("PASS" if overall == 0 else "FAIL") + " — overall exit code:", overall)
    return overall


if __name__ == "__main__":
    sys.exit(main())
