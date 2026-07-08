"""Core requirements context adapter contracts and helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal, Protocol, cast, get_args

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from specfact_cli.models.project import ProjectBundle
from specfact_cli.models.requirements import (
    RequirementEvidenceLinkType,
    RequirementInput,
    load_requirements_input_extension,
    requirements_input_extension_payload,
)
from specfact_cli.models.validation import ValidationReport


RequirementContextValidationProfile = Literal[
    "solo",
    "startup",
    "team",
    "enterprise",
    "strict",
    "solo_developer",
    "api_first_team",
    "enterprise_full_stack",
]
KNOWN_REQUIREMENT_CONTEXT_PROFILES: frozenset[str] = frozenset(get_args(RequirementContextValidationProfile))
STRICT_REQUIREMENT_CONTEXT_PROFILES: frozenset[str] = frozenset({"enterprise", "strict", "enterprise_full_stack"})


class RequirementContextDiagnosticSeverity(StrEnum):
    """Severity for bounded requirements context diagnostics."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@beartype
class RequirementContextDiagnostic(BaseModel):
    """Bounded diagnostic emitted while importing requirement context."""

    model_config = ConfigDict(use_enum_values=True)

    severity: RequirementContextDiagnosticSeverity = Field(..., description="Diagnostic severity")
    code: str = Field(..., min_length=1, description="Stable diagnostic code")
    message: str = Field(..., min_length=1, description="Human-readable diagnostic message")
    source_locator: str | None = Field(default=None, description="Optional upstream source locator")
    requirement_id: str | None = Field(default=None, description="Best-effort requirement identifier")
    record_index: int | None = Field(
        default=None,
        ge=0,
        description="Zero-based source record index when available",
    )


@beartype
class RequirementContextImportResult(BaseModel):
    """Normalized requirement import result plus bounded diagnostics."""

    requirements: list[RequirementInput] = Field(default_factory=list, description="Normalized requirement records")
    diagnostics: list[RequirementContextDiagnostic] = Field(
        default_factory=list,
        description="Import diagnostics for records that could not be normalized",
    )


@beartype
class RequirementContextCoverageSummary(BaseModel):
    """Machine-readable coverage summary for normalized requirement inputs."""

    total_requirements: int = Field(..., ge=0, description="Total normalized requirements")
    with_business_rules: int = Field(..., ge=0, description="Requirements with business rules")
    with_constraints: int = Field(..., ge=0, description="Requirements with constraints")
    with_evidence_links: int = Field(..., ge=0, description="Requirements with evidence links")
    with_architecture_links: int = Field(..., ge=0, description="Requirements linked to architecture evidence")
    with_code_links: int = Field(..., ge=0, description="Requirements linked to code evidence")
    with_test_links: int = Field(..., ge=0, description="Requirements linked to test evidence")
    missing_evidence_requirement_ids: list[str] = Field(
        default_factory=list,
        description="Requirement IDs missing downstream evidence links",
    )


class RequirementContextAdapter(Protocol):
    """Protocol for module adapters that import requirement-like sources."""

    @beartype
    @require(lambda source: isinstance(source, Path), "source must be a Path")
    def import_requirements(self, source: Path, config: Mapping[str, Any]) -> RequirementContextImportResult:
        """Import source-attributed requirement records from an upstream source."""
        raise NotImplementedError


def _all_records_supported(records: Sequence[RequirementInput | Mapping[str, Any]]) -> bool:
    return all(isinstance(record, RequirementInput | Mapping) for record in records)


def _normalization_result_valid(result: RequirementContextImportResult) -> bool:
    return all(isinstance(requirement, RequirementInput) for requirement in result.requirements)


def _record_requirement_id(record: RequirementInput | Mapping[str, Any]) -> str | None:
    if isinstance(record, RequirementInput):
        return _optional_text(record.requirement_id)
    value = record.get("requirement_id")
    return _optional_text(value) if isinstance(value, str) and value else None


