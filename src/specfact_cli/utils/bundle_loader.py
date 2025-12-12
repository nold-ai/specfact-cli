"""
Bundle loader utilities for format detection and loading.

This module provides format detection, validation, and loading functions
for modular project bundle formats.
"""

from __future__ import annotations

import hashlib
import tempfile
from collections.abc import Callable
from pathlib import Path

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.project import BundleFormat, ProjectBundle
from specfact_cli.utils.structured_io import load_structured_file


class BundleFormatError(Exception):
    """Raised when bundle format cannot be determined or is unsupported."""


@beartype
@require(lambda path: isinstance(path, Path), "Path must be Path")
@ensure(
    lambda result: isinstance(result, tuple) and len(result) == 2,
    "Must return (BundleFormat, Optional[str]) tuple",
)
def detect_bundle_format(path: Path) -> tuple[BundleFormat, str | None]:
    """
    Detect if bundle is monolithic or modular.

    Args:
        path: Path to bundle (file or directory)

    Returns:
        Tuple of (format, error_message)
        - format: Detected format type
        - error_message: None if successful, error message if detection failed

    Raises:
        BundleFormatError: If path does not exist or is invalid

    Examples:
        >>> format, error = detect_bundle_format(Path('.specfact/plans/main.bundle.yaml'))
        >>> format
        <BundleFormat.MONOLITHIC: 'monolithic'>

        >>> format, error = detect_bundle_format(Path('.specfact/projects/legacy-api'))
        >>> format
        <BundleFormat.MODULAR: 'modular'>
    """
    if not path.exists():
        return BundleFormat.UNKNOWN, f"Path does not exist: {path}"

    if path.is_file() and path.suffix in [".yaml", ".yml", ".json"]:
        # Check if it's a monolithic bundle
        try:
            data = load_structured_file(path)
            if isinstance(data, dict):
                # Monolithic bundle has all aspects in one file
                if "idea" in data and "product" in data and "features" in data:
                    return BundleFormat.MONOLITHIC, None
                # Could be a bundle manifest (modular) - check for dual versioning
                versions = data.get("versions", {})
                if isinstance(versions, dict) and "schema" in versions and "bundle" in data:
                    return BundleFormat.MODULAR, None
        except Exception as e:
            return BundleFormat.UNKNOWN, f"Failed to parse file: {e}"
    elif path.is_dir():
        # Check for modular project bundle structure
        manifest_path = path / "bundle.manifest.yaml"
        if manifest_path.exists():
            return BundleFormat.MODULAR, None
        # Check if directory has partial bundle files (incomplete save)
        # If it has features/ or contracts/ but no manifest, it's likely an incomplete modular bundle
        if (path / "features").exists() or (path / "contracts").exists():
            return (
                BundleFormat.UNKNOWN,
                "Incomplete bundle directory (missing bundle.manifest.yaml). This may be from a failed save. Consider removing the directory and re-running import.",
            )
        # Check for legacy plans directory
        if path.name == "plans" and any(f.suffix in [".yaml", ".yml", ".json"] for f in path.glob("*.bundle.*")):
            return BundleFormat.MONOLITHIC, None

    return BundleFormat.UNKNOWN, "Could not determine bundle format"


@beartype
@require(lambda path: isinstance(path, Path), "Path must be Path")
@require(lambda path: path.exists(), "Path must exist")
@ensure(lambda result: isinstance(result, BundleFormat), "Must return BundleFormat")
def validate_bundle_format(path: Path) -> BundleFormat:
    """
    Validate bundle format and raise error if unsupported.

    Args:
        path: Path to bundle (file or directory)

    Returns:
        Detected bundle format

    Raises:
        BundleFormatError: If format cannot be determined or is unsupported
        FileNotFoundError: If path does not exist

    Examples:
        >>> format = validate_bundle_format(Path('.specfact/projects/legacy-api'))
        >>> format
        <BundleFormat.MODULAR: 'modular'>
    """
    if not path.exists():
        raise FileNotFoundError(f"Bundle path does not exist: {path}")

    format_type, error_message = detect_bundle_format(path)

    if format_type == BundleFormat.UNKNOWN:
        error_msg = f"Cannot determine bundle format for: {path}"
        if error_message:
            error_msg += f"\n  Reason: {error_message}"
        error_msg += "\n\nSupported formats:"
        error_msg += "\n  - Monolithic: Single file with 'idea', 'product', 'features' keys"
        error_msg += "\n  - Modular: Directory with 'bundle.manifest.yaml' file"
        error_msg += "\n\nTo migrate from monolithic to modular format, run:"
        error_msg += "\n  specfact migrate bundle <old-file> <bundle-name>"
        raise BundleFormatError(error_msg)

    return format_type


