"""Module package metadata models."""

from __future__ import annotations

import re

from beartype import beartype
from icontract import ensure
from pydantic import BaseModel, Field, model_validator


CONVERTER_CLASS_PATH_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+$")


@beartype
class ServiceBridgeMetadata(BaseModel):
    """Service bridge declaration from module package manifest."""

    id: str = Field(..., description="Bridge identifier (for example: ado, jira, linear, github).")
    converter_class: str = Field(..., description="Fully-qualified converter class path.")
    description: str | None = Field(default=None, description="Optional bridge description.")

    @model_validator(mode="after")
    def _validate_bridge_metadata(self) -> ServiceBridgeMetadata:
        """Validate required bridge fields."""
        if not self.id.strip():
            raise ValueError("service_bridges.id must not be empty.")
        if not self.converter_class.strip():
            raise ValueError("service_bridges.converter_class must not be empty.")
        if not CONVERTER_CLASS_PATH_RE.match(self.converter_class):
            raise ValueError(
                "service_bridges.converter_class must be a dotted path (for example: package.module.ClassName)."
            )
        return self


@beartype
class ModulePackageMetadata(BaseModel):
    """Schema for a module package manifest."""

    name: str = Field(..., description="Package identifier (e.g. backlog_refine)")
    version: str = Field(default="0.1.0", description="Package version")
    commands: list[str] = Field(default_factory=list, description="Command names this package provides")
    command_help: dict[str, str] | None = Field(
        default=None,
        description="Optional command name -> help text for root help.",
    )
    pip_dependencies: list[str] = Field(default_factory=list, description="Optional pip dependencies")
    module_dependencies: list[str] = Field(default_factory=list, description="Optional other package ids")
    core_compatibility: str | None = Field(
        default=None,
        description="CLI core version compatibility (PEP 440 specifier, e.g. '>=0.28.0,<1.0.0').",
    )
    tier: str = Field(default="community", description="Tier: community or enterprise")
    addon_id: str | None = Field(default=None, description="Optional addon identifier")
    schema_version: str | None = Field(
        default=None,
        description="Compatible ProjectBundle schema version. None means current schema.",
    )
    protocol_operations: list[str] = Field(
        default_factory=list,
        description="Detected ModuleIOContract operations: import, export, sync, validate.",
    )
    service_bridges: list[ServiceBridgeMetadata] = Field(
        default_factory=list,
        description="Optional bridge declarations for converter registration.",
    )

    @beartype
    @ensure(lambda result: isinstance(result, list), "Validated bridges must be returned as a list")
    def validate_service_bridges(self) -> list[ServiceBridgeMetadata]:
        """Return validated bridge declarations for lifecycle registration."""
        return list(self.service_bridges)
