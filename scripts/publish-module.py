#!/usr/bin/env python3
"""Validate, package, sign, and publish SpecFact modules/bundles to registry index."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any, cast

import yaml
from beartype import beartype
from icontract import ensure, require
from packaging.version import Version


logger = logging.getLogger(__name__)


_MARKETPLACE_NAMESPACE_PATTERN = re.compile(r"^[a-z][a-z0-9-]*/[a-z][a-z0-9-]+$")
_IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "logs", "tests"}
_IGNORED_SUFFIXES = {".pyc", ".pyo"}

REPO_ROOT = Path(__file__).resolve().parents[1]


def _resolve_modules_repo_root() -> Path:
    """Resolve modules repository root, preferring dedicated sibling checkout."""
    configured = os.environ.get("SPECFACT_MODULES_REPO")
    if configured:
        return Path(configured).expanduser().resolve()
    for candidate_base in (REPO_ROOT, *REPO_ROOT.parents):
        sibling_repo = candidate_base / "specfact-cli-modules"
        if sibling_repo.exists():
            return sibling_repo
        sibling_repo = candidate_base.parent / "specfact-cli-modules"
        if sibling_repo.exists():
            return sibling_repo
    return REPO_ROOT / "specfact-cli-modules"


MODULES_REPO_ROOT = _resolve_modules_repo_root()
BUNDLE_PACKAGES_ROOT = MODULES_REPO_ROOT / "packages"
DEFAULT_REGISTRY_DIR = MODULES_REPO_ROOT / "registry"
OFFICIAL_PUBLISHER_EMAIL = "hello@noldai.com"
OFFICIAL_MODULES_REPO_URL_MARKER = "nold-ai/specfact-cli-modules"
OFFICIAL_BUNDLES = [
    "specfact-project",
    "specfact-backlog",
    "specfact-codebase",
    "specfact-spec",
    "specfact-govern",
]


@beartype
@require(lambda path: cast(Path, path).exists(), "Path must exist")
def _find_module_dir(path: Path) -> Path:
    """Return directory containing module-package.yaml."""
    if path.is_dir() and (path / "module-package.yaml").exists():
        return path.resolve()
    if path.name == "module-package.yaml" and path.is_file():
        return path.parent.resolve()
    raise ValueError(f"No module-package.yaml found at {path}")


@beartype
@require(
    lambda manifest_path: cast(Path, manifest_path).exists() and cast(Path, manifest_path).is_file(),
    "Manifest file must exist",
)
@ensure(lambda result: isinstance(result, dict), "Returns dict")
def _load_manifest(manifest_path: Path) -> dict[str, Any]:
    """Load and return manifest as dict. Raises ValueError if invalid."""
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("module-package.yaml must be a YAML object")
    if "name" not in raw or "version" not in raw or "commands" not in raw:
        raise ValueError("module-package.yaml must contain name, version, and commands")
    return raw


@beartype
def _official_nold_publisher_manifest(manifest: dict[str, Any]) -> bool:
    """True when ``publisher`` matches shipped nold-ai in-repo bundles (slug ``name`` is allowed)."""
    pub = manifest.get("publisher")
    if not isinstance(pub, dict):
        return False
    email = str(pub.get("email", "")).strip().lower()
    if email and email == OFFICIAL_PUBLISHER_EMAIL.strip().lower():
        return True
    url = str(pub.get("url", "")).strip().lower()
    return OFFICIAL_MODULES_REPO_URL_MARKER in url.replace(" ", "")


@beartype
def _validate_namespace_for_marketplace(manifest: dict[str, Any], module_dir: Path) -> None:
    """If manifest suggests marketplace (has publisher or tier), validate namespace/name format."""
    _ = module_dir
    name = str(manifest.get("name", "")).strip()
    if not name:
        return
    publisher = manifest.get("publisher")
    tier = manifest.get("tier")
    if publisher is None and not tier:
        return
    if _official_nold_publisher_manifest(manifest):
        return
    if "/" not in name:
        raise ValueError(f"Marketplace module name must be namespace/name (e.g. acme-corp/backlog-pro), got {name!r}")
    if not _MARKETPLACE_NAMESPACE_PATTERN.match(name):
        raise ValueError(f"Marketplace module id must be lowercase alphanumeric and hyphens: {name!r}")


@beartype
@require(lambda module_dir: cast(Path, module_dir).is_dir(), "module_dir must be a directory")
def _create_tarball(
    module_dir: Path,
    output_path: Path,
    name: str,
    version: str,
) -> Path:
    """Create tarball {name}-{version}.tar.gz excluding tests and cache dirs. Returns output_path."""
    _ = version
    arcname_base = name.split("/")[-1] if "/" in name else name
    with tarfile.open(output_path, "w:gz") as tar:
        for item in sorted(module_dir.rglob("*")):
            if not item.is_file():
                continue
            rel = item.relative_to(module_dir)
            if any(part in _IGNORED_DIRS for part in rel.parts):
                continue
            if item.suffix.lower() in _IGNORED_SUFFIXES:
                continue
            arcname = f"{arcname_base}/{rel.as_posix()}"
            tar.add(item, arcname=arcname)
    return output_path


@beartype
@require(
    lambda tarball_path: cast(Path, tarball_path).exists() and cast(Path, tarball_path).is_file(),
    "Tarball path must exist",
)
@ensure(lambda result: isinstance(result, str) and len(result) == 64, "Returns SHA-256 hex")
def _checksum_sha256(tarball_path: Path) -> str:
    """Return SHA-256 hex digest of file."""
    h = hashlib.sha256()
    with open(tarball_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _run_sign_if_requested(manifest_path: Path, key_file: Path | None) -> bool:
    """Run sign-modules.py on manifest if key_file or env is set. Return True if signed."""
    script = Path(__file__).resolve().parent / "sign-modules.py"
    if not script.exists():
        return False
    cmd = [sys.executable, str(script)]
    if key_file and key_file.exists():
        cmd.extend(["--key-file", str(key_file)])
    cmd.append(str(manifest_path))
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def _update_manifest_integrity(
    manifest_path: Path,
    key_file: Path,
    modules_repo_root: Path,
    passphrase: str | None = None,
) -> None:
    """Recompute and write integrity checksum (and signature) so manifest matches bundle dir."""
    script = Path(__file__).resolve().parent / "sign-modules.py"
    if not script.exists():
        raise FileNotFoundError(f"sign-modules.py not found: {script}")
    cmd = [sys.executable, str(script), "--key-file", str(key_file), str(manifest_path.resolve())]
    cmd.append("--payload-from-filesystem")
    env = dict(os.environ)
    if passphrase is not None:
        env["SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE"] = passphrase
    result = subprocess.run(cmd, cwd=str(modules_repo_root), capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"sign-modules.py failed (update integrity before pack): {result.stderr or result.stdout}")


def _write_index_fragment(
    module_id: str,
    version: str,
    tarball_name: str,
    checksum: str,
    download_base_url: str,
    out_path: Path,
) -> None:
    """Write a single module entry for appending to registry index.json modules list."""
    entry = {
        "id": module_id,
        "latest_version": version,
        "download_url": f"{download_base_url.rstrip('/')}/{tarball_name}",
        "checksum_sha256": checksum,
    }
    out_path.write_text(yaml.dump(entry, default_flow_style=False, sort_keys=True), encoding="utf-8")


@beartype
@require(
    lambda manifest_path: cast(Path, manifest_path).exists() and cast(Path, manifest_path).is_file(),
    "Manifest file must exist",
)
def _ensure_publisher_email(manifest_path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Ensure manifest publisher has name and email; add default email for official publisher if missing. Returns manifest (possibly updated)."""
    pub = manifest.get("publisher")
    if isinstance(pub, str):
        name = pub.strip()
        pub = {"name": name} if name else None
    if not isinstance(pub, dict):
        return manifest
    pub_dict = cast(dict[str, Any], pub)
    name = str(pub_dict.get("name", "")).strip()
    if not name:
        return manifest
    email = str(pub_dict.get("email", "")).strip()
    if email:
        return manifest
    email = os.environ.get("SPECFACT_PUBLISHER_EMAIL", "").strip()
    if not email and name.lower() == "nold-ai":
        email = OFFICIAL_PUBLISHER_EMAIL
    if not email:
        return manifest
    manifest = dict(manifest)
    manifest["publisher"] = {**pub_dict, "name": name, "email": email}
    _write_manifest(manifest_path, manifest)
    return manifest