@beartype
@require(lambda path: isinstance(path, Path), "Path must be Path")
@require(lambda path: path.exists(), "Path must exist")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def is_monolithic_bundle(path: Path) -> bool:
    """
    Check if path points to a monolithic bundle.

    Args:
        path: Path to bundle (file or directory)

    Returns:
        True if monolithic bundle, False otherwise

    Examples:
        >>> is_monolithic_bundle(Path('.specfact/plans/main.bundle.yaml'))
        True
    """
    format_type, _ = detect_bundle_format(path)
    return format_type == BundleFormat.MONOLITHIC


@beartype
@require(lambda path: isinstance(path, Path), "Path must be Path")
@require(lambda path: path.exists(), "Path must exist")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def is_modular_bundle(path: Path) -> bool:
    """
    Check if path points to a modular bundle.

    Args:
        path: Path to bundle (file or directory)

    Returns:
        True if modular bundle, False otherwise

    Examples:
        >>> is_modular_bundle(Path('.specfact/projects/legacy-api'))
        True
    """
    format_type, _ = detect_bundle_format(path)
    return format_type == BundleFormat.MODULAR


class BundleLoadError(Exception):
    """Raised when bundle cannot be loaded."""


class BundleSaveError(Exception):
    """Raised when bundle cannot be saved."""


