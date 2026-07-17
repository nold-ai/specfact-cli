"""Core requirements context adapter contracts and helpers."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal, Protocol, cast, get_args

import yaml
from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from specfact_cli.models.project import ProjectBundle
from specfact_cli.models.requirements import (
    RequirementEvidenceLinkType,
    RequirementInput,
    RequirementSourceType,
    load_requirements_input_extension,
    requirements_input_extension_payload,
)
from specfact_cli.models.validation import ValidationReport
from specfact_cli.modules.init.src.first_run_selection import resolve_profile_config


RequirementContextValidationProfile = Literal[
    "solo",
    "startup",
    "team",
    "enterprise",
    "mid_size",
    "strict",
    "solo_developer",
    "api_first_team",
    "enterprise_full_stack",
]
KNOWN_REQUIREMENT_CONTEXT_PROFILES: frozenset[str] = frozenset(get_args(RequirementContextValidationProfile))
STRICT_REQUIREMENT_CONTEXT_PROFILES: frozenset[str] = frozenset({"enterprise", "strict", "enterprise_full_stack"})
_PROFILE_RESOLUTION_ALIASES: dict[str, str] = {
    "api_first_team": "mid_size",
    "enterprise_full_stack": "enterprise",
    "solo_developer": "solo",
    "strict": "enterprise",
    "team": "mid_size",
}
_REQUIRED_FIELD_ALIASES: dict[str, str] = {
    "id": "requirement_id",
    "title": "title",
    "acceptance": "business_rules",
    "trace_links": "evidence_links",
}


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


def _source_locator_supported(source_locator: str | None) -> bool:
    return source_locator is None or type(source_locator) is str


def _optional_profile_supported(profile: str | None) -> bool:
    return profile is None or (profile.strip() != "" and profile in KNOWN_REQUIREMENT_CONTEXT_PROFILES)


def _project_root_supported(project_root: Path | None) -> bool:
    return project_root is None or isinstance(project_root, Path)


def _read_config_mapping(path: Path) -> dict[str, Any]:
    try:
        if not path.is_file():
            return {}
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _without_profile_derived_values(layer: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in layer.items() if key not in {"profile", "requirements_schema"}}


def _configured_profile(*layers: Mapping[str, object]) -> str:
    for layer in layers:
        profile = layer.get("profile")
        if isinstance(profile, str) and profile in KNOWN_REQUIREMENT_CONTEXT_PROFILES:
            return profile
    return "startup"


def _requirements_schema_fields(values: Mapping[str, Any]) -> list[str]:
    schema = values.get("requirements_schema")
    if not isinstance(schema, Mapping):
        return []
    fields = cast(Mapping[str, object], schema).get("required_fields")
    return [field for field in fields if isinstance(field, str)] if isinstance(fields, list) else []


def _resolve_requirement_profile(
    profile: RequirementContextValidationProfile | None,
    project_root: Path | None,
) -> tuple[str, dict[str, Any]]:
    root = project_root or Path.cwd()
    org_baseline = _read_config_mapping(Path.home() / ".specfact" / "config.yaml")
    repo_overlay = _read_config_mapping(root / ".specfact" / "config.yaml")
    developer_local = _read_config_mapping(root / ".specfact" / "config.local.yaml")
    configured = _configured_profile(developer_local, repo_overlay, org_baseline)
    effective_profile = profile or configured
    resolver_profile = _PROFILE_RESOLUTION_ALIASES.get(effective_profile, effective_profile)
    if profile is not None:
        org_baseline = _without_profile_derived_values(org_baseline)
        repo_overlay = _without_profile_derived_values(repo_overlay)
        developer_local = _without_profile_derived_values(developer_local)
    resolved = resolve_profile_config(
        resolver_profile,
        org_baseline=org_baseline,
        repo_overlay=repo_overlay,
        developer_local=developer_local,
    )
    return effective_profile, resolved.values


@beartype
@require(_optional_profile_supported, "profile must be a supported requirements profile when provided")
@require(_project_root_supported, "project_root must be a Path when provided")
@ensure(lambda result: isinstance(result, bool), "result must be a boolean")
def requires_native_openspec_validation(
    *,
    profile: RequirementContextValidationProfile | None = None,
    project_root: Path | None = None,
) -> bool:
    """Return whether layered policy requires native OpenSpec validation."""
    effective_profile, resolved_config = _resolve_requirement_profile(profile, project_root)
    validation_tier = _PROFILE_RESOLUTION_ALIASES.get(effective_profile, effective_profile)
    validation_value = resolved_config.get("validation")
    if not isinstance(validation_value, Mapping):
        return validation_tier == "enterprise"
    validation = cast(Mapping[str, object], validation_value)
    openspec_value = validation.get("openspec")
    if not isinstance(openspec_value, Mapping):
        return validation_tier == "enterprise"
    openspec = cast(Mapping[str, object], openspec_value)
    configured = openspec.get("require_native_validation")
    return configured if isinstance(configured, bool) else validation_tier == "enterprise"


def _is_imported_requirement(requirement: RequirementInput) -> bool:
    return any(
        source.source_type in {RequirementSourceType.OPENSPEC_CHANGE, RequirementSourceType.SPECKIT_SPEC}
        for source in requirement.sources
    )


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
            "code": "missing-evidence",
            "severity": severity,
            "message": "Requirement input has no downstream evidence links.",
            "location": f"requirements.inputs[{requirement_id}].evidence_links",
        }
        for requirement_id in coverage.missing_evidence_requirement_ids
    ]


def _scenario_unverified_violation(requirement: RequirementInput, *, severity: str) -> dict[str, str] | None:
    if not requirement.business_rules or any(
        link.link_type in {RequirementEvidenceLinkType.TEST, RequirementEvidenceLinkType.VALIDATION}
        for link in requirement.evidence_links
    ):
        return None
    rule_ids = ", ".join(rule.rule_id for rule in requirement.business_rules)
    return {
        "code": "scenario-unverified",
        "severity": severity,
        "message": f"Imported scenarios have no test or validation evidence links: {rule_ids}.",
        "location": f"requirements.inputs[{requirement.requirement_id}].business_rules",
    }


def _source_integrity_violations(
    requirement: RequirementInput,
    *,
    severity: str,
    project_root: Path,
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    for source in requirement.sources:
        if source.source_type not in {RequirementSourceType.OPENSPEC_CHANGE, RequirementSourceType.SPECKIT_SPEC}:
            continue
        source_path = Path(source.locator)
        if not source_path.is_absolute():
            source_path = project_root / source_path
        if not source_path.is_file():
            violations.append(
                {
                    "code": "source-missing",
                    "severity": severity,
                    "message": "Imported source artifact no longer exists.",
                    "location": source.locator,
                }
            )
            continue
        if source.revision and source.revision.startswith("sha256:"):
            current_revision = f"sha256:{hashlib.sha256(source_path.read_bytes()).hexdigest()}"
            if current_revision != source.revision:
                violations.append(
                    {
                        "code": "stale-import",
                        "severity": severity,
                        "message": "Imported source artifact content changed after import.",
                        "location": source.locator,
                    }
                )
    return violations


def _ambiguous_mapping_violations(identities: Mapping[str, set[str]], *, severity: str) -> list[dict[str, str]]:
    return [
        {
            "code": "ambiguous-mapping",
            "severity": severity,
            "message": "Multiple imported sources claim the same requirement identity.",
            "location": f"requirements.inputs[{requirement_id}]",
        }
        for requirement_id, locators in identities.items()
        if len(locators) > 1
    ]


def _import_gate_violations(
    requirements: Sequence[RequirementInput],
    *,
    severity: str,
    project_root: Path,
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    identities: dict[str, set[str]] = {}
    for requirement in requirements:
        if not _is_imported_requirement(requirement):
            continue
        identities.setdefault(requirement.requirement_id, set()).update(
            source.locator for source in requirement.sources
        )
        scenario_violation = _scenario_unverified_violation(requirement, severity=severity)
        if scenario_violation:
            violations.append(scenario_violation)
        violations.extend(
            _source_integrity_violations(
                requirement,
                severity=severity,
                project_root=project_root,
            )
        )
    violations.extend(_ambiguous_mapping_violations(identities, severity=severity))
    return violations


def _required_field_violations(
    requirements: Sequence[RequirementInput],
    required_fields: Sequence[str],
    *,
    severity: str,
) -> list[dict[str, str]]:
    imported_requirements = [requirement for requirement in requirements if _is_imported_requirement(requirement)]
    if not imported_requirements:
        return []

    violations: list[dict[str, str]] = []
    for field in required_fields:
        attribute = _REQUIRED_FIELD_ALIASES.get(field)
        if attribute is None:
            violations.append(
                {
                    "code": "unsupported-profile-field",
                    "severity": "info",
                    "message": "Profile field is not represented by the import-first requirements evidence schema.",
                    "location": f"requirements_schema.required_fields[{field}]",
                }
            )
            continue
        for requirement in imported_requirements:
            value = getattr(requirement, attribute)
            if not value:
                violations.append(
                    {
                        "code": "required-field-missing",
                        "severity": severity,
                        "message": f"Required evidence field '{field}' is missing.",
                        "location": f"requirements.inputs[{requirement.requirement_id}].{attribute}",
                    }
                )
    return violations


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
@require(
    _optional_profile_supported, "profile must be a supported requirements context validation profile when provided"
)
@require(_project_root_supported, "project_root must be a Path when provided")
@ensure(lambda result: isinstance(result, ValidationReport))
def validate_requirement_context(
    bundle: ProjectBundle,
    *,
    profile: RequirementContextValidationProfile | None = None,
    project_root: Path | None = None,
) -> ValidationReport:
    """Validate requirements context evidence usefulness for a ProjectBundle."""
    requirements = load_requirements_from_bundle(bundle)
    if not requirements:
        return _empty_requirements_report()

    effective_profile, resolved_config = _resolve_requirement_profile(profile, project_root)
    severity = _missing_evidence_severity(cast(RequirementContextValidationProfile, effective_profile))
    coverage = inspect_requirement_context_coverage(requirements)
    violations = _missing_evidence_violations(coverage, severity=severity)
    violations.extend(
        _import_gate_violations(
            requirements,
            severity=severity,
            project_root=project_root or Path.cwd(),
        )
    )
    violations.extend(
        _required_field_violations(
            requirements,
            _requirements_schema_fields(resolved_config),
            severity=severity,
        )
    )
    summary = _validation_summary(requirements, coverage, violations)
    return ValidationReport(
        status=_validation_status(summary["failed"], summary["warnings"]),
        violations=violations,
        summary=summary,
    )