def _validation_error_message(exc: ValidationError) -> str:
    first_error = exc.errors()[0] if exc.errors() else {"msg": str(exc)}
    location = ".".join(str(part) for part in first_error.get("loc", ()))
    message = str(first_error.get("msg", "invalid requirement input")) or "invalid requirement input"
    return f"{location}: {message}" if location else message


def _optional_text(value: str | None) -> str | None:
    if not value:
        return None
    realize = getattr(value, "__ch_realize__", None)
    if callable(realize):
        realized = realize()
        return realized if isinstance(realized, str) else str(realized)
    return value


def _profile_nonempty(profile: str) -> bool:
    return profile.strip() != ""


def _profile_supported(profile: str) -> bool:
    return profile in KNOWN_REQUIREMENT_CONTEXT_PROFILES


def _source_locator_supported(source_locator: str | None) -> bool:
    return source_locator is None or type(source_locator) is str


def _coverage_summary_consistent(result: RequirementContextCoverageSummary) -> bool:
    return result.total_requirements >= len(result.missing_evidence_requirement_ids)


def _requirements_with_evidence_link_type(
    requirements: Sequence[RequirementInput],
    link_type: RequirementEvidenceLinkType,
) -> int:
    count = 0
    for requirement in requirements:
        if any(link.link_type == link_type for link in requirement.evidence_links):
            count += 1
    return max(0, count)


def _missing_evidence_requirement_ids(requirements: Sequence[RequirementInput]) -> list[str]:
    return [requirement.requirement_id for requirement in requirements if not requirement.evidence_links]


def _invalid_requirement_diagnostic(
    exc: ValidationError,
    record: RequirementInput | Mapping[str, Any],
    source_locator: str | None,
    record_index: int,
) -> RequirementContextDiagnostic:
    return RequirementContextDiagnostic(
        severity=RequirementContextDiagnosticSeverity.ERROR,
        code="invalid_requirement_input",
        message=_validation_error_message(exc),
        source_locator=_optional_text(source_locator),
        requirement_id=_record_requirement_id(record),
        record_index=record_index,
    )


@beartype
@require(_all_records_supported, "records must be RequirementInput or mapping values")
@require(_source_locator_supported, "source_locator must be text when provided")
@ensure(_normalization_result_valid)
def normalize_requirement_records(
    records: Sequence[RequirementInput | Mapping[str, Any]],
    *,
    source_locator: str | None = None,
) -> RequirementContextImportResult:
    """Normalize source-attributed requirement records with bounded diagnostics."""
    normalized: list[RequirementInput] = []
    diagnostics: list[RequirementContextDiagnostic] = []

    for record_index, record in enumerate(records):
        if isinstance(record, RequirementInput):
            normalized.append(record)
            continue
        try:
            normalized.append(RequirementInput.model_validate(record))
        except ValidationError as exc:
            diagnostics.append(_invalid_requirement_diagnostic(exc, record, source_locator, record_index))

    return RequirementContextImportResult(requirements=normalized, diagnostics=diagnostics)


@beartype
@require(lambda bundle: isinstance(bundle, ProjectBundle), "bundle must be a ProjectBundle")
@require(lambda requirements: all(isinstance(record, RequirementInput) for record in requirements))
@ensure(lambda result: isinstance(result, ProjectBundle))
def attach_requirements_to_bundle(bundle: ProjectBundle, requirements: Sequence[RequirementInput]) -> ProjectBundle:
    """Store normalized requirements on the existing requirements.inputs extension."""
    bundle.set_extension("requirements", "inputs", requirements_input_extension_payload(list(requirements)))
    return bundle


@beartype
@require(lambda bundle: isinstance(bundle, ProjectBundle), "bundle must be a ProjectBundle")
@ensure(lambda result: all(isinstance(record, RequirementInput) for record in result))
def load_requirements_from_bundle(bundle: ProjectBundle) -> list[RequirementInput]:
    """Load normalized requirements from the requirements.inputs extension."""
    payload = bundle.get_extension("requirements", "inputs", default=None)
    if payload is None:
        return []
    if not isinstance(payload, dict):
        raise ValueError("requirements.inputs extension must be a mapping payload")
    return load_requirements_input_extension(cast(dict[str, Any], payload))