@beartype
@require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
@require(lambda bundle_dir: bundle_dir.exists(), "Bundle directory must exist")
@ensure(lambda result: isinstance(result, ProjectBundle), "Must return ProjectBundle")
def load_project_bundle(
    bundle_dir: Path,
    validate_hashes: bool = False,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> ProjectBundle:
    """
    Load modular project bundle from directory structure.

    This function wraps ProjectBundle.load_from_directory() with format validation
    and optional hash consistency checking.

    Args:
        bundle_dir: Path to project bundle directory (e.g., .specfact/projects/legacy-api/)
        validate_hashes: If True, validate file checksums against manifest

    Returns:
        ProjectBundle instance loaded from directory

    Raises:
        BundleFormatError: If bundle format is not modular
        BundleLoadError: If bundle cannot be loaded or hash validation fails
        FileNotFoundError: If bundle directory or manifest is missing

    Examples:
        >>> bundle = load_project_bundle(Path('.specfact/projects/legacy-api'))
        >>> bundle.bundle_name
        'legacy-api'
    """
    # Validate format
    format_type = validate_bundle_format(bundle_dir)
    if format_type != BundleFormat.MODULAR:
        raise BundleFormatError(f"Expected modular bundle format, got: {format_type}")

    try:
        # Load bundle using ProjectBundle method with progress callback
        bundle = ProjectBundle.load_from_directory(bundle_dir, progress_callback=progress_callback)

        # Validate hashes if requested
        if validate_hashes:
            _validate_bundle_hashes(bundle, bundle_dir)

        return bundle
    except FileNotFoundError as e:
        raise BundleLoadError(f"Bundle file not found: {e}") from e
    except ValueError as e:
        raise BundleLoadError(f"Invalid bundle structure: {e}") from e
    except Exception as e:
        raise BundleLoadError(f"Failed to load bundle: {e}") from e


@beartype
@require(lambda bundle: isinstance(bundle, ProjectBundle), "Bundle must be ProjectBundle")
@require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
@ensure(lambda result: result is None, "Must return None")
def save_project_bundle(
    bundle: ProjectBundle,
    bundle_dir: Path,
    atomic: bool = True,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> None:
    """
    Save modular project bundle to directory structure.

    This function wraps ProjectBundle.save_to_directory() with atomic write support
    and automatic hash computation.

    Args:
        bundle: ProjectBundle instance to save
        bundle_dir: Path to project bundle directory (e.g., .specfact/projects/legacy-api/)
        atomic: If True, use atomic writes (write to temp, then rename)

    Raises:
        BundleSaveError: If bundle cannot be saved
        ValueError: If bundle structure is invalid

    Examples:
        >>> bundle = ProjectBundle(...)
        >>> save_project_bundle(bundle, Path('.specfact/projects/legacy-api'))
    """
    try:
        if atomic:
            # Atomic write: write to temp directory, then rename
            # IMPORTANT: Preserve non-bundle directories (contracts, protocols, reports, logs, etc.)
            import shutil

            # Directories/files to preserve during atomic save
            # Phase 8.5: Include bundle-specific reports and logs directories
            preserve_items = ["contracts", "protocols", "reports", "logs", "enrichment_context.md"]

            # Backup directories/files to preserve (use separate temp dir that persists)
            preserved_data: dict[str, Path] = {}
            backup_temp_dir = None
            if bundle_dir.exists():
                backup_temp_dir = tempfile.mkdtemp()
                for preserve_name in preserve_items:
                    preserve_path = bundle_dir / preserve_name
                    if preserve_path.exists():
                        backup_path = Path(backup_temp_dir) / preserve_name
                        if preserve_path.is_dir():
                            shutil.copytree(preserve_path, backup_path, dirs_exist_ok=True)
                        else:
                            backup_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(preserve_path, backup_path)
                        preserved_data[preserve_name] = backup_path

            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir) / bundle_dir.name
                    bundle.save_to_directory(temp_path, progress_callback=progress_callback)

                    # Restore preserved directories/files to temp before moving
                    for preserve_name, backup_path in preserved_data.items():
                        restore_path = temp_path / preserve_name
                        if backup_path.exists():
                            if backup_path.is_dir():
                                shutil.copytree(backup_path, restore_path, dirs_exist_ok=True)
                            else:
                                restore_path.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(backup_path, restore_path)

                    # Ensure target directory parent exists
                    bundle_dir.parent.mkdir(parents=True, exist_ok=True)

                    # Remove existing directory if it exists
                    if bundle_dir.exists():
                        shutil.rmtree(bundle_dir)

                    # Move temp directory to target
                    temp_path.rename(bundle_dir)
            finally:
                # Clean up backup temp directory
                if backup_temp_dir and Path(backup_temp_dir).exists():
                    shutil.rmtree(backup_temp_dir, ignore_errors=True)
        else:
            # Direct write
            bundle.save_to_directory(bundle_dir, progress_callback=progress_callback)
    except Exception as e:
        error_msg = "Failed to save bundle"
        if str(e):
            error_msg += f": {e}"
        raise BundleSaveError(error_msg) from e


@beartype
@require(lambda bundle: isinstance(bundle, ProjectBundle), "Bundle must be ProjectBundle")
@require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
@require(lambda bundle_dir: bundle_dir.exists(), "Bundle directory must exist")
@ensure(lambda result: result is None, "Must return None")
def _validate_bundle_hashes(bundle: ProjectBundle, bundle_dir: Path) -> None:
    """
    Validate file checksums against manifest.

    Args:
        bundle: ProjectBundle instance
        bundle_dir: Path to bundle directory

    Raises:
        BundleLoadError: If hash validation fails
    """
    manifest = bundle.manifest
    checksums = manifest.checksums

    if checksums.algorithm != "sha256":
        raise BundleLoadError(f"Unsupported checksum algorithm: {checksums.algorithm}")

    errors: list[str] = []

    for file_path_str, expected_hash in checksums.files.items():
        file_path = bundle_dir / file_path_str

        if not file_path.exists():
            errors.append(f"File in manifest but missing: {file_path_str}")
            continue

        # Compute actual hash
        actual_hash = _compute_file_hash(file_path)

        if actual_hash != expected_hash:
            errors.append(
                f"Hash mismatch for {file_path_str}: expected {expected_hash[:8]}..., got {actual_hash[:8]}..."
            )

    if errors:
        error_msg = "Hash validation failed:\n  " + "\n  ".join(errors)
        raise BundleLoadError(error_msg)


@beartype
@require(lambda file_path: isinstance(file_path, Path), "File path must be Path")
@require(lambda file_path: file_path.exists(), "File must exist")
@ensure(lambda result: isinstance(result, str) and len(result) == 64, "Must return SHA256 hex digest")
def _compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA256 hash of a file.

    Args:
        file_path: Path to file

    Returns:
        SHA256 hex digest
    """
    hash_obj = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()
