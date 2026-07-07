"""Requirement evidence input models.

These models normalize upstream requirement context for validation evidence.
They do not make SpecFact the authoring system or source of truth for
requirements.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, cast

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, ConfigDict, Field


REQUIREMENTS_INPUT_SCHEMA_VERSION = "1"


class RequirementSourceType(StrEnum):
    """Supported upstream source reference types."""

    ISSUE = "issue"
    DOCUMENT = "document"
    OPENSPEC_CHANGE = "openspec_change"
    SPECKIT_SPEC = "speckit_spec"
    FILE = "file"
    BACKLOG_ITEM = "backlog_item"


class RequirementEvidenceLinkType(StrEnum):
    """Kinds of downstream evidence linked from a requirement input."""

    ARCHITECTURE = "architecture"
    SPEC = "spec"
    CODE = "code"
    TEST = "test"
    VALIDATION = "validation"
    REQUIREMENT = "requirement"


class RequirementConstraintType(StrEnum):
    """Supported requirement constraint categories."""

    PERFORMANCE = "performance"
    SECURITY = "security"
    INTEGRATION = "integration"
    COMPLIANCE = "compliance"
    UX = "ux"
    OPERATIONAL = "operational"


class RequirementCompletenessSeverity(StrEnum):
    """Advisory completeness finding severity."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@beartype
class RequirementSourceReference(BaseModel):
    """Reference to an upstream requirement source."""

    model_config = ConfigDict(use_enum_values=True)

    source_type: RequirementSourceType = Field(..., description="Type of upstream requirement source")
    locator: str = Field(..., min_length=1, description="Source locator such as URL, file path, or change ID")
    title: str | None = Field(default=None, description="Human-readable source title")
    revision: str | None = Field(default=None, description="Optional source revision, commit, or version")


@beartype
class BusinessRule(BaseModel):
    """Business rule imported from upstream requirement context."""

    rule_id: str = Field(..., min_length=1, description="Stable business rule identifier")
    name: str = Field(..., min_length=1, description="Rule name")
    given: str = Field(..., min_length=1, description="Given clause for validation scenario context")
    when: str = Field(..., min_length=1, description="When clause for validation scenario context")
    then: str = Field(..., min_length=1, description="Then clause for validation scenario context")
    priority: str | None = Field(default=None, description="Optional upstream priority such as MoSCoW")


@beartype
class RequirementConstraint(BaseModel):
    """Constraint imported from upstream requirement context."""

    model_config = ConfigDict(use_enum_values=True)

    constraint_id: str = Field(..., min_length=1, description="Stable constraint identifier")
    constraint_type: RequirementConstraintType = Field(..., description="Constraint category")
    statement: str = Field(..., min_length=1, description="Constraint statement")
    validation_criteria: list[str] = Field(default_factory=list, description="Criteria used to validate constraint")


@beartype
class RequirementEvidenceLink(BaseModel):
    """Link from requirement input to downstream validation evidence."""

    model_config = ConfigDict(use_enum_values=True)

    link_type: RequirementEvidenceLinkType = Field(..., description="Evidence target category")
    target: str = Field(..., min_length=1, description="Evidence target locator")
    relation: str = Field(default="references", min_length=1, description="Relationship to the target")


@beartype
class RequirementCompletenessFinding(BaseModel):
    """Profile-aware completeness finding stored as advisory evidence."""

    model_config = ConfigDict(use_enum_values=True)

    profile: str = Field(..., min_length=1, description="Profile that produced this finding")
    severity: RequirementCompletenessSeverity = Field(..., description="Finding severity")
    field_path: str = Field(..., min_length=1, description="Requirement field path")
    message: str = Field(..., min_length=1, description="Human-readable completeness guidance")


@beartype
class RequirementInput(BaseModel):
    """Normalized requirement context consumed by validation evidence."""

    schema_version: str = Field(..., min_length=1, description="Requirement input schema version")
    requirement_id: str = Field(..., min_length=1, description="Stable requirement identifier")
    title: str = Field(..., min_length=1, description="Requirement title")
    summary: str | None = Field(default=None, description="Optional upstream requirement summary")
    sources: list[RequirementSourceReference] = Field(
        ...,
        min_length=1,
        description="Upstream requirement source references",
    )
    business_rules: list[BusinessRule] = Field(default_factory=list, description="Imported business rules")
    constraints: list[RequirementConstraint] = Field(default_factory=list, description="Imported constraints")
    evidence_links: list[RequirementEvidenceLink] = Field(default_factory=list, description="Evidence target links")
    completeness_findings: list[RequirementCompletenessFinding] = Field(
        default_factory=list,
        description="Profile-aware advisory completeness findings",
    )


@beartype
class RequirementsInputExtensionPayload(BaseModel):
    """Serializable ProjectBundle extension payload for requirement inputs."""

    schema_version: str = Field(
        default=REQUIREMENTS_INPUT_SCHEMA_VERSION,
        min_length=1,
        description="Requirements extension payload schema version",
    )
    requirements: list[RequirementInput] = Field(default_factory=list, description="Requirement input records")


def _payload_has_schema_version(result: dict[str, Any]) -> bool:
    return result.get("schema_version") == REQUIREMENTS_INPUT_SCHEMA_VERSION


def _payload_has_requirements_list(result: dict[str, Any]) -> bool:
    return isinstance(result.get("requirements"), list)


def _payload_is_valid_extension(payload: dict[str, Any]) -> bool:
    try:
        RequirementsInputExtensionPayload.model_validate(payload)
    except ValueError:
        return False
    return True


@beartype
@require(lambda records: all(isinstance(record, RequirementInput) for record in records))
@ensure(_payload_has_schema_version)
@ensure(_payload_has_requirements_list)
def requirements_input_extension_payload(records: list[RequirementInput]) -> dict[str, Any]:
    """Return a JSON-serializable ProjectBundle extension payload."""
    payload = RequirementsInputExtensionPayload(requirements=records)
    return cast(dict[str, Any], payload.model_dump(mode="json"))


@beartype
@require(lambda payload: isinstance(payload, dict))
@require(_payload_is_valid_extension)
@ensure(lambda result: all(isinstance(record, RequirementInput) for record in result))
def load_requirements_input_extension(payload: dict[str, Any]) -> list[RequirementInput]:
    """Load requirement input records from a ProjectBundle extension payload."""
    return RequirementsInputExtensionPayload.model_validate(payload).requirements
