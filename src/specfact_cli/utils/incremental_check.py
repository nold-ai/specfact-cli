"""
Incremental processing utilities for change detection.

This module provides utilities to check if artifacts need to be regenerated
based on file hash changes, enabling fast incremental imports.
"""

from __future__ import annotations

import contextlib
import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.plan import Feature


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
    result = {
        "relationships": True,
        "contracts": True,
        "graph": True,
        "enrichment_context": True,
        "bundle": True,
    }

    # If bundle doesn't exist, everything needs to be generated
    if not bundle_dir.exists():
        return result

    # Load only source_tracking sections from feature files (optimization: don't load full features)
    # This avoids loading and validating entire Feature models just to check file hashes
    if features is None:
        try:
            from specfact_cli.models.plan import Feature
            from specfact_cli.models.project import BundleManifest, FeatureIndex
            from specfact_cli.models.source_tracking import SourceTracking
            from specfact_cli.utils.structured_io import load_structured_file

            # Load manifest first (fast, single file)
            manifest_path = bundle_dir / "bundle.manifest.yaml"
            if not manifest_path.exists():
                return result

            manifest_data = load_structured_file(manifest_path)
            manifest = BundleManifest.model_validate(manifest_data)

            # Calculate estimated total for progress tracking (will be refined when we know actual file count)
            num_features = len(manifest.features)
            estimated_total = 1 + num_features + (num_features * 2)  # ~2 files per feature average

            if progress_callback:
                progress_callback(1, estimated_total, "Loading manifest...")

            # Load only source_tracking sections from feature files in parallel
            features_dir = bundle_dir / "features"
            if not features_dir.exists():
                return result

            def extract_source_tracking_section(file_path: Path) -> dict[str, Any] | None:
                """Extract only source_tracking section from YAML file without parsing entire file."""
                try:
                    content = file_path.read_text(encoding="utf-8")
                    # Find source_tracking section using text parsing (much faster than full YAML parse)
                    lines = content.split("\n")
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

                        # Check if this is the source_tracking key
                        if stripped.startswith("source_tracking:"):
                            in_section = True
                            indent_level = current_indent
                            section_lines.append(line)
                            continue

                        # If we're in the section, check if we've hit the next top-level key
                        if in_section:
                            if current_indent <= indent_level and ":" in stripped and not stripped.startswith("- "):
                                # Hit next top-level key, stop
                                break
                            section_lines.append(line)

                    if not section_lines:
                        return None

                    # Parse only the extracted section
                    section_text = "\n".join(section_lines)
                    from specfact_cli.utils.structured_io import StructuredFormat, loads_structured_data

                    section_data = loads_structured_data(section_text, StructuredFormat.YAML)
                    return section_data.get("source_tracking") if isinstance(section_data, dict) else None
                except Exception:
                    # Fallback to full parse if text extraction fails
                    try:
                        feature_data = load_structured_file(file_path)
                        return feature_data.get("source_tracking") if isinstance(feature_data, dict) else None
                    except Exception:
                        return None

            def load_feature_source_tracking(feature_index: FeatureIndex) -> Feature | None:
                """Load only source_tracking section from a feature file (optimized - no full YAML parse)."""
                feature_path = features_dir / feature_index.file
                if not feature_path.exists():
                    return None
                try:
                    # Extract only source_tracking section (fast text-based extraction)
                    source_tracking_data = extract_source_tracking_section(feature_path)

                    if source_tracking_data:
                        source_tracking = SourceTracking.model_validate(source_tracking_data)
                        # Create minimal Feature object with just what we need
                        return Feature(
                            key=feature_index.key,
                            title=feature_index.title or "",
                            source_tracking=source_tracking,
                            contract=None,  # Don't need contract for hash checking
                            protocol=None,  # Don't need protocol for hash checking
                        )
                    # No source_tracking means we should regenerate
                    return Feature(
                        key=feature_index.key,
                        title=feature_index.title or "",
                        source_tracking=None,
                        contract=None,
                        protocol=None,
                    )
                except Exception:
                    # If we can't load, assume it changed
                    return Feature(
                        key=feature_index.key,
                        title=feature_index.title or "",
                        source_tracking=None,
                        contract=None,
                        protocol=None,
                    )

            # Load source_tracking sections in parallel
            # In test mode, use fewer workers to avoid resource contention
            if os.environ.get("TEST_MODE") == "true":
                max_workers = max(1, min(2, len(manifest.features)))  # Max 2 workers in test mode
            else:
                max_workers = min(os.cpu_count() or 4, 8, len(manifest.features))
            features = []
            executor = ThreadPoolExecutor(max_workers=max_workers)
            # In test mode, use wait=False to avoid hanging on shutdown
            wait_on_shutdown = os.environ.get("TEST_MODE") != "true"
            try:
                future_to_index = {executor.submit(load_feature_source_tracking, fi): fi for fi in manifest.features}
                completed_features = 0
                for future in as_completed(future_to_index):
                    try:
                        feature = future.result()
                        if feature:
                            features.append(feature)
                        completed_features += 1
                        if progress_callback:
                            # Use estimated_total for now (will be refined when we know actual file count)
                            progress_callback(
                                1 + completed_features,
                                estimated_total,
                                f"Loading features... ({completed_features}/{num_features})",
                            )
                    except KeyboardInterrupt:
                        # Cancel remaining tasks and re-raise
                        for f in future_to_index:
                            f.cancel()
                        raise
            except KeyboardInterrupt:
                # Gracefully shutdown executor on interrupt (cancel pending tasks)
                executor.shutdown(wait=False, cancel_futures=True)
                raise
            finally:
                # Ensure executor is properly shutdown (shutdown() is safe to call multiple times)
                with contextlib.suppress(RuntimeError):
                    executor.shutdown(wait=wait_on_shutdown)

        except Exception:
            # Bundle exists but can't be loaded - regenerate everything
            return result

    # Check if any source files changed (parallelized for performance)
    source_files_changed = False
    contracts_exist = True
    contracts_changed = False

    # Collect all file check tasks for parallel processing
    check_tasks: list[tuple[Feature, Path, str]] = []  # (feature, file_path, file_type)
    contract_checks: list[tuple[Feature, Path]] = []  # (feature, contract_path)

    num_features_loaded = len(features) if features else 0

    # Collect all file check tasks first
    for feature in features:
        if not feature.source_tracking:
            source_files_changed = True
            continue

        # Collect implementation files to check
        for impl_file in feature.source_tracking.implementation_files:
            file_path = repo / impl_file
            check_tasks.append((feature, file_path, "implementation"))

        # Collect contract checks
        if feature.contract:
            contract_path = bundle_dir / feature.contract
            contract_checks.append((feature, contract_path))

    # Calculate actual total for progress tracking
    # If we loaded features from manifest, we already counted manifest (1) + features (num_features_loaded)
    # If features were passed directly, we need to account for that differently
    if num_features_loaded > 0:
        # Features were loaded from manifest, so we already counted: manifest (1) + features loaded
        actual_total = 1 + num_features_loaded + len(check_tasks)
    else:
        # Features were passed directly, estimate total
        actual_total = len(check_tasks) if check_tasks else 100

    # Update progress before starting file checks (use actual_total, which may be more accurate than estimated_total)
    if progress_callback and num_features_loaded > 0:
        # Update to actual total (this will refine the estimate based on real file count)
        # This is important: actual_total may be different from estimated_total
        progress_callback(1 + num_features_loaded, actual_total, f"Checking {len(check_tasks)} file(s) for changes...")
    elif progress_callback and not num_features_loaded and check_tasks:
        # Features passed directly, start progress tracking
        progress_callback(0, actual_total, f"Checking {len(check_tasks)} file(s) for changes...")

    # Check files in parallel (early exit if any change detected)
    if check_tasks:
        # In test mode, use fewer workers to avoid resource contention
        if os.environ.get("TEST_MODE") == "true":
            max_workers = max(1, min(2, len(check_tasks)))  # Max 2 workers in test mode
        else:
            max_workers = min(os.cpu_count() or 4, 8, len(check_tasks))  # Cap at 8 workers

        def check_file_change(task: tuple[Feature, Path, str]) -> bool:
            """Check if a single file has changed (thread-safe)."""
            feature, file_path, _file_type = task
            if not file_path.exists():
                return True  # File deleted
            if not feature.source_tracking:
                return True  # No tracking means we should regenerate
            return feature.source_tracking.has_changed(file_path)

        executor = ThreadPoolExecutor(max_workers=max_workers)
        interrupted = False
        # In test mode, use wait=False to avoid hanging on shutdown
        wait_on_shutdown = os.environ.get("TEST_MODE") != "true"
        try:
            # Submit all tasks
            future_to_task = {executor.submit(check_file_change, task): task for task in check_tasks}

            # Check results as they complete (early exit on first change)
            completed_checks = 0
            try:
                for future in as_completed(future_to_task):
                    try:
                        if future.result():
                            source_files_changed = True
                            # Cancel remaining tasks (they'll complete but we won't wait)
                            break
                        completed_checks += 1
                        # Update progress as file checks complete
                        if progress_callback and num_features_loaded > 0:
                            current_progress = 1 + num_features_loaded + completed_checks
                            progress_callback(
                                current_progress,
                                actual_total,
                                f"Checking files... ({completed_checks}/{len(check_tasks)})",
                            )
                    except KeyboardInterrupt:
                        interrupted = True
                        for f in future_to_task:
                            if not f.done():
                                f.cancel()
                        break
            except KeyboardInterrupt:
                interrupted = True
                for f in future_to_task:
                    if not f.done():
                        f.cancel()
            if interrupted:
                raise KeyboardInterrupt
        except KeyboardInterrupt:
            interrupted = True
            executor.shutdown(wait=False, cancel_futures=True)
            raise
        finally:
            # Ensure executor is properly shutdown (safe to call multiple times)
            if not interrupted:
                executor.shutdown(wait=wait_on_shutdown)
            else:
                executor.shutdown(wait=False)

    # Check contracts (sequential, fast operation)
    for _feature, contract_path in contract_checks:
        if not contract_path.exists():
            contracts_exist = False
            contracts_changed = True
        elif source_files_changed:
            # If source changed, contract might be outdated
            contracts_changed = True

    # If no source files changed and contracts exist, we can skip some processing
    if not source_files_changed and contracts_exist and not contracts_changed:
        result["relationships"] = False
        result["contracts"] = False
        result["graph"] = False
        result["enrichment_context"] = False
        result["bundle"] = False

    # Check if enrichment context file exists
    enrichment_context_path = bundle_dir / "enrichment_context.md"
    if enrichment_context_path.exists() and not source_files_changed:
        result["enrichment_context"] = False

    # Check if contracts directory exists and has files
    contracts_dir = bundle_dir / "contracts"
    if contracts_dir.exists() and contracts_dir.is_dir():
        contract_files = list(contracts_dir.glob("*.openapi.yaml"))
        if contract_files and not contracts_changed:
            result["contracts"] = False

    # Final progress update (use already calculated actual_total)
    if progress_callback:
        if num_features_loaded > 0 and actual_total > 0:
            # Features loaded from manifest: use calculated total
            progress_callback(actual_total, actual_total, "Change check complete")
        elif check_tasks:
            # Features passed directly: use check_tasks count
            progress_callback(len(check_tasks), len(check_tasks), "Change check complete")
        else:
            # No files to check, just mark complete
            progress_callback(1, 1, "Change check complete")

    return result


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
