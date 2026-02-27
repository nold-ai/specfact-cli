#!/usr/bin/env python3
"""Validate, package, and optionally sign a SpecFact module for registry publishing."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
import tarfile
from pathlib import Path

import yaml
from beartype import beartype
from icontract import ensure, require


_MARKETPLACE_NAMESPACE_PATTERN = re.compile(r"^[a-z][a-z0-9-]*/[a-z][a-z0-9-]+$")
_IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "logs", "tests"}
_IGNORED_SUFFIXES = {".pyc", ".pyo"}


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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and package a SpecFact module for registry publishing.",
    )
    parser.add_argument(
        "module_path",
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
        help="Private key for signing (used with --sign)",
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
    args = parser.parse_args()

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
