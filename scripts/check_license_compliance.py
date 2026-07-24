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
from typing import Any, cast

import yaml
from beartype import beartype
from icontract import ensure
from packaging.requirements import InvalidRequirement, Requirement


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


@beartype
def _emit(message: str, *, error: bool = False) -> None:
    """Write a single log line without using ``print`` in source."""
    stream = sys.stderr if error else sys.stdout
    stream.write(f"{message}\n")
    stream.flush()


@beartype
def _validate_allowlist_entry(entry: object, *, index: int, allowlist_path: Path) -> dict[str, str]:
    """Validate one allowlist entry and return its normalized mapping."""
    if not isinstance(entry, dict):
        raise RuntimeError(f"Allowlist exceptions[{index}] must be a mapping in {allowlist_path}")
    entry_map = cast(dict[str, object], entry)

    pkg = entry_map.get("package")
    lic = entry_map.get("license")
    reason = entry_map.get("reason", "")
    version = entry_map.get("version")
    if not isinstance(pkg, str) or not pkg.strip():
        raise RuntimeError(f"Allowlist exceptions[{index}] must include non-empty 'package' in {allowlist_path}")
    if not isinstance(lic, str) or not lic.strip():
        raise RuntimeError(f"Allowlist exceptions[{index}] must include non-empty 'license' for package {pkg!r}")
    if not isinstance(reason, str) or not reason.strip():
        raise RuntimeError(f"Allowlist exceptions[{index}] must include non-empty 'reason' for package {pkg!r}")
    if version is not None and (not isinstance(version, str) or not version.strip()):
        raise RuntimeError(f"Allowlist exceptions[{index}] has invalid 'version' for package {pkg!r}")
    return cast(dict[str, str], entry_map)