@beartype
@require(lambda requirements: all(isinstance(record, RequirementInput) for record in requirements))
@ensure(_coverage_summary_consistent)
def inspect_requirement_context_coverage(
    requirements: Sequence[RequirementInput],
) -> RequirementContextCoverageSummary:
    """Return machine-readable coverage counts for normalized requirement inputs."""
    requirement_list = list(requirements)
    return RequirementContextCoverageSummary(
        total_requirements=len(requirement_list),
        with_business_rules=sum(bool(requirement.business_rules) for requirement in requirement_list),
        with_constraints=sum(bool(requirement.constraints) for requirement in requirement_list),
        with_evidence_links=sum(bool(requirement.evidence_links) for requirement in requirement_list),
        with_architecture_links=_requirements_with_evidence_link_type(
            requirement_list,
            RequirementEvidenceLinkType.ARCHITECTURE,
        ),
        with_code_links=_requirements_with_evidence_link_type(requirement_list, RequirementEvidenceLinkType.CODE),
        with_test_links=_requirements_with_evidence_link_type(requirement_list, RequirementEvidenceLinkType.TEST),
        missing_evidence_requirement_ids=_missing_evidence_requirement_ids(requirement_list),
    )


def _missing_evidence_severity(profile: RequirementContextValidationProfile) -> str:
    return "error" if profile in STRICT_REQUIREMENT_CONTEXT_PROFILES else "warning"


def _empty_requirements_report() -> ValidationReport:
    return ValidationReport(
        status="warnings",
        violations=[
            {
                "severity": "warning",
                "message": "No requirements.inputs records are attached to the bundle.",
                "location": "requirements.inputs",
            }
        ],
        summary={"total_checks": 1, "passed": 0, "failed": 0, "warnings": 1},
    )


def _missing_evidence_violations(
    coverage: RequirementContextCoverageSummary,
    *,
    severity: str,
) -> list[dict[str, str]]:
    return [
        {
            "severity": severity,
            "message": "Requirement input has no downstream evidence links.",
            "location": f"requirements.inputs[{requirement_id}].evidence_links",
        }
        for requirement_id in coverage.missing_evidence_requirement_ids
    ]


def _validation_status(failed: int, warnings: int) -> Literal["passed", "failed", "warnings"]:
    if failed:
        return "failed"
    if warnings:
        return "warnings"
    return "passed"


def _validation_summary(
    requirements: Sequence[RequirementInput],
    coverage: RequirementContextCoverageSummary,
    violations: Sequence[Mapping[str, str]],
) -> dict[str, int]:
    failed = sum(violation["severity"] == "error" for violation in violations)
    warnings = sum(violation["severity"] == "warning" for violation in violations)
    return {
        "total_checks": max(1, len(requirements) * 2),
        "passed": len(requirements) + coverage.with_evidence_links,
        "failed": failed,
        "warnings": warnings,
    }


@beartype
@require(lambda bundle: isinstance(bundle, ProjectBundle), "bundle must be a ProjectBundle")
@require(_profile_nonempty, "profile must not be empty")
@require(_profile_supported, "profile must be a supported requirements context validation profile")
@ensure(lambda result: isinstance(result, ValidationReport))
def validate_requirement_context(
    bundle: ProjectBundle,
    *,
    profile: RequirementContextValidationProfile = "startup",
) -> ValidationReport:
    """Validate requirements context evidence usefulness for a ProjectBundle."""
    requirements = load_requirements_from_bundle(bundle)
    if not requirements:
        return _empty_requirements_report()

    coverage = inspect_requirement_context_coverage(requirements)
    violations = _missing_evidence_violations(coverage, severity=_missing_evidence_severity(profile))
    summary = _validation_summary(requirements, coverage, violations)
    return ValidationReport(
        status=_validation_status(summary["failed"], summary["warnings"]),
        violations=violations,
        summary=summary,
    )
