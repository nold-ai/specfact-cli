"""Tests for ProjectBundle schema_version field."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from specfact_cli.models.plan import Product
from specfact_cli.models.project import BundleManifest, ProjectBundle


def test_project_bundle_has_schema_version() -> None:
    """ProjectBundle should expose schema_version with default value '1'."""
    bundle = ProjectBundle(
        manifest=BundleManifest(schema_metadata=None, project_metadata=None),
        bundle_name="test-bundle",
        product=Product(),
    )
    assert bundle.schema_version == "1"


def test_schema_version_can_be_set() -> None:
    """ProjectBundle should accept custom schema_version values."""
    bundle = ProjectBundle(
        manifest=BundleManifest(schema_metadata=None, project_metadata=None),
        bundle_name="test-bundle",
        product=Product(),
        schema_version="2",
    )
    assert bundle.schema_version == "2"


def test_schema_version_validation() -> None:
    """ProjectBundle schema_version must be validated as string."""
    with pytest.raises(ValidationError):
        ProjectBundle(
            manifest=BundleManifest(schema_metadata=None, project_metadata=None),
            bundle_name="test-bundle",
            product=Product(),
            schema_version=1,
        )
