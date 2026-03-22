"""
Incremental processing utilities for change detection.

This module provides utilities to check if artifacts need to be regenerated
based on file hash changes, enabling fast incremental imports.
"""

from __future__ import annotations

import contextlib
import os
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, cast

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.plan import Feature


def _collect_source_tracking_yaml_lines(lines: list[str]) -> list[str]:
    in_section = False
    section_lines: list[str] = []
    indent_level = 0
    for line in lines:
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            if in_section:
                section_lines.append(line)
            continue
        current_indent = len(line) - len(stripped)
        if stripped.startswith("source_tracking:"):
            in_section = True
            indent_level = current_indent
            section_lines.append(line)
            continue
        if in_section:
            if current_indent <= indent_level and ":" in stripped and not stripped.startswith("- "):
                break
            section_lines.append(line)
    return section_lines


def _extract_source_tracking_section(
    file_path: Path,
) -> dict[str, Any] | None:
    """
    Extract only the source_tracking YAML section from a feature file without parsing the whole file.

    Args:
        file_path: Path to the feature YAML file

    Returns:
        Parsed source_tracking dict, or None if not found
    """
    from specfact_cli.utils.structured_io import load_structured_file

    try:
        content = file_path.read_text(encoding="utf-8")
        section_lines = _collect_source_tracking_yaml_lines(content.split("\n"))
        if not section_lines:
            return None
        from specfact_cli.utils.structured_io import StructuredFormat, loads_structured_data

        section_data = loads_structured_data("\n".join(section_lines), StructuredFormat.YAML)
        if not isinstance(section_data, dict):
            return None
        return cast(dict[str, Any], section_data).get("source_tracking")
    except Exception:
        try:
            feature_data = load_structured_file(file_path)
            if not isinstance(feature_data, dict):
                return None
            return cast(dict[str, Any], feature_data).get("source_tracking")
        except Exception:
            return None


def _load_features_from_manifest(
    bundle_dir: Path,
    progress_callback: Callable[[int, int, str], None] | None,
) -> list[Feature]:
    """
    Load minimal Feature objects (source_tracking only) from a bundle manifest using parallel I/O.

    Args:
        bundle_dir: Path to the project bundle directory
        progress_callback: Optional progress callback (current, total, message)

    Returns:
        List of minimal Feature objects with source_tracking populated

    Raises:
        Exception: Propagates any loading failure so the caller can fall back
    """
    from specfact_cli.models.plan import Feature
    from specfact_cli.models.project import BundleManifest, FeatureIndex
    from specfact_cli.models.source_tracking import SourceTracking
    from specfact_cli.utils.structured_io import load_structured_file

    manifest_path = bundle_dir / "bundle.manifest.yaml"
    if not manifest_path.exists():
        raise FileNotFoundError("bundle.manifest.yaml not found")
    manifest = BundleManifest.model_validate(load_structured_file(manifest_path))
    num_features = len(manifest.features)
    estimated_total = 1 + num_features + (num_features * 2)
    if progress_callback:
        progress_callback(1, estimated_total, "Loading manifest...")
    features_dir = bundle_dir / "features"
    if not features_dir.exists():
        raise FileNotFoundError("features/ directory not found")

    def _load_one(feature_index: FeatureIndex) -> Feature | None:
        """Load source_tracking-only Feature for a single index entry."""
        feature_path = features_dir / feature_index.file
        if not feature_path.exists():
            return None
        try:
            st_data = _extract_source_tracking_section(feature_path)
            source_tracking = SourceTracking.model_validate(st_data) if st_data else None
            return Feature(
                key=feature_index.key,
                title=feature_index.title or "",
                source_tracking=source_tracking,
                contract=None,
                protocol=None,
            )
        except Exception:
            return Feature(
                key=feature_index.key,
                title=feature_index.title or "",
                source_tracking=None,
                contract=None,
                protocol=None,
            )

    in_test = os.environ.get("TEST_MODE") == "true"
    max_workers = max(1, min(2, num_features)) if in_test else min(os.cpu_count() or 4, 8, max(1, num_features))
    wait_on_shutdown = not in_test
    executor = ThreadPoolExecutor(max_workers=max_workers)
    try:
        future_to_index = {executor.submit(_load_one, fi): fi for fi in manifest.features}
        features = _execute_manifest_feature_loads(future_to_index, progress_callback, estimated_total, num_features)
    except KeyboardInterrupt:
        executor.shutdown(wait=False, cancel_futures=True)
        raise
    finally:
        with contextlib.suppress(RuntimeError):
            executor.shutdown(wait=wait_on_shutdown)
    return features


def _cancel_pending_futures(future_to_task: dict[Future[Any], Any]) -> None:
    for f in future_to_task:
        if not f.done():
            f.cancel()


