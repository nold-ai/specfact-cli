"""Module package metadata models."""

from __future__ import annotations

import re

from beartype import beartype
from icontract import ensure
from pydantic import BaseModel, Field, model_validator


CHECKSUM_ALGO_RE = re.compile(r"^sha256:[a-fA-F0-9]{64}$|^sha384:[a-fA-F0-9]{96}$|^sha512:[a-fA-F0-9]{128}$")
CONVERTER_CLASS_PATH_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+$")
MODULE_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
FIELD_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


@beartype
class SchemaExtension(BaseModel):
    """Declarative schema extension for Feature or ProjectBundle (arch-07)."""

    target: str = Field(..., description="Target model: Feature or ProjectBundle")
    field: str = Field(..., description="Field name (snake_case)")
    type_hint: str = Field(..., description="Type hint for documentation (e.g. str, int)")
    description: str = Field(default="", description="Human-readable description")

    @model_validator(mode="after")
    def _validate_target_and_field(self) -> SchemaExtension:
        if self.target not in ("Feature", "ProjectBundle"):
            raise ValueError("target must be Feature or ProjectBundle")
        if not FIELD_NAME_RE.match(self.field):
            raise ValueError("field must match [a-z][a-z0-9_]*")
        return self


@beartype
class PublisherInfo(BaseModel):
    """Publisher identity from module manifest (arch-06)."""

    name: str = Field(..., description="Publisher display name")
    email: str = Field(..., description="Publisher contact email")
    attributes: dict[str, str] = Field(default_factory=dict, description="Optional publisher attributes")

    @model_validator(mode="after")
    def _validate_non_empty(self) -> PublisherInfo:
        if not self.name.strip():
            raise ValueError("Publisher name must not be empty")
        if not self.email.strip():
            raise ValueError("Publisher email must not be empty")
        return self


@beartype
class IntegrityInfo(BaseModel):
    """Integrity metadata for module artifact verification (arch-06)."""

    checksum: str = Field(..., description="Checksum in algo:hex format (e.g. sha256:...)")
    signature: str | None = Field(default=None, description="Optional detached signature (base64)")

    @model_validator(mode="after")
    def _validate_checksum_format(self) -> IntegrityInfo:
        """Validation SHALL ensure checksum format correctness."""
        if not CHECKSUM_ALGO_RE.match(self.checksum):
            raise ValueError(
                "integrity.checksum must be algo:hex (e.g. sha256:<64 hex chars>, sha384:<96>, sha512:<128>)"
            )
        return self


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
class VersionedModuleDependency(BaseModel):
    """Versioned module dependency entry (arch-06)."""

    name: str = Field(..., description="Module package id")
    version_specifier: str | None = Field(default=None, description="PEP 440 version specifier")


@beartype
class VersionedPipDependency(BaseModel):
    """Versioned pip dependency entry (arch-06)."""

    name: str = Field(..., description="PyPI package name")
    version_specifier: str | None = Field(default=None, description="PEP 440 version specifier")


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
    publisher: PublisherInfo | None = Field(default=None, description="Publisher identity (arch-06)")
    integrity: IntegrityInfo | None = Field(default=None, description="Integrity metadata (arch-06)")
    module_dependencies_versioned: list[VersionedModuleDependency] = Field(
        default_factory=list,
        description="Versioned module dependency declarations (arch-06)",
    )
    pip_dependencies_versioned: list[VersionedPipDependency] = Field(
        default_factory=list,
        description="Versioned pip dependency declarations (arch-06)",
    )
    service_bridges: list[ServiceBridgeMetadata] = Field(
        default_factory=list,
        description="Optional bridge declarations for converter registration.",
    )
    schema_extensions: list[SchemaExtension] = Field(
        default_factory=list,
        description="Declarative schema extensions for Feature/ProjectBundle (arch-07).",
    )
    description: str | None = Field(default=None, description="Module description for user-facing module details")
    license: str | None = Field(default=None, description="SPDX license identifier or license name")
    source: str = Field(default="builtin", description="Module source: builtin, marketplace, or custom")

    @beartype
    @ensure(lambda result: isinstance(result, list), "Validated bridges must be returned as a list")
    def validate_service_bridges(self) -> list[ServiceBridgeMetadata]:
        """Return validated bridge declarations for lifecycle registration."""
        return list(self.service_bridges)

    @model_validator(mode="after")
    def validate_source(self) -> ModulePackageMetadata:
        """Validate source is one of supported module origins."""
        if self.source not in {"builtin", "marketplace", "custom"}:
            raise ValueError("source must be one of: builtin, marketplace, custom")
        return self