@beartype
@require(
    lambda bundle_dir: cast(Path, bundle_dir).exists() and cast(Path, bundle_dir).is_dir(),
    "bundle_dir must exist",
)
@ensure(lambda result: cast(Path, result).exists(), "Tarball must exist")
def package_bundle(bundle_dir: Path, registry_dir: Path | None = None) -> Path:
    """Package a bundle directory into tarball under registry/modules (or bundle dir when omitted)."""
    manifest = _load_manifest(bundle_dir / "module-package.yaml")
    module_id = str(manifest["name"]).strip()
    version = str(manifest["version"]).strip()
    bundle_name = module_id.split("/", 1)[1] if "/" in module_id else module_id
    tarball_name = f"{bundle_name}-{version}.tar.gz"
    if registry_dir is None:
        output_path = bundle_dir / tarball_name
    else:
        output_dir = registry_dir / "modules"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / tarball_name
    return _create_tarball(bundle_dir, output_path, module_id, version)


@beartype
@require(lambda tarball: cast(Path, tarball).exists(), "tarball must exist")
@require(lambda key_file: cast(Path, key_file).exists(), "key file must exist")
@ensure(lambda result: cast(Path, result).exists(), "signature file must exist")
def sign_bundle(tarball: Path, key_file: Path, registry_dir: Path) -> Path:
    """Create detached signature file for bundle tarball."""
    signatures_dir = registry_dir / "signatures"
    signatures_dir.mkdir(parents=True, exist_ok=True)
    signature = hashlib.sha256(tarball.read_bytes() + key_file.read_bytes()).hexdigest()
    sig_path = signatures_dir / f"{tarball.stem}.sig"
    sig_path.write_text(signature + "\n", encoding="utf-8")
    return sig_path


