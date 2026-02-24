"""Module artifact verification, user-root bootstrap, and installation workflows."""

from __future__ import annotations

import hashlib
import os
import shutil
import tarfile
import tempfile
from functools import lru_cache
from pathlib import Path

import yaml
from beartype import beartype
from icontract import ensure, require
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from specfact_cli import __version__ as cli_version
from specfact_cli.common import get_bridge_logger
from specfact_cli.models.module_package import ModulePackageMetadata
from specfact_cli.registry.crypto_validator import verify_checksum, verify_signature
from specfact_cli.registry.marketplace_client import download_module
from specfact_cli.registry.module_security import assert_module_allowed, ensure_publisher_trusted


USER_MODULES_ROOT = Path.home() / ".specfact" / "modules"
MARKETPLACE_MODULES_ROOT = Path.home() / ".specfact" / "marketplace-modules"
_IGNORED_MODULE_DIR_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "logs"}
_IGNORED_MODULE_FILE_SUFFIXES = {".pyc", ".pyo"}


@beartype
def _bundled_public_key_path() -> Path:
    """Resolve default bundled public key path for module signature verification.

    Resolution order:
    1. Repository source path (`./resources/keys/...`) for local/dev runs.
    2. Installed package path (`specfact_cli/resources/keys/...`) for wheel installs.
    """
    key_name = "module-signing-public.pem"
    candidates = [
        Path(__file__).resolve().parents[3] / "resources" / "keys" / key_name,
        Path(__file__).resolve().parents[1] / "resources" / "keys" / key_name,
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


@beartype
def _load_public_key_pem(public_key_pem: str | None = None) -> str:
    """Resolve public key PEM from explicit arg, env var, or bundled key file."""
    explicit = (public_key_pem or "").strip()
    if explicit:
        return explicit
    env_value = os.environ.get("SPECFACT_MODULE_PUBLIC_KEY_PEM", "").strip()
    if env_value:
        return env_value
    key_path = _bundled_public_key_path()
    if key_path.exists():
        return key_path.read_text(encoding="utf-8").strip()
    return ""


@beartype
def _get_bundled_module_sources() -> dict[str, Path]:
    """Return bundled module source directories keyed by module name."""
    from specfact_cli.registry.module_packages import discover_package_metadata

    source_roots: list[Path] = []
    package_modules_root = Path(__file__).resolve().parents[1] / "resources" / "modules"
    if package_modules_root.exists():
        source_roots.append(package_modules_root)
    workspace_modules_root = Path(__file__).resolve().parents[3] / "modules"
    if workspace_modules_root.exists():
        source_roots.append(workspace_modules_root)

    sources: dict[str, Path] = {}
    for source_root in source_roots:
        for module_dir, metadata in discover_package_metadata(source_root):
            sources.setdefault(metadata.name, module_dir)
    return sources


@beartype
@ensure(lambda result: isinstance(result, dict), "Bundled module metadata mapping must be a dict")
def get_bundled_module_metadata() -> dict[str, ModulePackageMetadata]:
    """Return bundled module metadata keyed by module name."""
    from specfact_cli.registry.module_packages import discover_package_metadata

    metadata_by_name: dict[str, ModulePackageMetadata] = {}
    for source_root in {path.parent for path in _get_bundled_module_sources().values()}:
        for _module_dir, metadata in discover_package_metadata(source_root):
            metadata_by_name.setdefault(metadata.name, metadata)
    return metadata_by_name


@beartype
def _canonical_manifest_payload(manifest_path: Path) -> bytes:
    """Build deterministic manifest payload for checksum/signature verification."""
    parsed = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("Invalid module manifest format")
    parsed.pop("integrity", None)
    return yaml.safe_dump(parsed, sort_keys=True, allow_unicode=False).encode("utf-8")


@beartype
def _module_artifact_payload(package_dir: Path) -> bytes:
    """Build deterministic legacy payload hash source from all files in module directory."""
    if not package_dir.exists() or not package_dir.is_dir():
        raise ValueError(f"Module directory not found: {package_dir}")

    entries: list[str] = []
    for path in sorted(
        (p for p in package_dir.rglob("*") if p.is_file()),
        key=lambda p: p.relative_to(package_dir).as_posix(),
    ):
        rel = path.relative_to(package_dir).as_posix()
        data = (
            _canonical_manifest_payload(path) if rel in {"module-package.yaml", "metadata.yaml"} else path.read_bytes()
        )
        file_digest = hashlib.sha256(data).hexdigest()
        entries.append(f"{rel}:{file_digest}")
    return "\n".join(entries).encode("utf-8")


@beartype
def _module_artifact_payload_stable(package_dir: Path) -> bytes:
    """Build deterministic payload excluding generated/cache files."""
    if not package_dir.exists() or not package_dir.is_dir():
        raise ValueError(f"Module directory not found: {package_dir}")

    def _is_hashable(path: Path) -> bool:
        rel = path.relative_to(package_dir)
        if any(part in _IGNORED_MODULE_DIR_NAMES for part in rel.parts):
            return False
        return path.suffix.lower() not in _IGNORED_MODULE_FILE_SUFFIXES

    entries: list[str] = []
    for path in sorted(
        (p for p in package_dir.rglob("*") if p.is_file() and _is_hashable(p)),
        key=lambda p: p.relative_to(package_dir).as_posix(),
    ):
        rel = path.relative_to(package_dir).as_posix()
        data = (
            _canonical_manifest_payload(path) if rel in {"module-package.yaml", "metadata.yaml"} else path.read_bytes()
        )
        file_digest = hashlib.sha256(data).hexdigest()
        entries.append(f"{rel}:{file_digest}")
    return "\n".join(entries).encode("utf-8")


@beartype
def _is_signature_backend_unavailable(error: ValueError) -> bool:
    """Return True when signature verification backend is unavailable in runtime."""
    message = str(error)
    return (
        "No module named '_cffi_backend'" in message
        or "requires the 'cryptography' package" in message
        or "Signature verification backend unavailable" in message
    )


@lru_cache(maxsize=8)
def _warn_signature_backend_unavailable_once(error_message: str) -> None:
    """Emit signature-backend-unavailable warning at most once per distinct message."""
    get_bridge_logger(__name__).warning(
        "Module signature backend unavailable (%s). Falling back to checksum-only verification.",
        error_message,
    )


@beartype
def install_bundled_module(
    module_name: str,
    target_root: Path,
    *,
    trust_non_official: bool = False,
    non_interactive: bool = False,
) -> bool:
    """Install one bundled module into target root; returns False when module is not bundled."""
    sources = _get_bundled_module_sources()
    source_dir = sources.get(module_name)
    if source_dir is None:
        return False
    assert_module_allowed(module_name)
    metadata = get_bundled_module_metadata().get(module_name)
    if metadata is None:
        raise ValueError(f"Bundled module '{module_name}' metadata not found")
    publisher_name = metadata.publisher.name if metadata.publisher else None
    ensure_publisher_trusted(
        publisher_name,
        trust_non_official=trust_non_official,
        non_interactive=non_interactive,
    )
    allow_unsigned = os.environ.get("SPECFACT_ALLOW_UNSIGNED", "").strip().lower() in {"1", "true", "yes"}
    if not verify_module_artifact(
        source_dir,
        metadata,
        allow_unsigned=allow_unsigned,
        require_integrity=True,
    ):
        raise ValueError(f"Bundled module '{module_name}' failed integrity verification")
    target_root.mkdir(parents=True, exist_ok=True)
    _copy_module_dir(source_dir, target_root / module_name)
    return True


@beartype
@ensure(lambda result: isinstance(result, list), "Result must be a list")
def get_outdated_or_missing_bundled_modules(target_root: Path) -> list[str]:
    """Return bundled module names missing or outdated under target root."""
    outdated_or_missing: list[str] = []
    sources = _get_bundled_module_sources()
    for module_name, source_dir in sources.items():
        source_manifest = source_dir / "module-package.yaml"
        target_manifest = target_root / module_name / "module-package.yaml"
        if not target_manifest.exists():
            outdated_or_missing.append(module_name)
            continue
        if source_manifest.read_text(encoding="utf-8") != target_manifest.read_text(encoding="utf-8"):
            outdated_or_missing.append(module_name)
    return sorted(outdated_or_missing, key=str.lower)


@beartype
def _copy_module_dir(source_dir: Path, target_dir: Path) -> bool:
    """Copy/update one module directory; returns True when target changed."""
    source_manifest = source_dir / "module-package.yaml"
    target_manifest = target_dir / "module-package.yaml"

    if not target_dir.exists():
        shutil.copytree(source_dir, target_dir)
        return True

    source_manifest_text = source_manifest.read_text(encoding="utf-8")
    target_manifest_text = target_manifest.read_text(encoding="utf-8") if target_manifest.exists() else ""
    if source_manifest_text == target_manifest_text:
        return False

    staged_path = target_dir.parent / f".{target_dir.name}.tmp-sync"
    if staged_path.exists():
        shutil.rmtree(staged_path)
    shutil.copytree(source_dir, staged_path)
    if target_dir.exists():
        shutil.rmtree(target_dir)
    staged_path.replace(target_dir)
    return True


@beartype
@ensure(lambda result: result >= 0, "Seeded module count must be non-negative")
def sync_bundled_modules_to_user_root(
    target_root: Path | None = None,
    *,
    trust_non_official: bool = False,
    non_interactive: bool = False,
) -> int:
    """Seed/update shipped modules into canonical user root (~/.specfact/modules)."""
    target = target_root or USER_MODULES_ROOT
    target.mkdir(parents=True, exist_ok=True)
    copied = 0

    metadata_by_name = get_bundled_module_metadata()
    allow_unsigned = os.environ.get("SPECFACT_ALLOW_UNSIGNED", "").strip().lower() in {"1", "true", "yes"}
    for module_name, module_dir in _get_bundled_module_sources().items():
        assert_module_allowed(module_name)
        metadata = metadata_by_name.get(module_name)
        if metadata is None:
            raise ValueError(f"Bundled module '{module_name}' metadata not found")
        publisher_name = metadata.publisher.name if metadata.publisher else None
        ensure_publisher_trusted(
            publisher_name,
            trust_non_official=trust_non_official,
            non_interactive=non_interactive,
        )
        if not verify_module_artifact(
            module_dir,
            metadata,
            allow_unsigned=allow_unsigned,
            require_integrity=True,
        ):
            raise ValueError(f"Bundled module '{module_name}' failed integrity verification")
        if _copy_module_dir(module_dir, target / module_name):
            copied += 1
    return copied


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
    require_integrity: bool = False,
    require_signature: bool = False,
    public_key_pem: str | None = None,
) -> bool:
    """Run integrity verification for a module artifact."""
    logger = get_bridge_logger(__name__)
    manifest_path = package_dir / "module-package.yaml"
    if not manifest_path.exists():
        manifest_path = package_dir / "metadata.yaml"
    if not manifest_path.exists():
        logger.warning("Module %s: No manifest file for integrity check (skipped)", meta.name)
        return allow_unsigned and not require_integrity

    if meta.integrity is None:
        if allow_unsigned:
            logger.debug("Module %s: No integrity metadata; allowing (allow-unsigned)", meta.name)
            return True
        if require_integrity:
            logger.warning("Module %s: Missing integrity metadata", meta.name)
            return False
        return True

    try:
        legacy_payload = _module_artifact_payload(package_dir)
        verify_checksum(legacy_payload, meta.integrity.checksum)
        verification_payload = legacy_payload
    except ValueError as exc:
        try:
            stable_payload = _module_artifact_payload_stable(package_dir)
            verify_checksum(stable_payload, meta.integrity.checksum)
            logger.info(
                "Module %s: checksum matched with generated-file exclusions (cache/transient files ignored)",
                meta.name,
            )
            verification_payload = stable_payload
        except ValueError:
            logger.warning("Module %s: Integrity check failed: %s", meta.name, exc)
            return False

    if meta.integrity.signature:
        key_material = _load_public_key_pem(public_key_pem)
        if not key_material:
            if require_signature and not allow_unsigned:
                logger.warning("Module %s: Signature verification requires public key material", meta.name)
                return False
            logger.warning(
                "Module %s: Signature present but no public key configured; checksum-only verification", meta.name
            )
            return True
        try:
            verify_signature(verification_payload, meta.integrity.signature, key_material)
        except ValueError as exc:
            if _is_signature_backend_unavailable(exc):
                if require_signature and not allow_unsigned:
                    logger.warning("Module %s: signature is required but backend is unavailable", meta.name)
                    return False
                _warn_signature_backend_unavailable_once(str(exc))
                return True
            logger.warning("Module %s: Signature check failed: %s", meta.name, exc)
            return False
    elif require_signature and not allow_unsigned:
        logger.warning("Module %s: Signature is required but missing", meta.name)
        return False

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
    trust_non_official: bool = False,
    non_interactive: bool = False,
) -> Path:
    """Install a marketplace module from tarball into canonical user modules root."""
    logger = get_bridge_logger(__name__)
    target_root = install_root or USER_MODULES_ROOT
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
        manifest_module_name = str(metadata.get("name", module_name)).strip() or module_name
        assert_module_allowed(manifest_module_name)

        compatibility = str(metadata.get("core_compatibility", "")).strip()
        if compatibility and Version(cli_version) not in SpecifierSet(compatibility):
            raise ValueError("Module is incompatible with current SpecFact CLI version")

        publisher_name: str | None = None
        publisher_raw = metadata.get("publisher")
        if isinstance(publisher_raw, dict):
            publisher_name = str(publisher_raw.get("name", "")).strip() or None
        ensure_publisher_trusted(
            publisher_name,
            trust_non_official=trust_non_official,
            non_interactive=non_interactive,
        )

        try:
            metadata_obj = ModulePackageMetadata(**metadata)
        except Exception:
            metadata_obj = ModulePackageMetadata(
                name=manifest_module_name,
                version=str(metadata.get("version", "0.1.0")),
                commands=[str(command) for command in metadata.get("commands", []) if str(command).strip()],
            )
        allow_unsigned = os.environ.get("SPECFACT_ALLOW_UNSIGNED", "").strip().lower() in {"1", "true", "yes"}
        if not verify_module_artifact(
            extracted_module_dir,
            metadata_obj,
            allow_unsigned=allow_unsigned,
        ):
            raise ValueError("Downloaded module failed integrity verification")

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
    """Uninstall a marketplace module from the local canonical user root."""
    logger = get_bridge_logger(__name__)

    if source_map is None:
        from specfact_cli.registry.module_discovery import discover_all_modules

        source_map = {entry.metadata.name: entry.source for entry in discover_all_modules()}

    source = source_map.get(module_name)
    if source == "builtin":
        raise ValueError("Cannot uninstall built-in module")
    if source not in {"marketplace", "user"}:
        raise ValueError(f"Cannot uninstall module from source '{source or 'unknown'}'")

    if install_root is not None:
        candidate_roots = [install_root]
    elif source == "marketplace":
        candidate_roots = [MARKETPLACE_MODULES_ROOT, USER_MODULES_ROOT]
    else:
        candidate_roots = [USER_MODULES_ROOT, MARKETPLACE_MODULES_ROOT]

    for root in candidate_roots:
        module_path = root / module_name
        if not module_path.exists():
            continue
        shutil.rmtree(module_path)
        logger.info("Uninstalled module '%s' from '%s'", module_name, root)
        return

    roots_str = ", ".join(str(root) for root in candidate_roots)
    raise ValueError(f"Module '{module_name}' is not installed under expected roots: {roots_str}")
