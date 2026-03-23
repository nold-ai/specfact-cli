#!/usr/bin/env python3
"""Sign SpecFact module manifests with checksum/signature over full module payload."""

from __future__ import annotations

import argparse
import base64
import getpass
import hashlib
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import yaml
from beartype import beartype
from icontract import ensure, require


logger = logging.getLogger(__name__)


_IGNORED_MODULE_DIR_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "logs", "tests"}
_IGNORED_MODULE_FILE_SUFFIXES = {".pyc", ".pyo"}
_PAYLOAD_FROM_FS_IGNORED_DIRS = _IGNORED_MODULE_DIR_NAMES | {".git"}


class _IndentedSafeDumper(yaml.SafeDumper):
    """Safe dumper that indents sequence items under their parent key."""

    @beartype
    @require(lambda self: self is not None, "Dumper must be bound")
    @require(lambda flow: isinstance(flow, bool), "flow must be bool")
    @require(lambda indentless: isinstance(indentless, bool), "indentless must be bool")
    @ensure(lambda result: result is None, "PyYAML increase_indent returns None")
    def increase_indent(self, flow: bool = False, indentless: bool = False) -> None:
        super().increase_indent(flow=flow, indentless=False)


def _canonical_payload(manifest_data: dict[str, Any]) -> bytes:
    payload = dict(manifest_data)
    payload.pop("integrity", None)
    return yaml.safe_dump(payload, sort_keys=True, allow_unicode=False).encode("utf-8")


def _is_hashable_path(path: Path, module_dir_resolved: Path, ignored_dirs: set[str]) -> bool:
    """Return whether a path should contribute to the module payload hash."""
    rel = path.resolve().relative_to(module_dir_resolved)
    if any(part in ignored_dirs for part in rel.parts):
        return False
    return path.suffix.lower() not in _IGNORED_MODULE_FILE_SUFFIXES


def _filesystem_payload_files(module_dir: Path, module_dir_resolved: Path, ignored_dirs: set[str]) -> list[Path]:
    """Collect payload files directly from the filesystem."""
    return sorted(
        (p for p in module_dir.rglob("*") if p.is_file() and _is_hashable_path(p, module_dir_resolved, ignored_dirs)),
        key=lambda p: p.resolve().relative_to(module_dir_resolved).as_posix(),
    )