def _execute_manifest_feature_loads(
    future_to_index: dict[Future[Any], Any],
    progress_callback: Callable[[int, int, str], None] | None,
    estimated_total: int,
    num_features: int,
) -> list[Feature]:
    features: list[Feature] = []
    completed = 0
    for future in as_completed(future_to_index):
        try:
            feat = future.result()
            if feat:
                features.append(feat)
            completed += 1
            if progress_callback:
                progress_callback(1 + completed, estimated_total, f"Loading features... ({completed}/{num_features})")
        except KeyboardInterrupt:
            for f in future_to_index:
                f.cancel()
            raise
    return features


def _parallel_drain_file_check_futures(
    future_to_task: dict[Future[Any], Any],
    progress_callback: Callable[[int, int, str], None] | None,
    num_features_loaded: int,
    actual_total: int,
) -> tuple[bool, bool]:
    """Return (any_file_changed, interrupted)."""
    source_files_changed = False
    interrupted = False
    completed_checks = 0
    total_tasks = len(future_to_task)
    try:
        for future in as_completed(future_to_task):
            try:
                if future.result():
                    source_files_changed = True
                    break
                completed_checks += 1
                if progress_callback and num_features_loaded > 0:
                    progress_callback(
                        1 + num_features_loaded + completed_checks,
                        actual_total,
                        f"Checking files... ({completed_checks}/{total_tasks})",
                    )
            except KeyboardInterrupt:
                interrupted = True
                _cancel_pending_futures(future_to_task)
                break
    except KeyboardInterrupt:
        interrupted = True
        _cancel_pending_futures(future_to_task)
    return source_files_changed, interrupted


def _run_parallel_file_checks(
    check_tasks: list[tuple[Feature, Path, str]],
    progress_callback: Callable[[int, int, str], None] | None,
    num_features_loaded: int,
    actual_total: int,
) -> bool:
    """
    Check all file tasks in parallel and return True if any file has changed.

    Args:
        check_tasks: List of (feature, file_path, file_type) tuples
        progress_callback: Optional progress callback
        num_features_loaded: Number of features already loaded (for progress offset)
        actual_total: Total expected steps (for progress reporting)

    Returns:
        True if any source file has changed or been deleted
    """

    def _check_one(task: tuple[Feature, Path, str]) -> bool:
        feat, file_path, _ = task
        if not file_path.exists():
            return True
        if not feat.source_tracking:
            return True
        return feat.source_tracking.has_changed(file_path)

    in_test = os.environ.get("TEST_MODE") == "true"
    max_workers = max(1, min(2, len(check_tasks))) if in_test else min(os.cpu_count() or 4, 8, len(check_tasks))
    wait_on_shutdown = not in_test
    interrupted = False
    executor = ThreadPoolExecutor(max_workers=max_workers)
    try:
        future_to_task = {executor.submit(_check_one, task): task for task in check_tasks}
        source_files_changed, interrupted = _parallel_drain_file_check_futures(
            future_to_task, progress_callback, num_features_loaded, actual_total
        )
        if interrupted:
            raise KeyboardInterrupt
    except KeyboardInterrupt:
        executor.shutdown(wait=False, cancel_futures=True)
        raise
    finally:
        executor.shutdown(wait=False if interrupted else wait_on_shutdown)
    return source_files_changed


def _build_incremental_check_work(
    features: list[Feature],
    repo: Path,
    bundle_dir: Path,
) -> tuple[list[tuple[Feature, Path, str]], list[tuple[Feature, Path]], bool]:
    """Collect parallel check tasks and contract paths; set source_files_changed if tracking missing."""
    check_tasks: list[tuple[Feature, Path, str]] = []
    contract_checks: list[tuple[Feature, Path]] = []
    source_files_changed = False
    for feature in features:
        if not feature.source_tracking:
            source_files_changed = True
            continue
        for impl_file in feature.source_tracking.implementation_files:
            check_tasks.append((feature, repo / impl_file, "implementation"))
        if feature.contract:
            contract_checks.append((feature, bundle_dir / feature.contract))
    return check_tasks, contract_checks, source_files_changed


def _scan_contract_drift(
    contract_checks: list[tuple[Feature, Path]],
    source_files_changed: bool,
) -> tuple[bool, bool]:
    contracts_exist = True
    contracts_changed = False
    for _feature, contract_path in contract_checks:
        if not contract_path.exists():
            contracts_exist = False
            contracts_changed = True
        elif source_files_changed:
            contracts_changed = True
    return contracts_exist, contracts_changed


def _maybe_mark_all_artifacts_clean(
    result: dict[str, bool],
    source_files_changed: bool,
    contracts_exist: bool,
    contracts_changed: bool,
) -> None:
    if not source_files_changed and contracts_exist and not contracts_changed:
        result["relationships"] = False
        result["contracts"] = False
        result["graph"] = False
        result["enrichment_context"] = False
        result["bundle"] = False


