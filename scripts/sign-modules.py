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


def _canonical_payload(manifest_data: dict[str, Any]) -> bytes:
    payload = dict(manifest_data)
    payload.pop("integrity", None)
    return yaml.safe_dump(payload, sort_keys=True, allow_unicode=False).encode("utf-8")


def _module_payload(module_dir: Path) -> bytes:
    if not module_dir.exists() or not module_dir.is_dir():
        msg = f"Module directory not found: {module_dir}"
        raise ValueError(msg)
    entries: list[str] = []
    files = sorted(
        (path for path in module_dir.rglob("*") if path.is_file()),
        key=lambda p: p.relative_to(module_dir).as_posix(),
    )
    for path in files:
        rel = path.relative_to(module_dir).as_posix()
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


def _read_manifest_version_from_git(head_ref: str, path: Path) -> str | None:
    try:
        output = subprocess.run(
            ["git", "show", f"{head_ref}:{path.as_posix()}"],
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


def _module_has_git_changes(module_dir: Path) -> bool:
    try:
        changed = subprocess.run(
            ["git", "diff", "--name-only", "HEAD", "--", module_dir.as_posix()],
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


def _enforce_version_bump_before_signing(manifest_path: Path, *, allow_same_version: bool) -> None:
    if allow_same_version:
        return

    current_version = _read_manifest_version(manifest_path)
    if not current_version:
        raise ValueError(f"Manifest missing version: {manifest_path}")

    previous_version = _read_manifest_version_from_git("HEAD", manifest_path)
    if previous_version is None:
        return
    if current_version != previous_version:
        return

    module_dir = manifest_path.parent
    if not _module_has_git_changes(module_dir):
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
    manifest_path.write_text(
        yaml.safe_dump(
            raw,
            sort_keys=False,
            allow_unicode=False,
            default_flow_style=False,
            indent=2,
        ),
        encoding="utf-8",
    )

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
    parser.add_argument("manifests", nargs="+", help="module-package.yaml path(s)")
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

    for manifest in args.manifests:
        try:
            manifest_path = Path(manifest)
            _enforce_version_bump_before_signing(
                manifest_path,
                allow_same_version=args.allow_same_version,
            )
            sign_manifest(manifest_path, private_key)
        except ValueError as exc:
            parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