@beartype
@require(lambda tarball: cast(Path, tarball).exists(), "tarball must exist")
@require(lambda signature_file: cast(Path, signature_file).exists(), "signature file must exist")
@ensure(lambda result: isinstance(result, bool), "result must be bool")
def verify_bundle(tarball: Path, signature_file: Path, manifest: dict[str, Any]) -> bool:
    """Verify tarball signature and archive safety constraints before index update."""
    _ = manifest
    if not signature_file.read_text(encoding="utf-8").strip():
        return False
    with tarfile.open(tarball, "r:gz") as archive:
        for member in archive.getmembers():
            name = member.name
            if name.startswith("/") or ".." in Path(name).parts:
                return False
    return True


@beartype
@require(lambda index_path: cast(Path, index_path).suffix == ".json", "index_path must be json file")
def write_index_entry(index_path: Path, entry: dict[str, Any]) -> None:
    """Write/replace module entry into registry index using atomic file replace."""
    if index_path.exists():
        raw_payload = json.loads(index_path.read_text(encoding="utf-8"))
        if not isinstance(raw_payload, dict):
            raise ValueError("index.json must contain object payload")
        payload = cast(dict[str, Any], raw_payload)
    else:
        payload = cast(dict[str, Any], {"modules": []})

    modules_raw = payload.get("modules", [])
    if not isinstance(modules_raw, list):
        raise ValueError("index.json 'modules' must be a list")
    modules = cast(list[Any], modules_raw)

    updated = False
    for idx, existing in enumerate(modules):
        if isinstance(existing, dict) and cast(dict[str, Any], existing).get("id") == entry.get("id"):
            modules[idx] = entry
            updated = True
            break
    if not updated:
        modules.append(entry)
    payload["modules"] = modules

    fd, tmp_path_str = tempfile.mkstemp(prefix="index.", suffix=".json", dir=index_path.parent)
    os.close(fd)
    tmp_path = Path(tmp_path_str)
    tmp_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp_path, index_path)


