"""Module artifact verification, user-root bootstrap, and installation workflows."""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

import yaml
from beartype import beartype
from icontract import ensure, require
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from specfact_cli import __version__ as cli_version
from specfact_cli.common import get_bridge_logger
from specfact_cli.models.module_package import ModulePackageMetadata
from specfact_cli.registry.crypto_validator import verify_checksum, verify_signature
from specfact_cli.registry.dependency_resolver import DependencyConflictError, resolve_dependencies
from specfact_cli.registry.marketplace_client import download_module
from specfact_cli.registry.module_discovery import discover_all_modules
from specfact_cli.registry.module_security import assert_module_allowed, ensure_publisher_trusted
from specfact_cli.runtime import is_debug_mode


USER_MODULES_ROOT = Path.home() / ".specfact" / "modules"
MARKETPLACE_MODULES_ROOT = Path.home() / ".specfact" / "marketplace-modules"
MODULE_DOWNLOAD_CACHE_ROOT = Path.home() / ".specfact" / "downloads" / "cache"
_IGNORED_MODULE_DIR_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "logs", "tests"}
_IGNORED_MODULE_FILE_SUFFIXES = {".pyc", ".pyo"}
REGISTRY_ID_FILE = ".specfact-registry-id"
# Installer-written runtime files; excluded from payload so post-install verification matches
INSTALL_VERIFIED_CHECKSUM_FILE = ".specfact-install-verified-checksum"
_IGNORED_MODULE_FILE_NAMES = {REGISTRY_ID_FILE, INSTALL_VERIFIED_CHECKSUM_FILE}
_MARKETPLACE_NAMESPACE_PATTERN = re.compile(r"^[a-z][a-z0-9-]*/[a-z][a-z0-9-]+$")


@beartype
def _validate_marketplace_namespace_format(module_id: str) -> None:
    """Raise ValueError if module_id does not match namespace/name (lowercase, alphanumeric + hyphens)."""
    if not _MARKETPLACE_NAMESPACE_PATTERN.match(module_id.strip()):
        raise ValueError(
            f"Marketplace module id must match namespace/name (lowercase, alphanumeric and hyphens): {module_id!r}"
        )


@beartype
def _check_namespace_collision(module_id: str, final_path: Path, reinstall: bool) -> None:
    """Raise ValueError if final_path already contains a module installed from a different module_id."""
    if reinstall or not final_path.exists():
        return
    id_file = final_path / REGISTRY_ID_FILE
    if not id_file.exists():
        return
    try:
        existing_id = id_file.read_text(encoding="utf-8").strip()
    except OSError:
        return
    if existing_id and existing_id != module_id:
        raise ValueError(
            f"Module namespace collision: {module_id!r} conflicts with existing {existing_id!r}. "
            "Use alias for disambiguation or uninstall the existing module first."
        )


@beartype
def _cache_archive_name(module_id: str, version: str | None = None) -> str:
    """Return deterministic archive cache filename for module id/version."""
    suffix = version.strip() if isinstance(version, str) and version.strip() else "latest"
    return f"{module_id.replace('/', '--')}--{suffix}.tar.gz"


@beartype
def _cache_downloaded_archive(archive_path: Path, module_id: str, version: str | None = None) -> Path:
    """Copy downloaded archive into deterministic local cache location."""
    logger = get_bridge_logger(__name__)
    cached_path = MODULE_DOWNLOAD_CACHE_ROOT / _cache_archive_name(module_id, version)
    try:
        MODULE_DOWNLOAD_CACHE_ROOT.mkdir(parents=True, exist_ok=True)
        if archive_path.resolve() == cached_path.resolve():
            return cached_path
        shutil.copy2(archive_path, cached_path)
        return cached_path
    except OSError as exc:
        logger.debug("Skipping module archive cache write for %s: %s", module_id, exc)
        return archive_path


@beartype
def _find_cached_archive(module_id: str, version: str | None = None) -> Path | None:
    """Find cached archive for module id/version; return newest matching artifact."""
    preferred: list[Path] = []
    if isinstance(version, str) and version.strip():
        preferred.append(MODULE_DOWNLOAD_CACHE_ROOT / _cache_archive_name(module_id, version))
    preferred.append(MODULE_DOWNLOAD_CACHE_ROOT / _cache_archive_name(module_id, None))
    for path in preferred:
        if path.exists():
            return path
    wildcard = sorted(MODULE_DOWNLOAD_CACHE_ROOT.glob(f"{module_id.replace('/', '--')}--*.tar.gz"))
    if wildcard:
        return wildcard[-1]
    return None


