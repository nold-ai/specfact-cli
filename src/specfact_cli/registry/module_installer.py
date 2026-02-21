"""Module artifact verification and marketplace installation workflows."""

from __future__ import annotations

import shutil
import tarfile
import tempfile
from pathlib import Path

import yaml
from beartype import beartype
from icontract import ensure, require
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from specfact_cli import __version__ as cli_version
from specfact_cli.common import get_bridge_logger
from specfact_cli.models.module_package import ModulePackageMetadata
from specfact_cli.registry.crypto_validator import verify_checksum
from specfact_cli.registry.marketplace_client import download_module


MARKETPLACE_MODULES_ROOT = Path.home() / ".specfact" / "marketplace-modules"


@beartype
def _validate_archive_members(members: list[tarfile.TarInfo], extract_root: Path) -> None:
    """Reject tar members that would escape the intended extraction directory."""
    extract_root_resolved = extract_root.resolve()
    for member in members:
        member_path = (extract_root / member.name).resolve()
        if member_path == extract_root_resolved:
            continue
        if extract_root_resolved not in member_path.parents:
            raise ValueError(f"Downloaded module archive contains unsafe archive path: {member.name}")


@beartype
def verify_module_artifact(
    package_dir: Path,
    meta: ModulePackageMetadata,
    allow_unsigned: bool = False,
) -> bool:
    """Run integrity verification for a module artifact."""
    logger = get_bridge_logger(__name__)
    manifest_path = package_dir / "module-package.yaml"
    if not manifest_path.exists():
        manifest_path = package_dir / "metadata.yaml"
    if not manifest_path.exists():
        logger.warning("Module %s: No manifest file for integrity check (skipped)", meta.name)
        return allow_unsigned

    if meta.integrity is None:
        if allow_unsigned:
            logger.debug("Module %s: No integrity metadata; allowing (allow-unsigned)", meta.name)
        return True

    try:
        data = manifest_path.read_bytes()
        verify_checksum(data, meta.integrity.checksum)
    except ValueError as exc:
        logger.warning("Module %s: Integrity check failed: %s", meta.name, exc)
        return False

    if meta.integrity.signature:
        logger.warning(
            "Module %s: Signature present but key material not configured; checksum-only verification",
            meta.name,
        )

    return True


@beartype
@require(lambda module_id: "/" in module_id and len(module_id.split("/")) == 2, "module_id must be namespace/name")
@ensure(lambda result: result.exists(), "Installed module path must exist")
def install_module(
    module_id: str,
    *,
    version: str | None = None,
    reinstall: bool = False,
    install_root: Path | None = None,
) -> Path:
    """Install a marketplace module from tarball into marketplace modules root."""
    logger = get_bridge_logger(__name__)
    target_root = install_root or MARKETPLACE_MODULES_ROOT
    target_root.mkdir(parents=True, exist_ok=True)

    _namespace, module_name = module_id.split("/", 1)
    final_path = target_root / module_name
    manifest_path = final_path / "module-package.yaml"

    if manifest_path.exists() and not reinstall:
        logger.info("Module already installed (%s)", module_name)
        return final_path

    archive_path = download_module(module_id, version=version)

    with tempfile.TemporaryDirectory(prefix="specfact-module-install-") as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        extract_root = tmp_dir_path / "extract"
        extract_root.mkdir(parents=True, exist_ok=True)

        with tarfile.open(archive_path, "r:gz") as archive:
            members = archive.getmembers()
            _validate_archive_members(members, extract_root)
            archive.extractall(path=extract_root, members=members)

        candidate_dirs = [p for p in extract_root.rglob("module-package.yaml") if p.is_file()]
        if not candidate_dirs:
            raise ValueError("Downloaded module archive does not contain module-package.yaml")

        extracted_manifest = candidate_dirs[0]
        extracted_module_dir = extracted_manifest.parent

        metadata = yaml.safe_load(extracted_manifest.read_text(encoding="utf-8"))
        if not isinstance(metadata, dict):
            raise ValueError("Invalid module manifest format")

        compatibility = str(metadata.get("core_compatibility", "")).strip()
        if compatibility and Version(cli_version) not in SpecifierSet(compatibility):
            raise ValueError("Module is incompatible with current SpecFact CLI version")

        staged_path = target_root / f".{module_name}.tmp-install"
        if staged_path.exists():
            shutil.rmtree(staged_path)
        shutil.copytree(extracted_module_dir, staged_path)

        try:
            if final_path.exists():
                shutil.rmtree(final_path)
            staged_path.replace(final_path)
        except Exception:
            if staged_path.exists():
                shutil.rmtree(staged_path)
            raise

    logger.info("Installed marketplace module '%s' to '%s'", module_id, final_path)
    return final_path


@beartype
@require(lambda module_name: module_name.strip() != "", "module_name must be non-empty")
def uninstall_module(
    module_name: str,
    *,
    install_root: Path | None = None,
    source_map: dict[str, str] | None = None,
) -> None:
    """Uninstall a marketplace module from the local marketplace root."""
    logger = get_bridge_logger(__name__)
    target_root = install_root or MARKETPLACE_MODULES_ROOT

    if source_map is None:
        from specfact_cli.registry.module_discovery import discover_all_modules

        source_map = {entry.metadata.name: entry.source for entry in discover_all_modules()}

    source = source_map.get(module_name)
    if source == "builtin":
        raise ValueError("Cannot uninstall built-in module")
    if source != "marketplace":
        raise ValueError(f"Cannot uninstall module from source '{source or 'unknown'}'")

    module_path = target_root / module_name
    if module_path.exists():
        shutil.rmtree(module_path)
        logger.info("Uninstalled marketplace module '%s'", module_name)