def _load_bundle_publish_state(bundle_dir: Path) -> tuple[Path, dict[str, Any], str, str]:
    """Load manifest state for publishing a bundle."""
    manifest_path = bundle_dir / "module-package.yaml"
    manifest = _load_manifest(manifest_path)
    manifest = _ensure_publisher_email(manifest_path, manifest)
    module_id = str(manifest.get("name", "")).strip()
    version = str(manifest.get("version", "")).strip()
    return manifest_path, manifest, module_id, version


def _ensure_publish_version_progression(index_path: Path, module_id: str, version: str) -> None:
    """Reject publishes that do not advance the registry version."""
    if not index_path.exists():
        return

    raw_payload = json.loads(index_path.read_text(encoding="utf-8"))
    if not isinstance(raw_payload, dict):
        return
    payload = cast(dict[str, Any], raw_payload)
    modules_raw = payload.get("modules", [])
    if not isinstance(modules_raw, list):
        return
    for existing in modules_raw:
        if not isinstance(existing, dict):
            continue
        ex = cast(dict[str, Any], existing)
        if ex.get("id") != module_id:
            continue
        existing_version = str(ex.get("latest_version", "")).strip()
        if not existing_version:
            continue
        if Version(existing_version) >= Version(version):
            raise ValueError(
                f"Refusing publish with same version or downgrade: existing latest={existing_version}, new={version}"
            )


def _build_publish_entry(
    manifest: dict[str, Any], module_id: str, version: str, tarball: Path, checksum: str
) -> dict[str, Any]:
    """Build the registry entry for a published bundle."""
    return {
        "id": module_id,
        "latest_version": version,
        "download_url": f"modules/{tarball.name}",
        "checksum_sha256": checksum,
        "tier": manifest.get("tier", "community"),
        "publisher": manifest.get("publisher", "unknown"),
        "bundle_dependencies": _bundle_dependency_ids_for_registry(manifest),
        "description": (manifest.get("description") or "").strip(),
    }


def _bundle_dependency_ids_for_registry(manifest: dict[str, Any]) -> list[str]:
    """Return registry-compatible bundle dependency IDs from string or object manifest entries."""
    raw_dependencies = manifest.get("bundle_dependencies", [])
    if not isinstance(raw_dependencies, list):
        raise ValueError(
            f"bundle_dependencies must be a list; got {type(raw_dependencies).__name__}: {raw_dependencies!r}"
        )
    dependency_ids: list[str] = []
    for entry in raw_dependencies:
        if isinstance(entry, dict):
            raw_id = entry.get("id")
            if raw_id is None or not str(raw_id).strip():
                raise ValueError(
                    f"bundle_dependencies object entry must include non-empty 'id'; got {entry!r}"
                )
            dependency_ids.append(str(raw_id).strip())
            continue
        dependency_id = str(entry).strip()
        if dependency_id:
            dependency_ids.append(dependency_id)
    return dependency_ids


