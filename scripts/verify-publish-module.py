#!/usr/bin/env python3
"""Require the replacement signing key and a new version for core bundle publication."""

from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path

import yaml
from icontract import ensure
from packaging.version import Version


@ensure(lambda result: result is None, "Verification either succeeds or raises")
def main(module_dir: Path) -> None:
    repository = Path(__file__).resolve().parents[1]
    registry = repository / "src/specfact_cli/registry"
    cutoff = json.loads((registry / "official-module-cutoff.json").read_text(encoding="utf-8"))
    manifest_path = module_dir / "module-package.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    module_id = str(manifest["name"])
    candidate_version = Version(str(manifest["version"]))
    bundled_versions = cutoff["bundled"].get(module_id)
    if not bundled_versions or candidate_version <= max(Version(version) for version in bundled_versions):
        raise ValueError("Core bundle publication requires a known module and a version above the release cutoff")
    verify_manifest = runpy.run_path(
        str(repository / "scripts/verify-modules-signature.py"),
        run_name="specfact_module_signature_verifier",
    )["verify_manifest"]
    verify_manifest(
        manifest_path,
        require_signature=True,
        public_key_pem=(registry / "module-signing-public-next.pem").read_text(encoding="utf-8"),
        payload_from_filesystem=True,
    )


if __name__ == "__main__":
    main(Path(sys.argv[1]))
