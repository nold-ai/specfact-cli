"""
Detect bundled modules whose manifest `version:` is strictly greater than the
version currently recorded for that module in the registry index.

Used by `.github/workflows/publish-modules.yml` to decide which bundled modules
an auto-publish run should package and upsert into
``resources/bundled-module-registry/index.json`` (PR opened in ``specfact-cli``).
Output is one module directory per line (newline-separated, no trailing newline).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, cast

import yaml
from beartype import beartype
from icontract import ensure, require
from packaging.version import InvalidVersion, Version


@beartype
@require(lambda path: path.exists() and path.is_file(), "Registry index file must exist")
@ensure(lambda result: isinstance(result, dict))
def _load_registry_versions(path: Path) -> dict[str, str]:
    """Return {module_id: latest_version_str} from registry/index.json."""
    try:
        raw_obj: object = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Registry index JSON is invalid ({path}): {exc}") from exc
    if not isinstance(raw_obj, dict):
        raise ValueError(f"Registry index JSON root must be an object ({path})")
    raw = cast(dict[str, Any], raw_obj)
    if "modules" not in raw or not isinstance(raw["modules"], list):
        raise ValueError(
            f"Registry index at {path} must contain a JSON array at key 'modules' "
            "(same contract as scripts/update-registry-index.py)."
        )
    modules = cast(list[Any], raw["modules"])
    versions: dict[str, str] = {}
    for entry in modules:
        if not isinstance(entry, dict):
            continue
        module_id = entry.get("id")
        latest = entry.get("latest_version")
        if isinstance(module_id, str) and isinstance(latest, str):
            versions[module_id] = latest.strip()
    return versions


@beartype
@require(lambda path: path.exists() and path.is_file(), "Manifest must exist")
def _read_manifest(path: Path) -> tuple[str | None, str | None]:
    """Return (module_id, version) from a module-package.yaml."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        return None, None
    module_id = raw.get("id") or raw.get("name")
    version = raw.get("version")
    module_id_s = str(module_id).strip() if module_id else None
    version_s = str(version).strip() if version else None
    return module_id_s or None, version_s or None


@beartype
def _is_strictly_newer(candidate: str, registered: str | None) -> bool:
    if not registered:
        return True
    try:
        cand = Version(candidate)
    except InvalidVersion:
        return False
    try:
        reg = Version(registered)
    except InvalidVersion:
        return False
    return cand > reg


@beartype
def _iter_manifests(roots: list[Path]) -> list[Path]:
    manifests: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        manifests.extend(sorted(root.rglob("module-package.yaml")))
    return manifests


@beartype
def _select_modules_to_publish(manifests: list[Path], registry_versions: dict[str, str]) -> list[Path]:
    selected: list[Path] = []
    for manifest in manifests:
        module_id, version = _read_manifest(manifest)
        if not module_id or not version:
            print(
                f"SKIP: {manifest} missing id/version (id={module_id!r} version={version!r})",
                file=sys.stderr,
            )
            continue
        registered = registry_versions.get(module_id)
        if _is_strictly_newer(version, registered):
            print(
                f"PUBLISH: {module_id} manifest={version} registry={registered or '<none>'}",
                file=sys.stderr,
            )
            selected.append(manifest.parent)
        else:
            print(
                f"SKIP: {module_id} manifest={version} <= registry={registered}",
                file=sys.stderr,
            )
    return selected


@beartype
@require(lambda argv: argv is None or (isinstance(argv, list) and all(isinstance(x, str) for x in argv)))
@ensure(lambda result: isinstance(result, int))
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry-index", required=True, type=Path)
    parser.add_argument(
        "--modules-root",
        action="append",
        required=True,
        type=Path,
        help="Repeat to search multiple roots (e.g. src/specfact_cli/modules and modules)",
    )
    parser.add_argument("--output-list", required=True, type=Path)
    args = parser.parse_args(argv)

    registry_versions = _load_registry_versions(args.registry_index)
    manifests = _iter_manifests(args.modules_root)
    selected = _select_modules_to_publish(manifests, registry_versions)

    args.output_list.write_text(
        "\n".join(str(p) for p in selected),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