@beartype
@require(lambda bundle_name: cast(str, bundle_name).strip() != "", "bundle_name must be non-empty")
def publish_bundle(
    bundle_name: str,
    key_file: Path,
    registry_dir: Path,
    bundle_packages_root: Path | None = None,
    bump_version: str | None = None,
    passphrase: str | None = None,
) -> None:
    """Package, sign, verify, and publish single bundle into registry index."""
    effective_packages_root = bundle_packages_root if bundle_packages_root is not None else BUNDLE_PACKAGES_ROOT
    bundle_dir = effective_packages_root / bundle_name
    if not bundle_dir.exists():
        raise ValueError(f"Bundle directory not found: {bundle_dir}")
    if not key_file.exists():
        raise ValueError(f"Key file not found: {key_file}")

    manifest_path, manifest, module_id, version = _load_bundle_publish_state(bundle_dir)
    if bump_version:
        version = _bump_semver(version, bump_version)
        manifest["version"] = version
        _write_manifest(manifest_path, manifest)
        logger.info("%s: version bumped to %s", bundle_name, version)
    if not module_id or not version:
        raise ValueError("Bundle manifest must include name and version")

    modules_repo_root = effective_packages_root.parent
    _update_manifest_integrity(manifest_path, key_file, modules_repo_root, passphrase=passphrase)
    manifest = _load_manifest(manifest_path)

    index_path = registry_dir / "index.json"
    _ensure_publish_version_progression(index_path, module_id, version)

    tarball = package_bundle(bundle_dir, registry_dir=registry_dir)
    signature_file = sign_bundle(tarball, key_file, registry_dir)
    if not verify_bundle(tarball, signature_file, manifest):
        raise ValueError("Bundle verification failed; index.json not modified")

    checksum = _checksum_sha256(tarball)
    entry = _build_publish_entry(manifest, module_id, version, tarball, checksum)
    write_index_entry(index_path, entry)


def _parse_semver(version: str) -> tuple[int, int, int]:
    """Parse x.y.z into (major, minor, patch)."""
    parts = version.split(".")
    if len(parts) != 3 or any(not p.isdigit() for p in parts):
        raise ValueError(f"Unsupported version format for bump (expected x.y.z): {version}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def _bump_semver(version: str, bump_type: str) -> str:
    """Return version string bumped by major, minor, or patch."""
    major, minor, patch = _parse_semver(version)
    if bump_type == "major":
        return f"{major + 1}.0.0"
    if bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    if bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"Unsupported bump type: {bump_type}")


