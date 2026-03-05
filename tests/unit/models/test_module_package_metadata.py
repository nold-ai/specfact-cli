"""Tests for module package metadata extensions."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from specfact_cli.models.module_package import (
    ModulePackageMetadata,
    SchemaExtension,
    ServiceBridgeMetadata,
)


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
            ServiceBridgeMetadata(
                id="ado",
                converter_class="specfact_backlog.backlog.adapters.ado.AdoConverter",
            )
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
            service_bridges=[ServiceBridgeMetadata(id="ado", converter_class="")],
        )


def test_service_bridge_converter_class_must_be_dotted_path() -> None:
    """converter class path should be module-qualified."""
    with pytest.raises(ValidationError):
        ModulePackageMetadata(
            name="backlog",
            commands=["backlog"],
            service_bridges=[ServiceBridgeMetadata(id="ado", converter_class="InvalidClassPath")],
        )


def test_manifest_parses_schema_extensions() -> None:
    """Module-package manifest MAY include schema_extensions array (arch-07)."""
    metadata = ModulePackageMetadata(
        name="backlog",
        commands=["backlog"],
        schema_extensions=[
            SchemaExtension(
                target="Feature",
                field="ado_work_item_id",
                type_hint="str",
                description="Azure DevOps work item ID",
            ),
        ],
    )
    assert len(metadata.schema_extensions) == 1
    assert metadata.schema_extensions[0].target == "Feature"
    assert metadata.schema_extensions[0].field == "ado_work_item_id"
    assert metadata.schema_extensions[0].type_hint == "str"
    assert "Azure DevOps" in metadata.schema_extensions[0].description


def test_schema_extension_target_must_be_feature_or_project_bundle() -> None:
    """SchemaExtension target SHALL be Feature or ProjectBundle."""
    with pytest.raises(ValidationError):
        SchemaExtension(
            target="Other",
            field="x",
            type_hint="str",
            description="",
        )


def test_module_without_schema_extensions_remains_valid() -> None:
    """Module without schema_extensions SHALL load successfully."""
    metadata = ModulePackageMetadata(name="backlog", commands=["backlog"])
    assert hasattr(metadata, "schema_extensions")
    assert metadata.schema_extensions == []