@beartype
def _download_archive_with_cache(module_id: str, version: str | None = None) -> Path:
    """Download module archive and fallback to cached artifact when offline."""
    logger = get_bridge_logger(__name__)
    try:
        archive = download_module(module_id, version=version)
        _cache_downloaded_archive(archive, module_id, version)
        return archive
    except Exception as exc:
        message = str(exc).lower()
        offline_like = "offline" in message or "cannot install from marketplace" in message
        if not offline_like:
            raise exc
        cached = _find_cached_archive(module_id, version)
        if cached is not None:
            logger.warning("Marketplace unavailable for %s; using cached archive %s", module_id, cached)
            return cached
        raise exc


@beartype
def _extract_bundle_dependencies(metadata: dict[str, Any]) -> list[str]:
    """Extract validated bundle dependency module ids from raw manifest metadata."""
    raw_dependencies = metadata.get("bundle_dependencies", [])
    if not isinstance(raw_dependencies, list):
        return []
    dependencies: list[str] = []
    for value in raw_dependencies:
        dep = str(value).strip()
        if not dep:
            continue
        _validate_marketplace_namespace_format(dep)
        dependencies.append(dep)
    return dependencies


@beartype
def _installed_dependency_version(manifest_path: Path) -> str:
    """Return installed dependency version from manifest path."""
    if not manifest_path.exists():
        return "unknown"
    try:
        metadata = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        if isinstance(metadata, dict):
            return str(cast(dict[str, Any], metadata).get("version", "unknown"))
    except Exception:
        return "unknown"
    return "unknown"


@beartype
def _integrity_debug_details_enabled() -> bool:
    """Return True when verbose integrity diagnostics should be shown."""
    if is_debug_mode():
        return True
    return "--debug" in sys.argv[1:]


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
    cast(dict[str, Any], parsed).pop("integrity", None)
    return yaml.safe_dump(parsed, sort_keys=True, allow_unicode=False).encode("utf-8")


@beartype
def _module_artifact_payload(package_dir: Path) -> bytes:
    """Build deterministic legacy payload hash source from all files in module directory."""
    if not package_dir.exists() or not package_dir.is_dir():
        raise ValueError(f"Module directory not found: {package_dir}")

    entries: list[str] = []
    for path in sorted(
        (p for p in package_dir.rglob("*") if p.is_file() and p.name not in _IGNORED_MODULE_FILE_NAMES),
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
        if path.name in _IGNORED_MODULE_FILE_NAMES:
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


def _signed_payload_is_hashable(path: Path, module_dir_resolved: Path) -> bool:
    rel = path.resolve().relative_to(module_dir_resolved)
    if any(part in _IGNORED_MODULE_DIR_NAMES for part in rel.parts):
        return False
    if path.name in _IGNORED_MODULE_FILE_NAMES:
        return False
    return path.suffix.lower() not in _IGNORED_MODULE_FILE_SUFFIXES


def _git_tracked_module_files(package_dir: Path, module_dir_resolved: Path) -> list[Path] | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=package_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=2,
        )
        if result.returncode != 0 or not result.stdout.strip():
            raise FileNotFoundError("not in git repo")
        git_root = Path(result.stdout.strip()).resolve()
        rel_to_repo = module_dir_resolved.relative_to(git_root)
        ls_result = subprocess.run(
            ["git", "ls-files", "--", rel_to_repo.as_posix()],
            cwd=git_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=2,
        )
        if ls_result.returncode != 0:
            raise FileNotFoundError("git ls-files failed")
        lines = [line.strip() for line in ls_result.stdout.splitlines() if line.strip()]
        files = [git_root / line for line in lines]
        files = [p for p in files if p.is_file() and _signed_payload_is_hashable(p, module_dir_resolved)]
        files.sort(key=lambda p: p.resolve().relative_to(module_dir_resolved).as_posix())
        return files
    except (FileNotFoundError, ValueError, subprocess.TimeoutExpired):
        return None


def _rglob_signed_module_files(package_dir: Path, module_dir_resolved: Path) -> list[Path]:
    return sorted(
        (p for p in package_dir.rglob("*") if p.is_file() and _signed_payload_is_hashable(p, module_dir_resolved)),
        key=lambda p: p.resolve().relative_to(module_dir_resolved).as_posix(),
    )


