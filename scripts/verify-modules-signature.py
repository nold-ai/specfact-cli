#!/usr/bin/env python3
"""Verify bundled module checksums/signatures against full module payload."""

from __future__ import annotations

import argparse
import base64
import hashlib
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, cast

import yaml
from beartype import beartype
from icontract import ensure, require


logger = logging.getLogger(__name__)


_IGNORED_MODULE_DIR_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "logs", "tests"}
_IGNORED_MODULE_FILE_SUFFIXES = {".pyc", ".pyo"}
_PAYLOAD_FROM_FS_IGNORED_DIRS = _IGNORED_MODULE_DIR_NAMES | {".git"}


def _canonical_manifest_payload(manifest_data: dict[str, Any]) -> bytes:
    payload = dict(manifest_data)
    payload.pop("integrity", None)
    return yaml.safe_dump(payload, sort_keys=True, allow_unicode=False).encode("utf-8")


def _path_is_hashable_module_file(
    path: Path,
    module_dir_resolved: Path,
    ignored_dirs: set[str],
) -> bool:
    rel = path.resolve().relative_to(module_dir_resolved)
    if any(part in ignored_dirs for part in rel.parts):
        return False
    return path.suffix.lower() not in _IGNORED_MODULE_FILE_SUFFIXES


def _sort_module_paths_key(module_dir_resolved: Path):
    return lambda p: cast(Path, p).resolve().relative_to(module_dir_resolved).as_posix()


def _list_module_files_git_tracked(module_dir: Path, module_dir_resolved: Path, ignored_dirs: set[str]) -> list[Path]:
    listed = subprocess.run(
        ["git", "ls-files", module_dir.as_posix()],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    git_files = [Path.cwd() / line.strip() for line in listed if line.strip()]
    return sorted(
        (
            path
            for path in git_files
            if path.is_file() and _path_is_hashable_module_file(path, module_dir_resolved, ignored_dirs)
        ),
        key=_sort_module_paths_key(module_dir_resolved),
    )


def _list_module_files_from_filesystem(
    module_dir: Path, module_dir_resolved: Path, ignored_dirs: set[str]
) -> list[Path]:
    return sorted(
        (
            path
            for path in module_dir.rglob("*")
            if path.is_file() and _path_is_hashable_module_file(path, module_dir_resolved, ignored_dirs)
        ),
        key=_sort_module_paths_key(module_dir_resolved),
    )


def _collect_module_file_list(
    module_dir: Path, module_dir_resolved: Path, payload_from_filesystem: bool, ignored_dirs: set[str]
) -> list[Path]:
    if payload_from_filesystem:
        return _list_module_files_from_filesystem(module_dir, module_dir_resolved, ignored_dirs)
    try:
        return _list_module_files_git_tracked(module_dir, module_dir_resolved, ignored_dirs)
    except Exception:
        return _list_module_files_from_filesystem(module_dir, module_dir_resolved, ignored_dirs)


def _digest_bytes_for_module_path(path: Path, rel: str) -> bytes:
    if rel in {"module-package.yaml", "metadata.yaml"}:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(f"Invalid manifest YAML: {path}")
        return _canonical_manifest_payload(raw)
    return path.read_bytes()


def _module_payload(module_dir: Path, payload_from_filesystem: bool = False) -> bytes:
    module_dir_resolved = module_dir.resolve()
    ignored_dirs = _PAYLOAD_FROM_FS_IGNORED_DIRS if payload_from_filesystem else _IGNORED_MODULE_DIR_NAMES
    files = _collect_module_file_list(module_dir, module_dir_resolved, payload_from_filesystem, ignored_dirs)
    entries: list[str] = []
    for path in files:
        rel = path.resolve().relative_to(module_dir_resolved).as_posix()
        data = _digest_bytes_for_module_path(path, rel)
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
    data = cast(dict[str, Any], raw)
    value = data.get("version")
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
    data = cast(dict[str, Any], raw)
    value = data.get("version")
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


def _manifest_path_for_git_diff_line(parts: tuple[str, ...]) -> Path | None:
    """Map a changed path under modules trees to its module-package.yaml, if applicable."""
    if len(parts) >= 4 and parts[0] == "src" and parts[1] == "specfact_cli" and parts[2] == "modules":
        return Path(*parts[:4]) / "module-package.yaml"
    if len(parts) >= 2 and parts[0] == "modules":
        return Path(*parts[:2]) / "module-package.yaml"
    return None


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
        manifest = _manifest_path_for_git_diff_line(tuple(changed_path.parts))
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


@beartype
@require(lambda manifest_path: cast(Path, manifest_path).exists(), "manifest_path must exist")
@ensure(lambda result: result is None, "verification raises or returns None")
def verify_manifest(
    manifest_path: Path,
    *,
    require_signature: bool,
    public_key_pem: str,
    payload_from_filesystem: bool = False,
    verify_checksum: bool = True,
) -> None:
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("manifest YAML must be object")
    data = cast(dict[str, Any], raw)
    integrity_raw = data.get("integrity")
    if not isinstance(integrity_raw, dict):
        raise ValueError("missing integrity metadata")
    integrity = cast(dict[str, Any], integrity_raw)

    checksum = str(integrity.get("checksum", "")).strip()
    if not checksum:
        raise ValueError("missing integrity.checksum")
    algo, digest = _parse_checksum(checksum)
    if not verify_checksum:
        if require_signature:
            raise ValueError("require_signature is incompatible with verify_checksum=False")
        return

    payload = _module_payload(manifest_path.parent, payload_from_filesystem=payload_from_filesystem)
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


@beartype
@ensure(lambda result: result >= 0, "exit code must be non-negative")
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
        "--payload-from-filesystem",
        action="store_true",
        help="Build payload from filesystem (rglob) with the same excludes as the signing path.",
    )
    parser.add_argument(
        "--skip-checksum-verification",
        action="store_true",
        help="Skip payload checksum (and signature) checks; use with --enforce-version-bump on non-main "
        "when CI will re-sign. Incompatible with --require-signature.",
    )
    parser.add_argument(
        "--version-check-base",
        default="",
        help="Git base ref for version-bump checks (default: origin/$GITHUB_BASE_REF or HEAD~1)",
    )
    args = parser.parse_args()
    if args.require_signature and args.skip_checksum_verification:
        parser.error("--skip-checksum-verification cannot be used with --require-signature")

    public_key_pem = _resolve_public_key(args)
    verify_checksum = not args.skip_checksum_verification
    manifests = _iter_manifests()
    if not manifests:
        logger.info("No module-package.yaml manifests found.")
        return 0

    failures: list[str] = []
    for manifest in manifests:
        try:
            verify_manifest(
                manifest,
                require_signature=args.require_signature,
                public_key_pem=public_key_pem,
                payload_from_filesystem=args.payload_from_filesystem,
                verify_checksum=verify_checksum,
            )
            logger.info("OK  %s", manifest)
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
        for line in failures:
            logger.error("%s", line)
        for line in version_failures:
            logger.error("%s", line)
        return 1

    logger.info("Verified %d module manifest(s).", len(manifests))
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    raise SystemExit(main())
