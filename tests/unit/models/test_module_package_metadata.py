"""Tests for module package metadata extensions."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

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


def test_metadata_supports_service_bridges() -> None:
    """service_bridges should be accepted and preserved."""
    metadata = ModulePackageMetadata(
        name="backlog",
        commands=["backlog"],
        service_bridges=[
            {"id": "ado", "converter_class": "specfact_cli.modules.backlog.src.adapters.ado.AdoConverter"}
        ],
    )
    assert len(metadata.service_bridges) == 1
    assert metadata.service_bridges[0].id == "ado"


def test_service_bridge_requires_converter_class_path() -> None:
    """service bridge declarations should require converter_class."""
    with pytest.raises(ValidationError):
        ModulePackageMetadata(
            name="backlog",
            commands=["backlog"],
            service_bridges=[{"id": "ado"}],
        )


def test_service_bridge_converter_class_must_be_dotted_path() -> None:
    """converter class path should be module-qualified."""
    with pytest.raises(ValidationError):
        ModulePackageMetadata(
            name="backlog",
            commands=["backlog"],
            service_bridges=[{"id": "ado", "converter_class": "InvalidClassPath"}],
        )
