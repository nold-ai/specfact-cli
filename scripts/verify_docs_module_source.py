#!/usr/bin/env python3
"""Authenticate documentation CI module sources with the trusted core verifier."""

from __future__ import annotations

import argparse
import importlib.util
import logging
from pathlib import Path
from types import ModuleType

from beartype import beartype
from icontract import ensure


REQUIRED_BUNDLES = frozenset(
    f"specfact-{name}" for name in ("backlog", "codebase", "code-review", "govern", "project", "requirements", "spec")
)


def _trusted_file(trusted_root: Path, relative: str, modules_root: Path) -> Path:
    path = (trusted_root / relative).resolve(strict=True)
    if not path.is_relative_to(trusted_root) or path.is_relative_to(modules_root):
        raise ValueError(f"Documentation verifier input must come from the separate core checkout: {relative}")
    return path


def _load_verifier(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("trusted_docs_module_verifier", path)
    if spec is None or spec.loader is None:
        raise ValueError("Cannot load the trusted core module verifier")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    return verifier


@beartype
@ensure(lambda result: result >= len(REQUIRED_BUNDLES))
def verify_source(modules_root: Path, trusted_root: Path) -> int:
    """Require publisher signatures and exact filesystem payloads for every import root."""
    modules_root, trusted_root = modules_root.resolve(strict=True), trusted_root.resolve(strict=True)
    verifier_path = _trusted_file(trusted_root, "scripts/verify-modules-signature.py", modules_root)
    key_path = _trusted_file(trusted_root, "resources/keys/module-signing-public.pem", modules_root)
    packages = modules_root / "packages"
    bundles = {path.parent.name: path.parent for path in packages.glob("*/src") if path.is_dir()}
    if missing := REQUIRED_BUNDLES - bundles.keys():
        raise ValueError(f"Documentation source is missing required bundles: {', '.join(sorted(missing))}")
    verifier = _load_verifier(verifier_path)
    public_key = key_path.read_text(encoding="utf-8")
    for name, bundle in sorted(bundles.items()):
        manifest = bundle / "module-package.yaml"
        if not manifest.is_file():
            raise ValueError(f"Documentation source is missing a manifest: {name}")
        verifier.verify_manifest(
            manifest,
            require_signature=True,
            public_key_pem=public_key,
            payload_from_filesystem=True,
            verify_checksum=True,
        )
    return len(bundles)


@beartype
@ensure(lambda result: result == 0)
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modules-root", required=True, type=Path)
    parser.add_argument("--trusted-core-root", required=True, type=Path)
    args = parser.parse_args()
    count = verify_source(args.modules_root, args.trusted_core_root)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger(__name__).info(
        "Verified publisher signatures and filesystem payloads for %d documentation bundles.", count
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
