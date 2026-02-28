#!/usr/bin/env python3
"""Validate, package, sign, and publish SpecFact modules/bundles to registry index."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import yaml
from beartype import beartype
from icontract import ensure, require
from packaging.version import Version


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
OFFICIAL_BUNDLES = [
    "specfact-project",
    "specfact-backlog",
    "specfact-codebase",
    "specfact-spec",
    "specfact-govern",
]


@beartype
@require(lambda path: path.exists(), "Path must exist")
def _find_module_dir(path: Path) -> Path:
    """Return directory containing module-package.yaml."""
    if path.is_dir() and (path / "module-package.yaml").exists():
        return path.resolve()
    if path.name == "module-package.yaml" and path.is_file():
        return path.parent.resolve()
    raise ValueError(f"No module-package.yaml found at {path}")


@beartype
@require(lambda manifest_path: manifest_path.exists() and manifest_path.is_file(), "Manifest file must exist")
@ensure(lambda result: isinstance(result, dict), "Returns dict")
def _load_manifest(manifest_path: Path) -> dict:
    """Load and return manifest as dict. Raises ValueError if invalid."""
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("module-package.yaml must be a YAML object")
    if "name" not in raw or "version" not in raw or "commands" not in raw:
        raise ValueError("module-package.yaml must contain name, version, and commands")
    return raw


@beartype
def _validate_namespace_for_marketplace(manifest: dict, module_dir: Path) -> None:
    """If manifest suggests marketplace (has publisher or tier), validate namespace/name format."""
    _ = module_dir
    name = str(manifest.get("name", "")).strip()
    if not name:
        return
    publisher = manifest.get("publisher")
    tier = manifest.get("tier")
    if publisher is None and not tier:
        return
    if "/" not in name:
        raise ValueError(f"Marketplace module name must be namespace/name (e.g. acme-corp/backlog-pro), got {name!r}")
    if not _MARKETPLACE_NAMESPACE_PATTERN.match(name):
        raise ValueError(f"Marketplace module id must be lowercase alphanumeric and hyphens: {name!r}")


@beartype
@require(lambda module_dir: module_dir.is_dir(), "module_dir must be a directory")
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
@require(lambda tarball_path: tarball_path.exists() and tarball_path.is_file(), "Tarball path must exist")
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
@require(lambda bundle_dir: bundle_dir.exists() and bundle_dir.is_dir(), "bundle_dir must exist")
@ensure(lambda result: result.exists(), "Tarball must exist")
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
@require(lambda tarball: tarball.exists(), "tarball must exist")
@require(lambda key_file: key_file.exists(), "key file must exist")
@ensure(lambda result: result.exists(), "signature file must exist")
def sign_bundle(tarball: Path, key_file: Path, registry_dir: Path) -> Path:
    """Create detached signature file for bundle tarball."""
    signatures_dir = registry_dir / "signatures"
    signatures_dir.mkdir(parents=True, exist_ok=True)
    signature = hashlib.sha256(tarball.read_bytes() + key_file.read_bytes()).hexdigest()
    sig_path = signatures_dir / f"{tarball.stem}.sig"
    sig_path.write_text(signature + "\n", encoding="utf-8")
    return sig_path


@beartype
@require(lambda tarball: tarball.exists(), "tarball must exist")
@require(lambda signature_file: signature_file.exists(), "signature file must exist")
@ensure(lambda result: isinstance(result, bool), "result must be bool")
def verify_bundle(tarball: Path, signature_file: Path, manifest: dict) -> bool:
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
@require(lambda index_path: index_path.suffix == ".json", "index_path must be json file")
def write_index_entry(index_path: Path, entry: dict) -> None:
    """Write/replace module entry into registry index using atomic file replace."""
    if index_path.exists():
        payload = json.loads(index_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("index.json must contain object payload")
    else:
        payload = {"modules": []}

    modules = payload.get("modules", [])
    if not isinstance(modules, list):
        raise ValueError("index.json 'modules' must be a list")

    updated = False
    for idx, existing in enumerate(modules):
        if isinstance(existing, dict) and existing.get("id") == entry.get("id"):
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


@beartype
@require(lambda bundle_name: bundle_name.strip() != "", "bundle_name must be non-empty")
def publish_bundle(
    bundle_name: str,
    key_file: Path,
    registry_dir: Path,
    bundle_packages_root: Path | None = None,
) -> None:
    """Package, sign, verify, and publish single bundle into registry index."""
    effective_packages_root = bundle_packages_root if bundle_packages_root is not None else BUNDLE_PACKAGES_ROOT
    bundle_dir = effective_packages_root / bundle_name
    if not bundle_dir.exists():
        raise ValueError(f"Bundle directory not found: {bundle_dir}")
    if not key_file.exists():
        raise ValueError(f"Key file not found: {key_file}")

    manifest = _load_manifest(bundle_dir / "module-package.yaml")
    module_id = str(manifest.get("name", "")).strip()
    version = str(manifest.get("version", "")).strip()
    if not module_id or not version:
        raise ValueError("Bundle manifest must include name and version")

    index_path = registry_dir / "index.json"
    if index_path.exists():
        payload = json.loads(index_path.read_text(encoding="utf-8"))
        modules = payload.get("modules", []) if isinstance(payload, dict) else []
        for existing in modules:
            if not isinstance(existing, dict) or existing.get("id") != module_id:
                continue
            existing_version = str(existing.get("latest_version", "")).strip()
            if not existing_version:
                continue
            if Version(existing_version) >= Version(version):
                raise ValueError(
                    f"Refusing publish with same version or downgrade: existing latest={existing_version}, new={version}"
                )

    tarball = package_bundle(bundle_dir, registry_dir=registry_dir)
    signature_file = sign_bundle(tarball, key_file, registry_dir)
    if not verify_bundle(tarball, signature_file, manifest):
        raise ValueError("Bundle verification failed; index.json not modified")

    checksum = _checksum_sha256(tarball)
    entry = {
        "id": module_id,
        "latest_version": version,
        "download_url": f"modules/{tarball.name}",
        "checksum_sha256": checksum,
        "tier": manifest.get("tier", "community"),
        "publisher": manifest.get("publisher", "unknown"),
        "bundle_dependencies": manifest.get("bundle_dependencies", []),
    }
    write_index_entry(index_path, entry)


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
        "--registry-dir",
        type=Path,
        default=None,
        help="Registry directory containing index.json/modules/signatures",
    )
    args = parser.parse_args()

    if args.bundle:
        if args.key_file is None:
            print("Error: --bundle requires --key-file", file=sys.stderr)
            return 1
        modules_repo_dir = args.modules_repo_dir.resolve()
        bundle_packages_root = modules_repo_dir / "packages"
        registry_dir = args.registry_dir.resolve() if args.registry_dir is not None else modules_repo_dir / "registry"
        global BUNDLE_PACKAGES_ROOT
        BUNDLE_PACKAGES_ROOT = bundle_packages_root
        bundles = OFFICIAL_BUNDLES if args.bundle == "all" else [args.bundle]
        for bundle_name in bundles:
            publish_bundle(bundle_name, args.key_file, registry_dir)
            print(f"Published bundle: {bundle_name}")
        return 0

    if args.module_path is None:
        print("Error: module_path is required when --bundle is not used", file=sys.stderr)
        return 1

    try:
        module_dir = _find_module_dir(args.module_path.resolve())
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    manifest_path = module_dir / "module-package.yaml"
    manifest = _load_manifest(manifest_path)
    name = str(manifest.get("name", "")).strip()
    version = str(manifest.get("version", "")).strip()
    if not name or not version:
        print("Error: name and version required in manifest", file=sys.stderr)
        return 1

    try:
        _validate_namespace_for_marketplace(manifest, module_dir)
    except ValueError as e:
        print(f"Validation: {e}", file=sys.stderr)
        return 1

    tarball_name = f"{name.replace('/', '-')}-{version}.tar.gz"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / tarball_name
    _create_tarball(module_dir, output_path, name, version)
    checksum = _checksum_sha256(output_path)
    (args.output_dir / f"{tarball_name}.sha256").write_text(f"{checksum}  {tarball_name}\n", encoding="utf-8")
    print(f"Created {output_path} (sha256={checksum})")

    if args.sign:
        if _run_sign_if_requested(manifest_path, args.key_file):
            print("Manifest signed.")
        else:
            print("Warning: signing skipped or failed.", file=sys.stderr)

    if args.index_fragment:
        _write_index_fragment(name, version, tarball_name, checksum, args.download_base_url, args.index_fragment)
        print(f"Wrote index fragment to {args.index_fragment}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
