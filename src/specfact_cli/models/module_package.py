"""Module package metadata models."""

from __future__ import annotations

from beartype import beartype
from pydantic import BaseModel, Field


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
