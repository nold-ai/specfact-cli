"""
Unit tests for schema extension system (arch-07).

Spec: schema-extension-system — extensions field and get_extension/set_extension on Feature and ProjectBundle.
"""

from __future__ import annotations

import json

import pytest
import yaml

from specfact_cli.models.plan import Feature, Product
from specfact_cli.models.project import ProjectBundle


class TestFeatureExtensions:
    """Feature model extensions field and accessors (spec: schema-extension-system)."""

    def test_feature_includes_extensions_field(self) -> None:
        """Feature model SHALL include extensions dict field defaulting to empty dict."""
        f = Feature(key="F-1", title="Test")
        assert hasattr(f, "extensions")
        assert f.extensions == {}
        assert f.extensions is not None

    def test_feature_extensions_serialize_deserialize_yaml(self) -> None:
        """extensions SHALL serialize/deserialize with YAML."""
        f = Feature(key="F-1", title="Test", extensions={"backlog.ado_id": "123"})
        dumped = yaml.safe_dump(f.model_dump())
        loaded = yaml.safe_load(dumped)
        f2 = Feature.model_validate(loaded)
        assert f2.extensions == {"backlog.ado_id": "123"}

    def test_feature_extensions_serialize_deserialize_json(self) -> None:
        """extensions SHALL serialize/deserialize with JSON."""
        f = Feature(key="F-1", title="Test", extensions={"backlog.ado_id": "123"})
        dumped = json.dumps(f.model_dump())
        loaded = json.loads(dumped)
        f2 = Feature.model_validate(loaded)
        assert f2.extensions == {"backlog.ado_id": "123"}

    def test_feature_get_extension_returns_value(self) -> None:
        """get_extension(module_name, field) SHALL return value at extensions['module.field']."""
        f = Feature(key="F-1", title="Test")
        f.set_extension("backlog", "ado_work_item_id", "123456")
        assert f.get_extension("backlog", "ado_work_item_id") == "123456"

    def test_feature_get_extension_missing_returns_default(self) -> None:
        """get_extension with missing field SHALL return default."""
        f = Feature(key="F-1", title="Test")
        assert f.get_extension("backlog", "missing_field", default="default_value") == "default_value"
        assert "backlog.missing_field" not in f.extensions

    def test_feature_set_extension_stores_with_namespace_prefix(self) -> None:
        """set_extension(module_name, field, value) SHALL store at extensions['module.field']."""
        f = Feature(key="F-1", title="Test")
        f.set_extension("backlog", "ado_work_item_id", "123456")
        assert f.extensions["backlog.ado_work_item_id"] == "123456"

    def test_feature_invalid_module_name_raises(self) -> None:
        """Invalid module_name (e.g. contains dots) SHALL raise ValueError or contract violation."""
        f = Feature(key="F-1", title="Test")
        with pytest.raises((ValueError, Exception), match="Invalid module name format|module name"):
            f.set_extension("backlog.submodule", "field", "value")

    def test_feature_invalid_field_name_raises(self) -> None:
        """Invalid field name format SHALL raise (contract or ValueError)."""
        f = Feature(key="F-1", title="Test")
        with pytest.raises(Exception):
            f.set_extension("backlog", "invalid-field", "value")


class TestProjectBundleExtensions:
    """ProjectBundle model extensions field and accessors."""

    def _minimal_bundle(self) -> ProjectBundle:
        from specfact_cli.models.project import BundleManifest, BundleVersions

        manifest = BundleManifest(versions=BundleVersions(schema="1.0", project="0.1.0"))
        return ProjectBundle(
            manifest=manifest,
            bundle_name="test",
            product=Product(themes=[], releases=[]),
        )

    def test_project_bundle_includes_extensions_field(self) -> None:
        """ProjectBundle SHALL include extensions dict field defaulting to empty dict."""
        bundle = self._minimal_bundle()
        assert hasattr(bundle, "extensions")
        assert bundle.extensions == {}
        assert bundle.extensions is not None

    def test_project_bundle_extensions_serialize_deserialize(self) -> None:
        """extensions SHALL serialize/deserialize with YAML/JSON."""
        bundle = self._minimal_bundle()
        bundle.set_extension("sync", "last_sync_timestamp", "2025-01-15T12:00:00Z")
        dumped = bundle.model_dump(mode="json")
        loaded = json.loads(json.dumps(dumped))
        bundle2 = ProjectBundle.model_validate(loaded)
        assert bundle2.get_extension("sync", "last_sync_timestamp") == "2025-01-15T12:00:00Z"

    def test_project_bundle_get_extension_set_extension(self) -> None:
        """get_extension/set_extension SHALL work on ProjectBundle."""
        bundle = self._minimal_bundle()
        bundle.set_extension("sync", "last_sync_timestamp", "2025-01-15T12:00:00Z")
        assert bundle.get_extension("sync", "last_sync_timestamp") == "2025-01-15T12:00:00Z"
        assert bundle.get_extension("sync", "missing", default="def") == "def"


class TestBackwardCompatibility:
    """Backward compatibility: bundles without extensions load successfully."""

    def test_feature_without_extensions_loads(self) -> None:
        """Feature from dict without 'extensions' key SHALL default to empty dict."""
        data = {"key": "F-1", "title": "Test"}
        f = Feature.model_validate(data)
        assert f.extensions == {}

    def test_bundle_operations_without_extensions(self) -> None:
        """Core operations SHALL work when extensions is empty dict."""
        from specfact_cli.models.project import BundleManifest, BundleVersions

        manifest = BundleManifest(versions=BundleVersions(schema="1.0", project="0.1.0"))
        bundle = ProjectBundle(
            manifest=manifest,
            bundle_name="test",
            product=Product(themes=[], releases=[]),
        )
        assert bundle.extensions == {}
        assert bundle.get_feature("x") is None
