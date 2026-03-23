"""
SDD discovery utilities for multi-SDD support.

This module provides utilities for discovering and managing multiple SDD manifests
in a repository, supporting both single-SDD (legacy) and multi-SDD (recommended)
layouts.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.sdd import SDDManifest
from specfact_cli.utils.structure import SpecFactStructure
from specfact_cli.utils.structured_io import StructuredFormat, load_structured_file


def _load_sdd_manifest_tuple(candidate: Path) -> tuple[Path, SDDManifest] | None:
    try:
        sdd_data = load_structured_file(candidate)
        return (candidate.resolve(), SDDManifest(**sdd_data))
    except Exception:
        return None


def _append_sdd_candidates(results: list[tuple[Path, SDDManifest]], candidates: Iterable[Path]) -> None:
    for candidate in candidates:
        if not candidate.exists():
            continue
        loaded = _load_sdd_manifest_tuple(candidate)
        if loaded:
            results.append(loaded)


def _collect_bundle_specific_sdds(base_path: Path, results: list[tuple[Path, SDDManifest]]) -> None:
    projects_dir = base_path / SpecFactStructure.PROJECTS
    if not (projects_dir.exists() and projects_dir.is_dir()):
        return
    for bundle_dir in projects_dir.iterdir():
        if not bundle_dir.is_dir():
            continue
        _append_sdd_candidates(results, (bundle_dir / "sdd.yaml", bundle_dir / "sdd.json"))


def _collect_legacy_multi_sdds(base_path: Path, results: list[tuple[Path, SDDManifest]]) -> None:
    sdd_dir = base_path / SpecFactStructure.SDD
    if not (sdd_dir.exists() and sdd_dir.is_dir()):
        return
    for sdd_file in list(sdd_dir.glob("*.yaml")) + list(sdd_dir.glob("*.json")):
        loaded = _load_sdd_manifest_tuple(sdd_file)
        if loaded:
            results.append(loaded)


def _collect_legacy_single_sdds(base_path: Path, results: list[tuple[Path, SDDManifest]]) -> None:
    for legacy_file in (
        base_path / SpecFactStructure.ROOT / "sdd.yaml",
        base_path / SpecFactStructure.ROOT / "sdd.json",
    ):
        if legacy_file.exists():
            loaded = _load_sdd_manifest_tuple(legacy_file)
            if loaded:
                results.append(loaded)


@beartype
@require(lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0, "Bundle name must be non-empty")
@require(lambda base_path: isinstance(base_path, Path), "Base path must be Path")
@require(lambda sdd_path: sdd_path is None or isinstance(sdd_path, Path), "SDD path must be None or Path")
@ensure(
    lambda result: result is None or (isinstance(result, Path) and result.exists()),
    "Result must be None or existing Path",
)
def find_sdd_for_bundle(bundle_name: str, base_path: Path, sdd_path: Path | None = None) -> Path | None:
    """
    Find SDD manifest for a project bundle.

    Discovery order (Phase 8.5: Bundle-Specific Artifact Organization):
    1. If --sdd is provided, use that path
    2. Search for .specfact/projects/<bundle-name>/sdd.yaml (bundle-specific, Phase 8.5)
    3. Search for .specfact/projects/<bundle-name>/sdd.json (bundle-specific, Phase 8.5)
    4. Fallback to .specfact/sdd/<bundle-name>.yaml (legacy multi-SDD layout)
    5. Fallback to .specfact/sdd/<bundle-name>.json (legacy multi-SDD layout)
    6. Fallback to .specfact/sdd.yaml (legacy single-SDD layout)
    7. Fallback to .specfact/sdd.json (legacy single-SDD layout)

    Args:
        bundle_name: Project bundle name (e.g., "legacy-api")
        base_path: Base repository path
        sdd_path: Explicit SDD path (if provided, used directly)

    Returns:
        Path to SDD manifest if found, None otherwise
    """
    if sdd_path is not None:
        if sdd_path.exists():
            return sdd_path.resolve()
        return None

    # Phase 8.5: Bundle-specific SDD location (NEW - preferred)
    bundle_sdd_yaml = SpecFactStructure.get_bundle_sdd_path(bundle_name, base_path, StructuredFormat.YAML)
    if bundle_sdd_yaml.exists():
        return bundle_sdd_yaml.resolve()

    bundle_sdd_json = SpecFactStructure.get_bundle_sdd_path(bundle_name, base_path, StructuredFormat.JSON)
    if bundle_sdd_json.exists():
        return bundle_sdd_json.resolve()

    # Legacy multi-SDD layout: .specfact/sdd/<bundle-name>.yaml
    sdd_dir = base_path / SpecFactStructure.SDD
    legacy_bundle_sdd_yaml = sdd_dir / f"{bundle_name}.yaml"
    if legacy_bundle_sdd_yaml.exists():
        return legacy_bundle_sdd_yaml.resolve()

    legacy_bundle_sdd_json = sdd_dir / f"{bundle_name}.json"
    if legacy_bundle_sdd_json.exists():
        return legacy_bundle_sdd_json.resolve()

    # Legacy single-SDD layout: .specfact/sdd.yaml
    legacy_sdd_yaml = base_path / SpecFactStructure.ROOT / "sdd.yaml"
    if legacy_sdd_yaml.exists():
        return legacy_sdd_yaml.resolve()

    legacy_sdd_json = base_path / SpecFactStructure.ROOT / "sdd.json"
    if legacy_sdd_json.exists():
        return legacy_sdd_json.resolve()

    return None


@beartype
@require(lambda base_path: isinstance(base_path, Path), "Base path must be Path")
@ensure(lambda result: isinstance(result, list), "Must return list")
def list_all_sdds(base_path: Path) -> list[tuple[Path, SDDManifest]]:
    """
    List all SDD manifests in the repository.

    Searches bundle-specific locations first (.specfact/projects/<bundle>/sdd.{yaml,json}),
    then legacy multi-SDD directory (.specfact/sdd/*.yaml),
    and legacy single-SDD file (.specfact/sdd.yaml).

    Args:
        base_path: Base repository path

    Returns:
        List of (path, manifest) tuples for all found SDD manifests
    """
    results: list[tuple[Path, SDDManifest]] = []
    _collect_bundle_specific_sdds(base_path, results)
    _collect_legacy_multi_sdds(base_path, results)
    _collect_legacy_single_sdds(base_path, results)
    return results


@beartype
@require(lambda plan_hash: isinstance(plan_hash, str) and len(plan_hash) > 0, "Plan hash must be non-empty string")
@require(lambda base_path: isinstance(base_path, Path), "Base path must be Path")
@ensure(
    lambda result: result is None or (isinstance(result, Path) and result.exists()),
    "Result must be None or existing Path",
)
def get_sdd_by_hash(plan_hash: str, base_path: Path) -> Path | None:
    """
    Find SDD manifest by plan bundle hash (legacy support).

    Searches all SDD manifests and returns the first one matching the hash.

    Args:
        plan_hash: Plan bundle content hash
        base_path: Base repository path

    Returns:
        Path to SDD manifest if found, None otherwise
    """
    all_sdds = list_all_sdds(base_path)
    for sdd_path, manifest in all_sdds:
        if manifest.plan_bundle_hash == plan_hash:
            return sdd_path
    return None


@beartype
@require(lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0, "Bundle name must be non-empty")
@require(lambda base_path: isinstance(base_path, Path), "Base path must be Path")
@ensure(lambda result: isinstance(result, Path), "Must return Path")
def get_default_sdd_path_for_bundle(bundle_name: str, base_path: Path, format: str = "yaml") -> Path:
    """
    Get default SDD path for a project bundle (for creation).

    Phase 8.5: Uses bundle-specific location: .specfact/projects/<bundle-name>/sdd.yaml

    Args:
        bundle_name: Project bundle name
        base_path: Base repository path
        format: File format ("yaml" or "json")

    Returns:
        Path where SDD should be created (bundle-specific location)
    """
    from specfact_cli.utils.structured_io import StructuredFormat

    structured_format = StructuredFormat.YAML if format.lower() == "yaml" else StructuredFormat.JSON
    return SpecFactStructure.get_bundle_sdd_path(bundle_name, base_path, structured_format)
