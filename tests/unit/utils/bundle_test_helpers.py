"""Shared helpers for bundle-related unit tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from specfact_cli.models.plan import Product
from specfact_cli.models.project import BundleManifest, BundleVersions, ProjectBundle


def write_minimal_bundle_files(
    bundle_dir: Path,
    *,
    manifest_overrides: dict[str, Any] | None = None,
    product_overrides: dict[str, Any] | None = None,
) -> None:
    """Create minimal manifest/product files for loading tests."""
    bundle_dir.mkdir(parents=True, exist_ok=True)

    manifest_data: dict[str, Any] = {
        "versions": {"schema": "1.0", "project": "0.1.0"},
        "bundle": {"format": "directory-based"},
        "checksums": {"algorithm": "sha256", "files": {}},
        "features": [],
        "protocols": [],
    }
    if manifest_overrides:
        manifest_data.update(manifest_overrides)

    product_data: dict[str, Any] = {"themes": [], "releases": []}
    if product_overrides:
        product_data.update(product_overrides)

    (bundle_dir / "bundle.manifest.yaml").write_text(yaml.dump(manifest_data))
    (bundle_dir / "product.yaml").write_text(yaml.dump(product_data))


def make_test_bundle(*, themes: list[str] | None = None, bundle_name: str = "test-bundle") -> ProjectBundle:
    """Construct a small ProjectBundle instance for save/roundtrip tests."""
    manifest = BundleManifest(
        versions=BundleVersions(schema="1.0", project="0.1.0"),
        schema_metadata=None,
        project_metadata=None,
    )
    product = Product(themes=themes or [])
    return ProjectBundle(manifest=manifest, bundle_name=bundle_name, product=product)


def assert_core_bundle_files(bundle_dir: Path) -> None:
    """Assert core files produced by save operations."""
    assert (bundle_dir / "bundle.manifest.yaml").exists()
    assert (bundle_dir / "product.yaml").exists()
