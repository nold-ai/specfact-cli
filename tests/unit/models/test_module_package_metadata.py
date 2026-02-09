"""Tests for module package metadata extensions."""

from __future__ import annotations

from specfact_cli.models.module_package import ModulePackageMetadata


def test_metadata_includes_schema_version() -> None:
    """Metadata model should provide optional schema_version field."""
    metadata = ModulePackageMetadata(name="backlog", commands=["backlog"])
    assert hasattr(metadata, "schema_version")


def test_metadata_includes_protocol_operations() -> None:
    """Metadata model should provide protocol_operations list field."""
    metadata = ModulePackageMetadata(name="backlog", commands=["backlog"])
    assert hasattr(metadata, "protocol_operations")
    assert isinstance(metadata.protocol_operations, list)


def test_metadata_schema_version_defaults_to_none() -> None:
    """schema_version should default to None when omitted."""
    metadata = ModulePackageMetadata(name="backlog", commands=["backlog"])
    assert metadata.schema_version is None


def test_protocol_operations_defaults_to_empty() -> None:
    """protocol_operations should default to an empty list."""
    metadata = ModulePackageMetadata(name="backlog", commands=["backlog"])
    assert metadata.protocol_operations == []