def _load_allowlist(allowlist_path: Path | None = None) -> dict[str, list[dict[str, str]]]:
    """Load license_allowlist.yaml and return {package_lower: [entry_dict, ...]}."""
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
    data_map = cast(dict[str, object], data)

    exceptions = data_map.get("exceptions")
    if not isinstance(exceptions, list):
        raise RuntimeError(f"License allowlist must contain an 'exceptions' list: {allowlist_path}")

    result: dict[str, list[dict[str, str]]] = {}
    for idx, entry in enumerate(exceptions):
        normalized_entry = _validate_allowlist_entry(entry, index=idx, allowlist_path=allowlist_path)
        pkg_key = normalized_entry["package"].strip().lower()
        result.setdefault(pkg_key, []).append(normalized_entry)
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
    data_map = cast(dict[str, object], data)
    licenses = data_map.get("licenses")
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
    try:
        result = subprocess.run(
            [sys.executable, "-m", "piplicenses", "--format=json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        _emit(
            "ERROR: pip-licenses timed out after 60s — cannot verify licenses (fail closed)",
            error=True,
        )
        return ""
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        _emit(
            f"ERROR: pip-licenses subprocess failed (exit {result.returncode})",
            error=True,
        )
        if detail:
            _emit(detail, error=True)
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


@beartype
def _is_mixed_gpl_metadata(license_expr: str) -> bool:
    """Return whether metadata mixes a GPL token with permissive/public-domain terms."""
    normalized = license_expr.upper()
    permissive_markers = ("BSD", "MIT", "APACHE", "PUBLIC DOMAIN", "PSF")
    license_terms = re.split(r"\s*(?:;|/|\bOR\b|\bAND\b)\s*", normalized)
    has_gpl_term = any("LGPL" not in term and bool(_GPL_TOKEN_RE.search(term)) for term in license_terms)
    return has_gpl_term and any(marker in normalized for marker in permissive_markers)


@beartype
def _report_unknown_env_license(name: str, version: str) -> None:
    _emit(f"WARNING: {name}=={version} has no resolvable license — manual review required")


@beartype
def _allowlist_license_matches_observed(entry_license: str, observed_license: str) -> bool:
    """True when an allowlist entry's SPDX string matches the observed pip-licenses expression."""
    left = entry_license.strip().lower()
    right = observed_license.strip().lower()
    return bool(left) and left == right


@beartype
def _allowlist_version_matches_observed(
    entry: dict[str, str], observed_version: str, *, require_version: bool = False
) -> bool:
    """Return whether a reviewed version matches, with exact version required for mixed metadata."""
    reviewed_version = entry.get("version", "").strip()
    if not reviewed_version:
        return not require_version
    return reviewed_version == observed_version.strip()


@beartype
def _matching_allowlist_entries(
    entries: list[dict[str, str]], license_expr: str, version: str, *, require_version: bool = False
) -> list[dict[str, str]]:
    """Return reviewed entries matching observed license metadata and version."""
    return [
        entry
        for entry in entries
        if _allowlist_license_matches_observed(str(entry.get("license", "")), license_expr)
        and _allowlist_version_matches_observed(entry, version, require_version=require_version)
    ]


@beartype
def _emit_allowlist_exception(name: str, version: str, license_expr: str, entries: list[dict[str, str]]) -> None:
    """Report the reviewed rationale for an accepted license exception."""
    reasons = "; ".join(
        str(entry.get("reason", "")).strip() for entry in entries if str(entry.get("reason", "")).strip()
    )
    _emit(f"EXCEPTION: {name}=={version} ({license_expr}) — {reasons}")


@beartype
def _evaluate_mixed_gpl_metadata(name: str, version: str, license_expr: str, entries: list[dict[str, str]]) -> int:
    """Require a version-specific review for metadata mixing GPL and permissive terms."""
    reviewed_entries = _matching_allowlist_entries(entries, license_expr, version, require_version=True)
    if reviewed_entries:
        _emit_allowlist_exception(name, version, license_expr, reviewed_entries)
        return 0
    _emit(
        f"LICENSE CLASSIFICATION REQUIRED: {name}=={version} uses mixed metadata ({license_expr}) — "
        "add reviewed file-level licensing evidence before acceptance"
    )
    return 1


@beartype
def _evaluate_env_package(
    pkg: dict[str, Any],
    allowlist: dict[str, list[dict[str, str]]],
) -> int:
    """Return 1 when the package is a GPL violation, else 0."""
    name = str(pkg.get("Name", ""))
    version = str(pkg.get("Version", ""))
    license_expr = str(pkg.get("License", ""))

    if license_expr in {"UNKNOWN", "", "N/A", "None"}:
        _report_unknown_env_license(name, version)
        return 0

    name_lower = name.lower()
    entries_all = allowlist.get(name_lower, [])

    if _is_mixed_gpl_metadata(license_expr):
        return _evaluate_mixed_gpl_metadata(name, version, license_expr, entries_all)

    if not _is_gpl(license_expr):
        return 0

    entries = _matching_allowlist_entries(entries_all, license_expr, version)
    if entries:
        _emit_allowlist_exception(name, version, license_expr, entries)
        return 0

    _emit(f"LICENSE VIOLATION: {name}=={version} uses {license_expr} — GPL/AGPL incompatible with Apache-2.0")
    return 1


@beartype
@ensure(lambda result: result in (0, 1))
def scan_installed_environment(
    allowlist: dict[str, list[dict[str, str]]] | None = None,
    allowlist_path: Path | None = None,
) -> int:
    """
    Scan the installed Python environment for GPL/AGPL packages.

    Args:
        allowlist: Pre-loaded allowlist dict {package_lower: [entry, ...]}. If None, loads from disk.
        allowlist_path: Path to license_allowlist.yaml override.

    Returns:
        0 on clean pass, 1 on violation.
    """
    if allowlist is None:
        allowlist = _load_allowlist(allowlist_path)

    raw = _run_pip_licenses()
    if not raw.strip():
        _emit(
            "ERROR: pip-licenses produced no usable output — cannot verify licenses (fail closed)",
            error=True,
        )
        return 1
    try:
        packages: list[dict[str, Any]] = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        _emit(
            "ERROR: pip-licenses produced unparseable output — cannot verify licenses (fail closed)",
            error=True,
        )
        return 1

    violations = 0
    for pkg in packages:
        violations += _evaluate_env_package(pkg, allowlist)

    _emit(f"\nEnvironment scan: {len(packages)} packages checked, {violations} violation(s)")
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


@beartype
def _normalize_dependency_name(dep: str) -> str:
    """Normalize a pip requirement string to its canonical package name."""
    spec = dep.strip()
    if not spec:
        return ""
    try:
        return Requirement(spec).name.strip().lower()
    except InvalidRequirement as exc:
        raise ValueError(f"Invalid pip dependency spec: {dep!r}") from exc


@beartype
def _handle_missing_manifest_license(module_name: str, dep_name: str) -> int:
    _emit(
        f"MODULE MANIFEST VIOLATION: {module_name}/module-package.yaml lists {dep_name} "
        "without an SPDX license entry in scripts/module_pip_dependencies_licenses.yaml — "
        "add the package under 'licenses' after license review"
    )
    return 1


@beartype
def _handle_gpl_manifest_dependency(
    module_name: str,
    dep_name: str,
    license_expr: str,
    allowlist: dict[str, list[dict[str, str]]],
) -> int:
    """Return 1 when the manifest dependency is a GPL violation, else 0."""
    entries_all = allowlist.get(dep_name.lower(), [])
    entries = [e for e in entries_all if _allowlist_license_matches_observed(str(e.get("license", "")), license_expr)]
    for entry in entries:
        scope = str(entry.get("scope", ""))
        if scope == "module-manifest":
            _emit(
                f"EXCEPTION: {module_name}/module-package.yaml lists "
                f"{dep_name} ({license_expr}) — {str(entry.get('reason', '')).strip()}"
            )
            return 0

    for entry in entries_all:
        if not _allowlist_license_matches_observed(str(entry.get("license", "")), license_expr):
            continue
        scope = str(entry.get("scope", ""))
        if scope == "dev-only":
            _emit(
                f"MODULE MANIFEST VIOLATION: {module_name}/module-package.yaml lists "
                f"{dep_name} with {license_expr} — "
                "dev-only exception does not apply to distributed module manifests"
            )
            return 1

    _emit(
        f"MODULE MANIFEST VIOLATION: {module_name}/module-package.yaml lists "
        f"{dep_name} with {license_expr} — incompatible with Apache-2.0"
    )
    return 1


@beartype
def _scan_manifest_dependency(
    module_name: str,
    dep: str,
    allowlist: dict[str, list[dict[str, str]]],
    static_license_map: dict[str, str],
) -> int:
    try:
        dep_name = _normalize_dependency_name(dep)
    except ValueError as exc:
        _emit(f"MODULE MANIFEST VIOLATION: {module_name}/module-package.yaml has invalid pip dependency {dep!r}: {exc}")
        return 1
    license_expr = static_license_map.get(dep_name.lower(), "")
    if not license_expr:
        return _handle_missing_manifest_license(module_name, dep_name)
    if not _is_gpl(license_expr):
        return 0
    return _handle_gpl_manifest_dependency(module_name, dep_name, license_expr, allowlist)


@beartype
def _iter_manifest_dependencies(manifest_path: Path) -> list[str]:
    try:
        with manifest_path.open(encoding="utf-8") as fh:
            manifest = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        raise RuntimeError(f"YAML parse error in module manifest {manifest_path}: {exc}") from exc
    if not isinstance(manifest, dict):
        raise RuntimeError(f"Module manifest must be a mapping at top level: {manifest_path}")
    manifest_map = cast(dict[str, object], manifest)
    if "pip_dependencies" not in manifest_map:
        return []
    pip_deps_raw = manifest_map.get("pip_dependencies")
    if not isinstance(pip_deps_raw, list):
        raise RuntimeError(
            f"module-package.yaml {manifest_path} field pip_dependencies must be a list of strings, "
            f"got {type(pip_deps_raw).__name__}"
        )
    return [dep for dep in pip_deps_raw if isinstance(dep, str)]


@beartype
def _scan_manifest_path(
    manifest_path: Path,
    allowlist: dict[str, list[dict[str, str]]],
    static_license_map: dict[str, str],
) -> int:
    try:
        deps = _iter_manifest_dependencies(manifest_path)
    except RuntimeError as exc:
        _emit(str(exc), error=True)
        return 1
    module_name = manifest_path.parent.name
    return sum(_scan_manifest_dependency(module_name, dep, allowlist, static_license_map) for dep in deps)


@beartype
@ensure(lambda result: result in (0, 1))
def scan_module_manifests(
    packages_dir: Path | None = None,
    allowlist: dict[str, list[dict[str, str]]] | None = None,
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
            _emit(
                "ERROR: no module-package.yaml found under modules/ or "
                "src/specfact_cli/modules/ — manifest license gate cannot run",
                error=True,
            )
            return 1
        _emit("No module-package.yaml files found under scan root — skipping manifest scan")
        return 0

    violations = sum(
        _scan_manifest_path(manifest_path, allowlist, static_license_map) for manifest_path in sorted(manifest_paths)
    )
    _emit(f"\nManifest scan: {len(manifest_paths)} manifest(s) checked, {violations} violation(s)")
    return 1 if violations > 0 else 0


@beartype
@ensure(lambda result: result in (0, 1))
def main() -> int:
    """Run both env and manifest scans. Return combined exit code."""
    try:
        allowlist = _load_allowlist()
    except RuntimeError as exc:
        _emit(f"ERROR: {exc}", error=True)
        return 1

    _emit("=" * 60)
    _emit("specfact-cli License Compliance Gate")
    _emit("=" * 60)

    _emit("\n--- Installed environment scan ---")
    env_exit = scan_installed_environment(allowlist=allowlist)

    _emit("\n--- Module manifest scan ---")
    try:
        manifest_exit = scan_module_manifests(allowlist=allowlist)
    except RuntimeError as exc:
        _emit(f"ERROR: {exc}", error=True)
        manifest_exit = 1

    overall = 1 if (env_exit or manifest_exit) else 0
    _emit(f"\n{'PASS' if overall == 0 else 'FAIL'} — overall exit code: {overall}")
    return overall


if __name__ == "__main__":
    sys.exit(main())
