#!/usr/bin/env python3
"""Sign SpecFact module manifests with checksum/signature over full module payload."""

from __future__ import annotations

import argparse
import base64
import getpass
import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


_IGNORED_MODULE_DIR_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "logs"}
_IGNORED_MODULE_FILE_SUFFIXES = {".pyc", ".pyo"}


class _IndentedSafeDumper(yaml.SafeDumper):
    """Safe dumper that indents sequence items under their parent key."""

    def increase_indent(self, flow: bool = False, indentless: bool = False):
        return super().increase_indent(flow=flow, indentless=False)


def _canonical_payload(manifest_data: dict[str, Any]) -> bytes:
    payload = dict(manifest_data)
    payload.pop("integrity", None)
    return yaml.safe_dump(payload, sort_keys=True, allow_unicode=False).encode("utf-8")


def _module_payload(module_dir: Path) -> bytes:
    if not module_dir.exists() or not module_dir.is_dir():
        msg = f"Module directory not found: {module_dir}"
        raise ValueError(msg)
    module_dir_resolved = module_dir.resolve()

    def _is_hashable(path: Path) -> bool:
        rel = path.resolve().relative_to(module_dir_resolved)
        if any(part in _IGNORED_MODULE_DIR_NAMES for part in rel.parts):
            return False
        return path.suffix.lower() not in _IGNORED_MODULE_FILE_SUFFIXES

    entries: list[str] = []

    files: list[Path]
    try:
        listed = subprocess.run(
            ["git", "ls-files", module_dir.as_posix()],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        git_files = [(Path.cwd() / line.strip()) for line in listed if line.strip()]
        files = sorted(
            (path for path in git_files if path.is_file() and _is_hashable(path)),
            key=lambda p: p.resolve().relative_to(module_dir_resolved).as_posix(),
        )
    except Exception:
        files = sorted(
            (path for path in module_dir.rglob("*") if path.is_file() and _is_hashable(path)),
            key=lambda p: p.resolve().relative_to(module_dir_resolved).as_posix(),
        )

    for path in files:
        rel = path.resolve().relative_to(module_dir_resolved).as_posix()
        if rel in {"module-package.yaml", "metadata.yaml"}:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                msg = f"Invalid manifest YAML: {path}"
                raise ValueError(msg)
            data = _canonical_payload(raw)
        else:
            data = path.read_bytes()
        entries.append(f"{rel}:{hashlib.sha256(data).hexdigest()}")
    return "\n".join(entries).encode("utf-8")


def _load_private_key(
    key_file: Path | None = None,
    *,
    passphrase: str | None = None,
    prompt_for_passphrase: bool = False,
) -> Any | None:
    pem = os.environ.get("SPECFACT_MODULE_PRIVATE_SIGN_KEY", "").strip()
    if not pem:
        pem = os.environ.get("SPECFACT_MODULE_SIGNING_PRIVATE_KEY_PEM", "").strip()
    configured_file = os.environ.get("SPECFACT_MODULE_PRIVATE_SIGN_KEY_FILE", "").strip()
    if not configured_file:
        configured_file = os.environ.get("SPECFACT_MODULE_SIGNING_PRIVATE_KEY_FILE", "").strip()
    effective_file = key_file or (Path(configured_file) if configured_file else None)
    if not pem and effective_file:
        pem = effective_file.read_text(encoding="utf-8")
    if not pem:
        return None

    try:
        from cryptography.hazmat.primitives import serialization
    except Exception as exc:
        raise ValueError(
            "Unable to import cryptography backend for signing. "
            "Install signing dependencies (`python3 -m pip install cryptography cffi`) "
            "or run via project environment (`hatch run python scripts/sign-modules.py ...`)."
        ) from exc

    password_bytes = passphrase.encode("utf-8") if passphrase is not None else None

    try:
        return serialization.load_pem_private_key(pem.encode("utf-8"), password=password_bytes)
    except Exception as exc:
        message = str(exc).lower()
        needs_password = "password was not given" in message or "private key is encrypted" in message
        if needs_password and prompt_for_passphrase:
            prompted = getpass.getpass("Enter signing key passphrase: ")
            try:
                return serialization.load_pem_private_key(
                    pem.encode("utf-8"),
                    password=prompted.encode("utf-8"),
                )
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
    value = raw.get("version")
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
    value = raw.get("version")
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
    print(f"{manifest_path}: version {current_version} -> {bumped}")
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


def sign_manifest(manifest_path: Path, private_key: Any | None) -> None:
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        msg = f"Invalid manifest YAML: {manifest_path}"
        raise ValueError(msg)

    payload = _module_payload(manifest_path.parent)
    checksum = f"sha256:{hashlib.sha256(payload).hexdigest()}"
    integrity: dict[str, str] = {"checksum": checksum}

    if private_key is not None:
        integrity["signature"] = _sign_payload(payload, private_key)

    raw["integrity"] = integrity
    _write_manifest(manifest_path, raw)

    status = "checksum+signature" if "signature" in integrity else "checksum"
    print(f"{manifest_path}: {status}")


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

    manifests: list[Path]
    if args.manifests:
        manifests = [Path(manifest) for manifest in args.manifests]
    elif args.changed_only:
        manifests = [
            manifest for manifest in _iter_manifests() if _module_has_git_changes_since(manifest.parent, args.base_ref)
        ]
    else:
        parser.error("Provide one or more manifests, or use --changed-only.")

    if args.changed_only and not manifests:
        print(f"No changed module manifests detected since {args.base_ref}.")
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
            sign_manifest(manifest_path, private_key)
        except ValueError as exc:
            parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