def _git_payload_files(module_dir: Path, module_dir_resolved: Path, ignored_dirs: set[str]) -> list[Path]:
    """Collect payload files from git, falling back to filesystem on failure."""
    try:
        listed = subprocess.run(
            ["git", "ls-files", module_dir.as_posix()],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    except Exception:
        return _filesystem_payload_files(module_dir, module_dir_resolved, ignored_dirs)
    git_files = [(Path.cwd() / line.strip()) for line in listed if line.strip()]
    return sorted(
        (path for path in git_files if path.is_file() and _is_hashable_path(path, module_dir_resolved, ignored_dirs)),
        key=lambda p: p.resolve().relative_to(module_dir_resolved).as_posix(),
    )


def _payload_files(
    module_dir: Path, module_dir_resolved: Path, payload_from_filesystem: bool, ignored_dirs: set[str]
) -> list[Path]:
    """Collect payload files from the requested source."""
    if payload_from_filesystem:
        return _filesystem_payload_files(module_dir, module_dir_resolved, ignored_dirs)
    return _git_payload_files(module_dir, module_dir_resolved, ignored_dirs)


def _payload_entry_bytes(path: Path) -> bytes:
    """Load bytes used for a single payload entry."""
    rel_name = path.name
    if rel_name in {"module-package.yaml", "metadata.yaml"}:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            msg = f"Invalid manifest YAML: {path}"
            raise ValueError(msg)
        return _canonical_payload(raw)
    return path.read_bytes()


def _module_payload(module_dir: Path, payload_from_filesystem: bool = False) -> bytes:
    if not module_dir.exists() or not module_dir.is_dir():
        msg = f"Module directory not found: {module_dir}"
        raise ValueError(msg)
    module_dir_resolved = module_dir.resolve()

    entries: list[str] = []
    ignored_dirs = _PAYLOAD_FROM_FS_IGNORED_DIRS if payload_from_filesystem else _IGNORED_MODULE_DIR_NAMES
    files = _payload_files(module_dir, module_dir_resolved, payload_from_filesystem, ignored_dirs)
    for path in files:
        rel = path.resolve().relative_to(module_dir_resolved).as_posix()
        data = _payload_entry_bytes(path)
        entries.append(f"{rel}:{hashlib.sha256(data).hexdigest()}")
    return "\n".join(entries).encode("utf-8")


def _configured_key_file(key_file: Path | None) -> Path | None:
    """Resolve the configured private key file from args or environment."""
    configured_file = os.environ.get("SPECFACT_MODULE_PRIVATE_SIGN_KEY_FILE", "").strip()
    if not configured_file:
        configured_file = os.environ.get("SPECFACT_MODULE_SIGNING_PRIVATE_KEY_FILE", "").strip()
    return key_file or (Path(configured_file) if configured_file else None)


def _private_key_pem(effective_file: Path | None) -> str:
    """Resolve PEM text from environment or the configured file."""
    pem = os.environ.get("SPECFACT_MODULE_PRIVATE_SIGN_KEY", "").strip()
    if not pem:
        pem = os.environ.get("SPECFACT_MODULE_SIGNING_PRIVATE_KEY_PEM", "").strip()
    if not pem and effective_file:
        pem = effective_file.read_text(encoding="utf-8")
    return pem


def _load_serialization_module() -> Any:
    """Import the cryptography serialization backend."""
    try:
        from cryptography.hazmat.primitives import serialization
    except Exception as exc:
        raise ValueError(
            "Unable to import cryptography backend for signing. "
            "Install signing dependencies (`python3 -m pip install cryptography cffi`) "
            "or run via project environment (`hatch run python scripts/sign-modules.py ...`)."
        ) from exc
    return serialization


def _load_private_key_bytes(serialization: Any, pem: str, password_bytes: bytes | None) -> Any:
    """Load a private key from PEM bytes with the provided password."""
    return serialization.load_pem_private_key(pem.encode("utf-8"), password=password_bytes)


def _load_private_key(
    key_file: Path | None = None,
    *,
    passphrase: str | None = None,
    prompt_for_passphrase: bool = False,
) -> Any | None:
    effective_file = _configured_key_file(key_file)
    pem = _private_key_pem(effective_file)
    if not pem:
        return None
    serialization = _load_serialization_module()
    password_bytes = passphrase.encode("utf-8") if passphrase is not None else None
    try:
        return _load_private_key_bytes(serialization, pem, password_bytes)
    except Exception as exc:
        message = str(exc).lower()
        needs_password = "password was not given" in message or "private key is encrypted" in message
        if needs_password and prompt_for_passphrase:
            prompted = getpass.getpass("Enter signing key passphrase: ")
            try:
                return _load_private_key_bytes(serialization, pem, prompted.encode("utf-8"))
            except Exception as retry_exc:
                raise ValueError(f"Failed to load private key from PEM: {retry_exc}") from retry_exc
        if needs_password and passphrase is None:
            raise ValueError(
                "Private key is encrypted. Provide passphrase via --passphrase, --passphrase-stdin, "
                "or SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE."
            ) from exc
        raise ValueError(f"Failed to load private key from PEM: {exc}") from exc


def _resolve_passphrase(args: argparse.Namespace) -> str | None:
    explicit = (args.passphrase or "").strip()
    if explicit:
        return explicit
    env_value = os.environ.get("SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE", "").strip()
    if not env_value:
        env_value = os.environ.get("SPECFACT_MODULE_SIGNING_PRIVATE_KEY_PASSPHRASE", "").strip()
    if env_value:
        return env_value
    if args.passphrase_stdin:
        piped = sys.stdin.read().rstrip("\r\n")
        return piped if piped else None
    return None


def _read_manifest_version(path: Path) -> str | None:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return None
    data = cast(dict[str, Any], raw)
    value = data.get("version")
    if value is None:
        return None
    version = str(value).strip()
    return version or None


def _read_manifest_version_from_git(git_ref: str, path: Path) -> str | None:
    try:
        output = subprocess.run(
            ["git", "show", f"{git_ref}:{path.as_posix()}"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    try:
        raw = yaml.safe_load(output.stdout)
    except Exception:
        return None
    if not isinstance(raw, dict):
        return None
    data = cast(dict[str, Any], raw)
    value = data.get("version")
    if value is None:
        return None
    version = str(value).strip()
    return version or None


def _iter_manifests() -> list[Path]:
    roots = [Path("src/specfact_cli/modules"), Path("modules")]
    manifests: list[Path] = []
    for root in roots:
        if root.exists():
            manifests.extend(sorted(root.rglob("module-package.yaml")))
    return manifests


def _ensure_valid_git_ref(git_ref: str) -> None:
    try:
        subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{git_ref}^{{commit}}"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        details = (exc.stderr or exc.stdout or "").strip()
        suffix = f": {details}" if details else ""
        raise ValueError(f"--base-ref is invalid or not resolvable: {git_ref}{suffix}") from exc


def _module_has_git_changes_since(module_dir: Path, git_ref: str) -> bool:
    try:
        changed = subprocess.run(
            ["git", "diff", "--name-only", git_ref, "--", module_dir.as_posix()],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard", "--", module_dir.as_posix()],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except Exception:
        return False
    return bool(changed or untracked)


def _parse_semver(version: str) -> tuple[int, int, int]:
    parts = version.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise ValueError(f"Unsupported version format for auto-bump (expected x.y.z): {version}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def _bump_semver(version: str, bump_type: str) -> str:
    major, minor, patch = _parse_semver(version)
    if bump_type == "major":
        return f"{major + 1}.0.0"
    if bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    if bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"Unsupported bump type: {bump_type}")


def _write_manifest(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        yaml.dump(
            data,
            Dumper=_IndentedSafeDumper,
            sort_keys=False,
            allow_unicode=False,
            default_flow_style=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _auto_bump_manifest_version(manifest_path: Path, *, base_ref: str, bump_type: str) -> bool:
    current_version = _read_manifest_version(manifest_path)
    if not current_version:
        raise ValueError(f"Manifest missing version: {manifest_path}")

    previous_version = _read_manifest_version_from_git(base_ref, manifest_path)
    if previous_version is None or current_version != previous_version:
        return False

    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid manifest YAML: {manifest_path}")
    bumped = _bump_semver(current_version, bump_type)
    raw["version"] = bumped
    _write_manifest(manifest_path, raw)
    logger.info("%s: version %s -> %s", manifest_path, current_version, bumped)
    return True


def _enforce_version_bump_before_signing(
    manifest_path: Path, *, allow_same_version: bool, comparison_ref: str = "HEAD"
) -> None:
    if allow_same_version:
        return

    current_version = _read_manifest_version(manifest_path)
    if not current_version:
        raise ValueError(f"Manifest missing version: {manifest_path}")

    previous_version = _read_manifest_version_from_git(comparison_ref, manifest_path)
    if previous_version is None:
        return
    if current_version != previous_version:
        return

    module_dir = manifest_path.parent
    if not _module_has_git_changes_since(module_dir, comparison_ref):
        return

    raise ValueError(
        f"Module version must be incremented before signing changed module contents: {manifest_path} "
        f"(current version {current_version})."
    )


def _sign_payload(payload: bytes, private_key: Any) -> str:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ed25519, padding, rsa

    if isinstance(private_key, ed25519.Ed25519PrivateKey):
        signature = private_key.sign(payload)
    elif isinstance(private_key, rsa.RSAPrivateKey):
        signature = private_key.sign(payload, padding.PKCS1v15(), hashes.SHA256())
    else:
        msg = "Unsupported private key type for signing (RSA and Ed25519 only)"
        raise ValueError(msg)
    return base64.b64encode(signature).decode("ascii")


@require(lambda manifest_path: cast(Path, manifest_path).suffix == ".yaml", "manifest_path must point to YAML")
def sign_manifest(manifest_path: Path, private_key: Any | None, *, payload_from_filesystem: bool = False) -> None:
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        msg = f"Invalid manifest YAML: {manifest_path}"
        raise ValueError(msg)

    payload = _module_payload(manifest_path.parent, payload_from_filesystem=payload_from_filesystem)
    checksum = f"sha256:{hashlib.sha256(payload).hexdigest()}"
    integrity: dict[str, str] = {"checksum": checksum}

    if private_key is not None:
        integrity["signature"] = _sign_payload(payload, private_key)

    raw["integrity"] = integrity
    _write_manifest(manifest_path, raw)

    status = "checksum+signature" if "signature" in integrity else "checksum"
    logger.info("%s: %s", manifest_path, status)


def _resolve_manifests(args: argparse.Namespace, parser: argparse.ArgumentParser) -> list[Path]:
    """Resolve the set of manifests to sign from CLI arguments."""
    if args.manifests:
        return [Path(manifest) for manifest in args.manifests]
    if not args.changed_only:
        parser.error("Provide one or more manifests, or use --changed-only.")
    try:
        _ensure_valid_git_ref(args.base_ref)
    except ValueError as exc:
        parser.error(str(exc))
    return [manifest for manifest in _iter_manifests() if _module_has_git_changes_since(manifest.parent, args.base_ref)]


def _sign_requested_manifests(
    args: argparse.Namespace, parser: argparse.ArgumentParser, private_key: Any | None
) -> int:
    """Sign the resolved manifest set."""
    manifests = _resolve_manifests(args, parser)
    if args.changed_only and not manifests:
        logger.info("No changed module manifests detected since %s.", args.base_ref)
        return 0
    for manifest_path in manifests:
        try:
            if args.changed_only and args.bump_version:
                _auto_bump_manifest_version(
                    manifest_path,
                    base_ref=args.base_ref,
                    bump_type=args.bump_version,
                )
            _enforce_version_bump_before_signing(
                manifest_path,
                allow_same_version=args.allow_same_version,
                comparison_ref=args.base_ref if args.changed_only else "HEAD",
            )
            sign_manifest(manifest_path, private_key, payload_from_filesystem=args.payload_from_filesystem)
        except ValueError as exc:
            parser.error(str(exc))
    return 0


@beartype
@ensure(lambda result: result >= 0, "exit code must be non-negative")
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--key-file",
        type=Path,
        default=None,
        help=(
            "Path to PEM private key (overrides SPECFACT_MODULE_PRIVATE_SIGN_KEY_FILE). "
            "Supported keys: Ed25519 and RSA."
        ),
    )
    parser.add_argument(
        "--passphrase", default="", help="Passphrase for encrypted private key (discouraged in shell history)"
    )
    parser.add_argument(
        "--passphrase-stdin",
        action="store_true",
        help="Read private-key passphrase from stdin (for secure piping/CI use)",
    )
    parser.add_argument(
        "--allow-unsigned",
        action="store_true",
        help="Allow checksum-only signing without private key (local testing only).",
    )
    parser.add_argument(
        "--payload-from-filesystem",
        action="store_true",
        help="Build payload from filesystem (rglob) with same excludes as publish tarball, so checksum matches install verification.",
    )
    parser.add_argument(
        "--allow-same-version",
        action="store_true",
        help="Bypass version-bump enforcement for changed module contents (not recommended).",
    )
    parser.add_argument(
        "--changed-only",
        action="store_true",
        help="Select only manifests whose module payload changed since --base-ref.",
    )
    parser.add_argument(
        "--base-ref",
        default="HEAD",
        help="Git ref used for change detection when --changed-only is set (default: HEAD).",
    )
    parser.add_argument(
        "--bump-version",
        choices=("patch", "minor", "major"),
        default="",
        help="Auto-bump changed module version when unchanged from --base-ref before signing.",
    )
    parser.add_argument("manifests", nargs="*", help="module-package.yaml path(s)")
    args = parser.parse_args()

    passphrase = _resolve_passphrase(args)
    try:
        private_key = _load_private_key(
            args.key_file,
            passphrase=passphrase,
            prompt_for_passphrase=sys.stdin.isatty() and not args.passphrase_stdin,
        )
    except ValueError as exc:
        parser.error(str(exc))
    if private_key is None and not args.allow_unsigned:
        parser.error(
            "No signing key provided. Use --key-file <path> (recommended) "
            "or set SPECFACT_MODULE_PRIVATE_SIGN_KEY / SPECFACT_MODULE_PRIVATE_SIGN_KEY_FILE. "
            "For local testing only, re-run with --allow-unsigned."
        )
    return _sign_requested_manifests(args, parser, private_key)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    raise SystemExit(main())