def _signed_payload_entries_for_files(files: list[Path], module_dir_resolved: Path) -> list[str]:
    entries: list[str] = []
    for path in files:
        rel = path.resolve().relative_to(module_dir_resolved).as_posix()
        if rel in {"module-package.yaml", "metadata.yaml"}:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError(f"Invalid manifest YAML: {path}")
            data = _canonical_manifest_payload(path)
        else:
            data = path.read_bytes()
        entries.append(f"{rel}:{hashlib.sha256(data).hexdigest()}")
    return entries


def _module_artifact_payload_signed(package_dir: Path) -> bytes:
    """Build payload identical to scripts/sign-modules.py so verification matches after signing.

    Uses git ls-files when the module lives in a git repo (same file set and order as sign script);
    otherwise falls back to rglob + same hashable/sort rules so checksums match for non-git use.
    """
    if not package_dir.exists() or not package_dir.is_dir():
        raise ValueError(f"Module directory not found: {package_dir}")
    module_dir_resolved = package_dir.resolve()
    files = _git_tracked_module_files(package_dir, module_dir_resolved)
    if files is None:
        files = _rglob_signed_module_files(package_dir, module_dir_resolved)
    return "\n".join(_signed_payload_entries_for_files(files, module_dir_resolved)).encode("utf-8")


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
@require(lambda module_name: cast(str, module_name).strip() != "", "module_name must not be empty")
@require(lambda target_root: isinstance(target_root, Path), "target_root must be a Path")
@ensure(lambda result: isinstance(result, bool), "Must return a bool")
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


def _resolve_checksum_verification_payload(
    package_dir: Path,
    meta: ModulePackageMetadata,
    logger: Any,
) -> bytes | None:
    assert meta.integrity is not None
    try:
        signed_payload = _module_artifact_payload_signed(package_dir)
        verify_checksum(signed_payload, meta.integrity.checksum)
        return signed_payload
    except ValueError:
        pass
    try:
        legacy_payload = _module_artifact_payload(package_dir)
        verify_checksum(legacy_payload, meta.integrity.checksum)
        return legacy_payload
    except ValueError as exc:
        legacy_exc = exc
        try:
            stable_payload = _module_artifact_payload_stable(package_dir)
            verify_checksum(stable_payload, meta.integrity.checksum)
            if _integrity_debug_details_enabled():
                logger.debug(
                    "Module %s: checksum matched with generated-file exclusions (cache/transient files ignored)",
                    meta.name,
                )
            return stable_payload
        except ValueError:
            if _integrity_debug_details_enabled():
                logger.warning("Module %s: Integrity check failed: %s", meta.name, legacy_exc)
            else:
                logger.debug("Module %s: Integrity check failed: %s", meta.name, legacy_exc)
            return _install_verified_checksum_fallback(package_dir, meta, logger)


def _install_verified_checksum_fallback(
    package_dir: Path,
    meta: ModulePackageMetadata,
    logger: Any,
) -> bytes | None:
    install_checksum_file = package_dir / INSTALL_VERIFIED_CHECKSUM_FILE
    if not install_checksum_file.is_file():
        if _integrity_debug_details_enabled():
            logger.debug(
                "Module %s: no %s (reinstall to write it)",
                meta.name,
                INSTALL_VERIFIED_CHECKSUM_FILE,
            )
        return None
    try:
        legacy_payload = _module_artifact_payload(package_dir)
        computed = f"sha256:{hashlib.sha256(legacy_payload).hexdigest()}"
        stored = install_checksum_file.read_text(encoding="utf-8").strip()
        if stored and computed == stored:
            if _integrity_debug_details_enabled():
                logger.debug(
                    "Module %s: accepted via install-time verified checksum",
                    meta.name,
                )
            return legacy_payload
        if _integrity_debug_details_enabled():
            logger.debug(
                "Module %s: install-verified checksum mismatch (computed=%s, stored=%s)",
                meta.name,
                computed[:32] + "...",
                stored[:32] + "..." if len(stored) > 32 else stored,
            )
        return None
    except (OSError, ValueError) as fallback_exc:
        if _integrity_debug_details_enabled():
            logger.debug(
                "Module %s: install-verified fallback error: %s",
                meta.name,
                fallback_exc,
            )
        return None


def _verify_signature_if_present(
    meta: ModulePackageMetadata,
    verification_payload: bytes,
    public_key_pem: str | None,
    allow_unsigned: bool,
    require_signature: bool,
    logger: Any,
) -> bool:
    if meta.integrity and meta.integrity.signature:
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
        return True
    if require_signature and not allow_unsigned:
        logger.warning("Module %s: Signature is required but missing", meta.name)
        return False
    return True


