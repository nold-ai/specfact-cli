#!/usr/bin/env python3
"""Verify bundled module checksums/signatures against full module payload."""

from __future__ import annotations

import argparse
import base64
import hashlib
import os
import subprocess
from pathlib import Path
from typing import Any

import yaml


_IGNORED_MODULE_DIR_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "logs"}
_IGNORED_MODULE_FILE_SUFFIXES = {".pyc", ".pyo"}


def _canonical_manifest_payload(manifest_data: dict[str, Any]) -> bytes:
    payload = dict(manifest_data)
    payload.pop("integrity", None)
    return yaml.safe_dump(payload, sort_keys=True, allow_unicode=False).encode("utf-8")


def _module_payload(module_dir: Path) -> bytes:
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
                raise ValueError(f"Invalid manifest YAML: {path}")
            data = _canonical_manifest_payload(raw)
        else:
            data = path.read_bytes()
        entries.append(f"{rel}:{hashlib.sha256(data).hexdigest()}")
    return "\n".join(entries).encode("utf-8")


def _parse_checksum(checksum: str) -> tuple[str, str]:
    if ":" not in checksum:
        raise ValueError("Checksum must be in algo:hex format")
    algo, digest = checksum.split(":", 1)
    algo = algo.strip().lower()
    digest = digest.strip().lower()
    if algo not in {"sha256", "sha384", "sha512"}:
        raise ValueError(f"Unsupported checksum algorithm: {algo}")
    if not digest:
        raise ValueError("Checksum digest is empty")
    return algo, digest


def _verify_signature(payload: bytes, signature_b64: str, public_key_pem: str) -> None:
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519, padding, rsa
    except Exception as exc:
        raise ValueError(
            "cryptography backend missing; install with `python3 -m pip install cryptography cffi`"
        ) from exc

    public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
    signature = base64.b64decode(signature_b64, validate=True)

    try:
        if isinstance(public_key, rsa.RSAPublicKey):
            public_key.verify(signature, payload, padding.PKCS1v15(), hashes.SHA256())
            return
        if isinstance(public_key, ed25519.Ed25519PublicKey):
            public_key.verify(signature, payload)
            return
    except InvalidSignature as exc:
        raise ValueError("Signature validation failed") from exc
    raise ValueError("Unsupported public key type (RSA or Ed25519 required)")


def _resolve_public_key(args: argparse.Namespace) -> str:
    if args.public_key_file:
        return Path(args.public_key_file).read_text(encoding="utf-8").strip()
    env_key = (args.public_key_pem or "").strip()
    if env_key:
        return env_key
    default_paths = [
        Path("resources/keys/module-signing-public.pem"),
        Path("src/specfact_cli/resources/keys/module-signing-public.pem"),
    ]
    for default_path in default_paths:
        if default_path.exists():
            return default_path.read_text(encoding="utf-8").strip()
    return ""


def _iter_manifests() -> list[Path]:
    roots = [Path("src/specfact_cli/modules"), Path("modules")]
    manifests: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        manifests.extend(sorted(root.rglob("module-package.yaml")))
    return manifests


def _read_manifest_version(path: Path) -> str | None:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return None
    value = raw.get("version")
    if value is None:
        return None
    version = str(value).strip()
    return version or None


