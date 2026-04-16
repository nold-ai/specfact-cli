"""Tests for publish-module marketplace namespace validation."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[3] / "scripts" / "publish-module.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("publish_module_script", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load publish-module.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_official_nold_publisher_slug_name_skips_namespace_requirement() -> None:
    mod = _load_script_module()
    manifest = {
        "name": "module-registry",
        "version": "0.1.0",
        "commands": ["module"],
        "tier": "community",
        "publisher": {
            "name": "nold-ai",
            "url": "https://github.com/nold-ai/specfact-cli-modules",
            "email": mod.OFFICIAL_PUBLISHER_EMAIL,
        },
    }
    assert mod._official_nold_publisher_manifest(manifest) is True
    mod._validate_namespace_for_marketplace(manifest, Path("/tmp/module"))


def test_official_publisher_detected_by_email_only() -> None:
    mod = _load_script_module()
    manifest = {
        "name": "init",
        "version": "0.1.0",
        "commands": ["init"],
        "tier": "community",
        "publisher": {"email": mod.OFFICIAL_PUBLISHER_EMAIL},
    }
    assert mod._official_nold_publisher_manifest(manifest) is True
    mod._validate_namespace_for_marketplace(manifest, Path("/tmp/init"))


def test_non_official_marketplace_still_requires_namespace() -> None:
    mod = _load_script_module()
    manifest = {
        "name": "rogue-bundle",
        "version": "1.0.0",
        "commands": ["x"],
        "tier": "community",
        "publisher": {
            "name": "other",
            "email": "vendor@example.com",
            "url": "https://example.com",
        },
    }
    assert mod._official_nold_publisher_manifest(manifest) is False
    with pytest.raises(ValueError, match="namespace/name"):
        mod._validate_namespace_for_marketplace(manifest, Path("/tmp/rogue"))


def test_tier_only_without_official_publisher_requires_namespace() -> None:
    mod = _load_script_module()
    manifest = {
        "name": "plain-slug",
        "version": "1.0.0",
        "commands": ["x"],
        "tier": "community",
    }
    assert mod._official_nold_publisher_manifest(manifest) is False
    with pytest.raises(ValueError, match="namespace/name"):
        mod._validate_namespace_for_marketplace(manifest, Path("/tmp/plain"))


def test_namespaced_id_still_validates_pattern() -> None:
    mod = _load_script_module()
    manifest = {
        "name": "Bad_/Slash",
        "version": "1.0.0",
        "commands": ["x"],
        "tier": "community",
        "publisher": {"email": "vendor@example.com"},
    }
    with pytest.raises(ValueError, match="lowercase alphanumeric"):
        mod._validate_namespace_for_marketplace(manifest, Path("/tmp/bad"))