@beartype
@require(lambda package_dir: isinstance(package_dir, Path), "package_dir must be a Path")
@require(lambda meta: isinstance(meta, ModulePackageMetadata), "meta must be a ModulePackageMetadata instance")
@ensure(lambda result: isinstance(result, bool), "Must return a bool")
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

    if (package_dir / REGISTRY_ID_FILE).exists() and _integrity_debug_details_enabled():
        logger.debug(
            "Excluding installer-written %s from verification payload",
            REGISTRY_ID_FILE,
        )

    assert meta.integrity is not None
    verification_payload = _resolve_checksum_verification_payload(package_dir, meta, logger)
    if verification_payload is None:
        return False
    return _verify_signature_if_present(
        meta, verification_payload, public_key_pem, allow_unsigned, require_signature, logger
    )


def _clear_reinstall_download_cache(module_id: str, logger: Any) -> None:
    from specfact_cli.registry.marketplace_client import get_modules_branch

    get_modules_branch.cache_clear()
    for stale in MODULE_DOWNLOAD_CACHE_ROOT.glob(f"{module_id.replace('/', '--')}--*.tar.gz"):
        try:
            stale.unlink()
            logger.debug("Cleared cached archive %s for reinstall", stale.name)
        except OSError:
            pass


def _extract_marketplace_archive(archive_path: Path, extract_root: Path) -> None:
    with tarfile.open(archive_path, "r:gz") as archive:
        members = archive.getmembers()
        _validate_archive_members(members, extract_root)
        try:
            archive.extractall(path=extract_root, members=members, filter="data")
        except TypeError:
            archive.extractall(path=extract_root, members=members)