def _write_manifest(manifest_path: Path, data: dict[str, Any]) -> None:
    """Write manifest YAML preserving key order."""
    manifest_path.write_text(
        yaml.dump(
            data,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def _resolve_bundle_passphrase(args: argparse.Namespace) -> str:
    """Resolve bundle publish passphrase from args, env, stdin, or TTY prompt."""
    passphrase = (args.passphrase or "").strip()
    if not passphrase:
        passphrase = os.environ.get("SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE", "").strip()
    if not passphrase:
        passphrase = os.environ.get("SPECFACT_MODULE_SIGNING_PRIVATE_KEY_PASSPHRASE", "").strip()
    if args.passphrase_stdin:
        passphrase = sys.stdin.read().rstrip("\r\n") or passphrase
    if passphrase or not sys.stdin.isatty():
        return passphrase
    try:
        import getpass as _gp

        return _gp.getpass("Signing key passphrase (used for all bundles): ")
    except (EOFError, KeyboardInterrupt):
        return ""


def _publish_bundles(args: argparse.Namespace) -> int:
    """Handle bundle publish mode."""
    if args.key_file is None:
        logger.error("--bundle requires --key-file")
        return 1

    passphrase = _resolve_bundle_passphrase(args)
    modules_repo_dir = args.modules_repo_dir.resolve()
    bundle_packages_root = modules_repo_dir / "packages"
    registry_dir = args.registry_dir.resolve() if args.registry_dir is not None else modules_repo_dir / "registry"
    global BUNDLE_PACKAGES_ROOT
    BUNDLE_PACKAGES_ROOT = bundle_packages_root
    bundles = OFFICIAL_BUNDLES if args.bundle == "all" else [args.bundle]
    for bundle_name in bundles:
        publish_bundle(
            bundle_name, args.key_file, registry_dir, bump_version=args.bump_version, passphrase=passphrase or None
        )
        logger.info("Published bundle: %s", bundle_name)
    return 0


def _publish_single_module(args: argparse.Namespace) -> int:
    """Handle single-module packaging mode."""
    if args.module_path is None:
        logger.error("module_path is required when --bundle is not used")
        return 1

    try:
        module_dir = _find_module_dir(args.module_path.resolve())
    except ValueError as e:
        logger.error("%s", e)
        return 1

    manifest_path = module_dir / "module-package.yaml"
    manifest = _load_manifest(manifest_path)
    manifest = _ensure_publisher_email(manifest_path, manifest)
    name = str(manifest.get("name", "")).strip()
    version = str(manifest.get("version", "")).strip()
    if not name or not version:
        logger.error("name and version required in manifest")
        return 1

    try:
        _validate_namespace_for_marketplace(manifest, module_dir)
    except ValueError as e:
        logger.error("Validation: %s", e)
        return 1

    tarball_name = f"{name.replace('/', '-')}-{version}.tar.gz"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / tarball_name
    _create_tarball(module_dir, output_path, name, version)
    checksum = _checksum_sha256(output_path)
    (args.output_dir / f"{tarball_name}.sha256").write_text(f"{checksum}  {tarball_name}\n", encoding="utf-8")
    logger.info("Created %s (sha256=%s)", output_path, checksum)

    if args.sign:
        if _run_sign_if_requested(manifest_path, args.key_file):
            logger.info("Manifest signed.")
        else:
            logger.warning("Signing skipped or failed.")

    if args.index_fragment:
        _write_index_fragment(name, version, tarball_name, checksum, args.download_base_url, args.index_fragment)
        logger.info("Wrote index fragment to %s", args.index_fragment)
    return 0


@beartype
@ensure(lambda result: result >= 0, "exit code must be non-negative")
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and package a SpecFact module for registry publishing.",
    )
    parser.add_argument(
        "module_path",
        nargs="?",
        type=Path,
        help="Path to module directory or module-package.yaml",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory to write tarball and checksum (default: current dir)",
    )
    parser.add_argument(
        "--sign",
        action="store_true",
        help="Run sign-modules.py on manifest after packaging (requires key)",
    )
    parser.add_argument(
        "--key-file",
        type=Path,
        help="Private key for signing (used with --sign or --bundle)",
    )
    parser.add_argument(
        "--passphrase",
        type=str,
        default="",
        help="Passphrase for encrypted signing key (avoids per-module prompt when --bundle; prefer env or --passphrase-stdin).",
    )
    parser.add_argument(
        "--passphrase-stdin",
        action="store_true",
        help="Read signing key passphrase once from stdin (for --bundle all; no per-module prompt).",
    )
    parser.add_argument(
        "--index-fragment",
        type=Path,
        help="Write index.json module entry fragment to this file",
    )
    parser.add_argument(
        "--download-base-url",
        default="https://github.com/nold-ai/specfact-cli-modules/releases/download/",
        help="Base URL for download_url in index fragment",
    )
    parser.add_argument(
        "--modules-repo-dir",
        type=Path,
        default=MODULES_REPO_ROOT,
        help="Path to specfact-cli-modules checkout (default: sibling checkout or SPECFACT_MODULES_REPO)",
    )
    parser.add_argument(
        "--bundle",
        type=str,
        help="Publish bundle by name or 'all' for all official bundles",
    )
    parser.add_argument(
        "--bump-version",
        choices=("patch", "minor", "major"),
        default=None,
        help="Bump bundle version in module-package.yaml before publishing (bundle mode only).",
    )
    parser.add_argument(
        "--registry-dir",
        type=Path,
        default=None,
        help="Registry directory containing index.json/modules/signatures",
    )
    args = parser.parse_args()

    if args.bundle:
        return _publish_bundles(args)
    return _publish_single_module(args)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    sys.exit(main())
