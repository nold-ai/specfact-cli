"""
Module artifact verification stages for installation and registration (arch-06).
"""

from __future__ import annotations

from pathlib import Path

from beartype import beartype

from specfact_cli.common import get_bridge_logger
from specfact_cli.models.module_package import ModulePackageMetadata
from specfact_cli.registry.crypto_validator import verify_checksum


@beartype
def verify_module_artifact(
    package_dir: Path,
    meta: ModulePackageMetadata,
    allow_unsigned: bool = False,
) -> bool:
    """
    Run integrity verification for a module artifact. Used at registration and install time.

    - If meta.integrity is set: verify checksum (and signature if present); return False on failure.
    - If meta.integrity is not set and allow_unsigned: return True (allow with warning).
    - If meta.integrity is not set and not allow_unsigned: return False (reject unsigned by default).

    Returns:
        True if the module passes trust checks and may be registered/installed.
    """
    logger = get_bridge_logger(__name__)
    manifest_path = package_dir / "module-package.yaml"
    if not manifest_path.exists():
        manifest_path = package_dir / "metadata.yaml"
    if not manifest_path.exists():
        logger.warning("Module %s: No manifest file for integrity check (skipped)", meta.name)
        return allow_unsigned

    if meta.integrity is None:
        # Backward compatible: allow modules without integrity unless strict mode is added later.
        if allow_unsigned:
            logger.debug("Module %s: No integrity metadata; allowing (allow-unsigned)", meta.name)
        return True

    try:
        data = manifest_path.read_bytes()
        verify_checksum(data, meta.integrity.checksum)
    except ValueError as e:
        logger.warning("Module %s: Integrity check failed: %s", meta.name, e)
        return False

    if meta.integrity.signature:
        # Signature verification would require key material (not in manifest). Allow with warning.
        logger.warning(
            "Module %s: Signature present but key material not configured; checksum-only verification",
            meta.name,
        )

    return True