def _load_first_extracted_module_manifest(extract_root: Path) -> tuple[Path, dict[str, Any]]:
    candidate_dirs = [p for p in extract_root.rglob("module-package.yaml") if p.is_file()]
    if not candidate_dirs:
        raise ValueError("Downloaded module archive does not contain module-package.yaml")
    extracted_manifest = candidate_dirs[0]
    metadata = yaml.safe_load(extracted_manifest.read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        raise ValueError("Invalid module manifest format")
    return extracted_manifest.parent, metadata


def _validate_install_manifest_constraints(
    metadata: dict[str, Any],
    module_name: str,
    trust_non_official: bool,
    non_interactive: bool,
) -> str:
    manifest_module_name = str(metadata.get("name", module_name)).strip() or module_name
    assert_module_allowed(manifest_module_name)
    compatibility = str(metadata.get("core_compatibility", "")).strip()
    if compatibility and Version(cli_version) not in SpecifierSet(compatibility):
        raise ValueError("Module is incompatible with current SpecFact CLI version")
    publisher_name: str | None = None
    publisher_raw = metadata.get("publisher")
    if isinstance(publisher_raw, dict):
        publisher_name = str(cast(dict[str, Any], publisher_raw).get("name", "")).strip() or None
    ensure_publisher_trusted(
        publisher_name,
        trust_non_official=trust_non_official,
        non_interactive=non_interactive,
    )
    return manifest_module_name


def _metadata_obj_from_install_dict(metadata: dict[str, Any], manifest_module_name: str) -> ModulePackageMetadata:
    try:
        return ModulePackageMetadata(**metadata)
    except Exception:
        return ModulePackageMetadata(
            name=manifest_module_name,
            version=str(metadata.get("version", "0.1.0")),
            commands=[str(command) for command in metadata.get("commands", []) if str(command).strip()],
        )


def _install_bundle_dependencies_for_module(
    module_id: str,
    metadata: dict[str, Any],
    metadata_obj: ModulePackageMetadata,
    target_root: Path,
    trust_non_official: bool,
    non_interactive: bool,
    force: bool,
    logger: Any,
) -> None:
    for dependency_module_id in _extract_bundle_dependencies(metadata):
        if dependency_module_id == module_id:
            continue
        dependency_name = dependency_module_id.split("/", 1)[1]
        dependency_manifest = target_root / dependency_name / "module-package.yaml"
        if dependency_manifest.exists():
            dependency_version = _installed_dependency_version(dependency_manifest)
            logger.info("Dependency %s already satisfied (version %s)", dependency_module_id, dependency_version)
            continue
        try:
            install_module(
                dependency_module_id,
                install_root=target_root,
                trust_non_official=trust_non_official,
                non_interactive=non_interactive,
                skip_deps=False,
                force=force,
            )
        except Exception as dep_exc:
            raise ValueError(f"Dependency install failed for {dependency_module_id}: {dep_exc}") from dep_exc
    try:
        all_metas = [e.metadata for e in discover_all_modules()]
        all_metas.append(metadata_obj)
        resolve_dependencies(all_metas)
    except DependencyConflictError as dep_err:
        if not force:
            raise ValueError(
                f"Dependency conflict: {dep_err}. Use --force to bypass or --skip-deps to skip resolution."
            ) from dep_err
        logger.warning("Dependency conflict bypassed by --force: %s", dep_err)


def _atomic_place_verified_module(
    extracted_module_dir: Path,
    metadata_obj: ModulePackageMetadata,
    module_name: str,
    module_id: str,
    target_root: Path,
    final_path: Path,
) -> None:
    allow_unsigned = os.environ.get("SPECFACT_ALLOW_UNSIGNED", "").strip().lower() in {"1", "true", "yes"}
    if not verify_module_artifact(
        extracted_module_dir,
        metadata_obj,
        allow_unsigned=allow_unsigned,
    ):
        raise ValueError("Downloaded module failed integrity verification")

    install_verified_checksum = f"sha256:{hashlib.sha256(_module_artifact_payload(extracted_module_dir)).hexdigest()}"

    staged_path = target_root / f".{module_name}.tmp-install"
    if staged_path.exists():
        shutil.rmtree(staged_path)
    shutil.copytree(extracted_module_dir, staged_path)

    try:
        if final_path.exists():
            shutil.rmtree(final_path)
        staged_path.replace(final_path)
        (final_path / REGISTRY_ID_FILE).write_text(module_id, encoding="utf-8")
        (final_path / INSTALL_VERIFIED_CHECKSUM_FILE).write_text(install_verified_checksum, encoding="utf-8")
    except Exception:
        if staged_path.exists():
            shutil.rmtree(staged_path)
        raise


@beartype
@require(
    lambda module_id: "/" in cast(str, module_id) and len(cast(str, module_id).split("/")) == 2,
    "module_id must be namespace/name",
)
@ensure(lambda result: cast(Path, result).exists(), "Installed module path must exist")
def install_module(
    module_id: str,
    *,
    version: str | None = None,
    reinstall: bool = False,
    install_root: Path | None = None,
    trust_non_official: bool = False,
    non_interactive: bool = False,
    skip_deps: bool = False,
    force: bool = False,
) -> Path:
    """Install a marketplace module from tarball into canonical user modules root."""
    logger = get_bridge_logger(__name__)
    target_root = install_root or USER_MODULES_ROOT
    target_root.mkdir(parents=True, exist_ok=True)

    _validate_marketplace_namespace_format(module_id)
    _namespace, module_name = module_id.split("/", 1)
    final_path = target_root / module_name
    manifest_path = final_path / "module-package.yaml"

    _check_namespace_collision(module_id, final_path, reinstall)
    if manifest_path.exists() and not reinstall:
        logger.debug("Module already installed (%s)", module_name)
        return final_path

    if reinstall:
        _clear_reinstall_download_cache(module_id, logger)

    archive_path = _download_archive_with_cache(module_id, version=version)

    with tempfile.TemporaryDirectory(prefix="specfact-module-install-") as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        extract_root = tmp_dir_path / "extract"
        extract_root.mkdir(parents=True, exist_ok=True)

        _extract_marketplace_archive(archive_path, extract_root)

        extracted_module_dir, metadata = _load_first_extracted_module_manifest(extract_root)
        manifest_module_name = _validate_install_manifest_constraints(
            metadata, module_name, trust_non_official, non_interactive
        )
        metadata_obj = _metadata_obj_from_install_dict(metadata, manifest_module_name)

        if not skip_deps:
            _install_bundle_dependencies_for_module(
                module_id,
                metadata,
                metadata_obj,
                target_root,
                trust_non_official,
                non_interactive,
                force,
                logger,
            )

        _atomic_place_verified_module(
            extracted_module_dir,
            metadata_obj,
            module_name,
            module_id,
            target_root,
            final_path,
        )

    logger.debug("Installed marketplace module '%s' to '%s'", module_id, final_path)
    return final_path


@beartype
@require(lambda module_name: cast(str, module_name).strip() != "", "module_name must be non-empty")
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
        logger.debug("Uninstalled module '%s' from '%s'", module_name, root)
        return

    roots_str = ", ".join(str(root) for root in candidate_roots)
    raise ValueError(f"Module '{module_name}' is not installed under expected roots: {roots_str}")