def _incremental_notify_file_check_progress(
    progress_callback: Callable[[int, int, str], None] | None,
    num_features_loaded: int,
    check_tasks: list[tuple[Feature, Path, str]],
    actual_total: int,
) -> None:
    if not progress_callback:
        return
    msg = f"Checking {len(check_tasks)} file(s) for changes..."
    if num_features_loaded > 0:
        progress_callback(1 + num_features_loaded, actual_total, msg)
    elif check_tasks:
        progress_callback(0, actual_total, msg)


@beartype
@require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
@ensure(lambda result: isinstance(result, dict), "Must return dict")
def check_incremental_changes(
    bundle_dir: Path,
    repo: Path,
    features: list[Feature] | None = None,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> dict[str, bool]:
    """
    Check which artifacts need regeneration based on file hash changes.

    Args:
        bundle_dir: Path to project bundle directory
        repo: Path to repository root
        features: Optional list of features to check (if None, loads from bundle)
        progress_callback: Optional callback function(current: int, total: int, message: str) for progress updates

    Returns:
        Dictionary with keys:
        - 'relationships': True if relationships need regeneration
        - 'contracts': True if contracts need regeneration
        - 'graph': True if graph analysis needs regeneration
        - 'enrichment_context': True if enrichment context needs regeneration
        - 'bundle': True if bundle needs saving
    """
    result: dict[str, bool] = {
        "relationships": True,
        "contracts": True,
        "graph": True,
        "enrichment_context": True,
        "bundle": True,
    }

    if not bundle_dir.exists():
        return result

    if features is None:
        try:
            features = _load_features_from_manifest(bundle_dir, progress_callback)
        except Exception:
            return result

    check_tasks, contract_checks, source_files_changed = _build_incremental_check_work(features, repo, bundle_dir)
    num_features_loaded = len(features)

    actual_total = (
        (1 + num_features_loaded + len(check_tasks)) if num_features_loaded > 0 else (len(check_tasks) or 100)
    )

    _incremental_notify_file_check_progress(progress_callback, num_features_loaded, check_tasks, actual_total)

    if check_tasks and not source_files_changed:
        source_files_changed = _run_parallel_file_checks(
            check_tasks, progress_callback, num_features_loaded, actual_total
        )

    contracts_exist, contracts_changed = _scan_contract_drift(contract_checks, source_files_changed)

    _maybe_mark_all_artifacts_clean(result, source_files_changed, contracts_exist, contracts_changed)

    _apply_enrichment_and_contracts_flags(bundle_dir, source_files_changed, contracts_changed, result)

    _emit_incremental_progress_complete(progress_callback, num_features_loaded, actual_total, check_tasks)

    return result


def _apply_enrichment_and_contracts_flags(
    bundle_dir: Path,
    source_files_changed: bool,
    contracts_changed: bool,
    result: dict[str, bool],
) -> None:
    enrichment_context_path = bundle_dir / "enrichment_context.md"
    if enrichment_context_path.exists() and not source_files_changed:
        result["enrichment_context"] = False

    contracts_dir = bundle_dir / "contracts"
    if (
        contracts_dir.exists()
        and contracts_dir.is_dir()
        and list(contracts_dir.glob("*.openapi.yaml"))
        and not contracts_changed
    ):
        result["contracts"] = False


def _emit_incremental_progress_complete(
    progress_callback: Callable[[int, int, str], None] | None,
    num_features_loaded: int,
    actual_total: int,
    check_tasks: list[tuple[Feature, Path, str]],
) -> None:
    if not progress_callback:
        return
    if num_features_loaded > 0 and actual_total > 0:
        progress_callback(actual_total, actual_total, "Change check complete")
    elif check_tasks:
        progress_callback(len(check_tasks), len(check_tasks), "Change check complete")
    else:
        progress_callback(1, 1, "Change check complete")


@beartype
@require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
@require(lambda repo: isinstance(repo, Path), "Repository path must be Path")
@ensure(lambda result: isinstance(result, dict), "Must return dict")
def get_changed_files(bundle_dir: Path, repo: Path, features: list[Feature]) -> dict[str, list[str]]:
    """
    Get list of changed files per feature.

    Args:
        bundle_dir: Path to project bundle directory
        repo: Path to repository root
        features: List of features to check

    Returns:
        Dictionary mapping feature_key -> list of changed file paths
    """
    changed_files: dict[str, list[str]] = {}

    for feature in features:
        if not feature.source_tracking:
            continue

        feature_changes: list[str] = []

        # Check implementation files
        for impl_file in feature.source_tracking.implementation_files:
            file_path = repo / impl_file
            if file_path.exists():
                if feature.source_tracking.has_changed(file_path):
                    feature_changes.append(impl_file)
            else:
                # File deleted
                feature_changes.append(f"{impl_file} (deleted)")

        # Check test files
        for test_file in feature.source_tracking.test_files:
            file_path = repo / test_file
            if file_path.exists():
                if feature.source_tracking.has_changed(file_path):
                    feature_changes.append(test_file)
            else:
                # File deleted
                feature_changes.append(f"{test_file} (deleted)")

        if feature_changes:
            changed_files[feature.key] = feature_changes

    return changed_files