def _read_manifest_version_from_git(ref: str, manifest_path: Path) -> str | None:
    try:
        output = subprocess.run(
            ["git", "show", f"{ref}:{manifest_path.as_posix()}"],
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


def _resolve_version_check_base(explicit_base: str | None) -> str:
    if explicit_base and explicit_base.strip():
        return explicit_base.strip()

    env_base_ref = (os.environ.get("GITHUB_BASE_REF", "") or "").strip()
    if env_base_ref:
        return f"origin/{env_base_ref}"
    return "HEAD~1"


def _changed_manifests_from_git(base_ref: str) -> list[Path]:
    try:
        output = subprocess.run(
            [
                "git",
                "diff",
                "--name-only",
                f"{base_ref}...HEAD",
                "--",
                "src/specfact_cli/modules",
                "modules",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception as exc:
        raise ValueError(f"Unable to diff manifests against base ref '{base_ref}': {exc}") from exc

    manifests: list[Path] = []
    seen: set[Path] = set()
    for line in output.stdout.splitlines():
        changed_path = Path(line.strip())
        if not changed_path:
            continue
        parts = changed_path.parts
        manifest: Path | None = None
        if len(parts) >= 4 and parts[0] == "src" and parts[1] == "specfact_cli" and parts[2] == "modules":
            manifest = Path(*parts[:4]) / "module-package.yaml"
        elif len(parts) >= 2 and parts[0] == "modules":
            manifest = Path(*parts[:2]) / "module-package.yaml"
        if manifest and manifest.exists() and manifest not in seen:
            manifests.append(manifest)
            seen.add(manifest)
    return manifests


def _verify_version_bumps(base_ref: str) -> list[str]:
    failures: list[str] = []
    for manifest in _changed_manifests_from_git(base_ref):
        current_version = _read_manifest_version(manifest)
        previous_version = _read_manifest_version_from_git(base_ref, manifest)
        if not current_version or not previous_version:
            continue
        if current_version == previous_version:
            failures.append(
                f"FAIL {manifest}: module version was not incremented (still {current_version}) compared to {base_ref}"
            )
    return failures


def verify_manifest(manifest_path: Path, *, require_signature: bool, public_key_pem: str) -> None:
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("manifest YAML must be object")
    integrity = raw.get("integrity")
    if not isinstance(integrity, dict):
        raise ValueError("missing integrity metadata")

    checksum = str(integrity.get("checksum", "")).strip()
    if not checksum:
        raise ValueError("missing integrity.checksum")
    algo, digest = _parse_checksum(checksum)
    payload = _module_payload(manifest_path.parent)
    actual = hashlib.new(algo, payload).hexdigest().lower()
    if actual != digest:
        raise ValueError("checksum mismatch")

    signature = str(integrity.get("signature", "")).strip()
    if require_signature and not signature:
        raise ValueError("missing integrity.signature")
    if signature:
        if not public_key_pem:
            raise ValueError("public key required to verify signature")
        _verify_signature(payload, signature, public_key_pem)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-signature", action="store_true", help="Require integrity.signature for every manifest"
    )
    parser.add_argument("--public-key-file", default="", help="Path to PEM public key")
    parser.add_argument(
        "--public-key-pem",
        default="",
        help="Inline PEM public key content (optional; fallback after --public-key-file)",
    )
    parser.add_argument(
        "--enforce-version-bump",
        action="store_true",
        help="Fail when changed module manifests keep the same version as base ref",
    )
    parser.add_argument(
        "--version-check-base",
        default="",
        help="Git base ref for version-bump checks (default: origin/$GITHUB_BASE_REF or HEAD~1)",
    )
    args = parser.parse_args()

    public_key_pem = _resolve_public_key(args)
    manifests = _iter_manifests()
    if not manifests:
        print("No module-package.yaml manifests found.")
        return 0

    failures: list[str] = []
    for manifest in manifests:
        try:
            verify_manifest(manifest, require_signature=args.require_signature, public_key_pem=public_key_pem)
            print(f"OK  {manifest}")
        except Exception as exc:
            failures.append(f"FAIL {manifest}: {exc}")

    version_failures: list[str] = []
    if args.enforce_version_bump:
        base_ref = _resolve_version_check_base(args.version_check_base)
        try:
            version_failures = _verify_version_bumps(base_ref)
        except ValueError as exc:
            version_failures.append(f"FAIL version-check: {exc}")

    if failures or version_failures:
        if failures:
            print("\n".join(failures))
        if version_failures:
            print("\n".join(version_failures))
        return 1

    print(f"Verified {len(manifests)} module manifest(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
