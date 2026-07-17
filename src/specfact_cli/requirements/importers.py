"""Read-only normalizers for native OpenSpec and Spec Kit requirement evidence."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import cast

import yaml
from beartype import beartype
from icontract import ensure, require

from specfact_cli.adapters.openspec_parser import OpenSpecParser
from specfact_cli.importers.speckit_scanner import SpecKitScanner
from specfact_cli.models.requirements import (
    BusinessRule,
    RequirementInput,
    RequirementSourceReference,
    RequirementSourceType,
)
from specfact_cli.requirements.context import (
    RequirementContextDiagnostic,
    RequirementContextDiagnosticSeverity,
    RequirementContextImportResult,
    RequirementContextValidationProfile,
    requires_native_openspec_validation,
)


_DEFAULT_OPENSPEC_SCHEMA = "spec-driven"
_OPENSPEC_REQUIREMENT_PATTERN = re.compile(r"^### Requirement:\s+.+$", re.MULTILINE)
_OPENSPEC_SCENARIO_PATTERN = re.compile(r"^#### Scenario:\s+.+$", re.MULTILINE)
_SPECKIT_TITLE_PATTERN = re.compile(r"^# Feature Specification:\s+.+$", re.MULTILINE)
_SPECKIT_REQUIREMENT_PATTERN = re.compile(r"^\s*-?\s*\*\*FR-\d+\*\*:\s*System MUST\s+.+$", re.MULTILINE)
_SPECKIT_CUSTOMIZATION_ROOTS = (
    Path(".specify/templates/overrides"),
    Path(".specify/presets"),
    Path(".specify/extensions"),
)
_OPENSPEC_VALIDATOR_TIMEOUT_SECONDS = 10
_SPECKIT_TEMPLATE_MARKERS = (
    "# Feature Specification: [FEATURE NAME]",
    "**Feature Branch**: `[###-feature-name]`",
    '**Input**: User description: "$ARGUMENTS"',
    "### User Story 1 - [Brief Title] (Priority: P1)",
    "[Describe this user journey in plain language]",
    "- **FR-001**: System MUST [specific capability,",
)
_SPECKIT_NEEDS_CLARIFICATION_MARKER = "[NEEDS CLARIFICATION:"
_SPECKIT_USER_STORY_PATTERN = re.compile(r"^### User Story\s+\d+\s+-\s+.+$", re.MULTILINE)


def _slug(value: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", value.lower())).strip("-") or "requirement"


def _unique_requirement_id(base_id: str, seen_ids: set[str]) -> str:
    candidate = base_id
    ordinal = 2
    while candidate in seen_ids:
        candidate = f"{base_id}-{ordinal}"
        ordinal += 1
    seen_ids.add(candidate)
    return candidate


def _source_revision(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _scenario_rules(requirement_id: str, content: str) -> list[BusinessRule]:
    rules: list[BusinessRule] = []
    scenario_pattern = re.compile(
        r"^#### Scenario:\s*(.+?)\n(.*?)(?=^#### Scenario:|^### Requirement:|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    for match in scenario_pattern.finditer(content):
        name = match.group(1).strip()
        body = match.group(2)
        clauses: dict[str, str] = {}
        for clause in ("given", "when", "then"):
            clause_match = re.search(
                rf"^- \*\*{clause.upper()}\*\*\s+([^\n]+(?:\n[ \t]+[^\n]+)*)",
                body,
                re.MULTILINE | re.IGNORECASE,
            )
            if clause_match:
                clauses[clause] = " ".join(clause_match.group(1).split())
        if len(clauses) == 3:
            rules.append(
                BusinessRule(
                    rule_id=f"{requirement_id}:{_slug(name)}",
                    name=name,
                    given=clauses["given"],
                    when=clauses["when"],
                    then=clauses["then"],
                )
            )
    return rules


def _speckit_rules(requirement_id: str, content: str) -> list[BusinessRule]:
    rules: list[BusinessRule] = []
    pattern = re.compile(
        r"\*\*Given\*\*\s+(.+?),\s*\*\*When\*\*\s+(.+?),\s*\*\*Then\*\*\s+(.+?)(?=\n|$)",
        re.IGNORECASE,
    )
    for index, match in enumerate(pattern.finditer(content), start=1):
        rules.append(
            BusinessRule(
                rule_id=f"{requirement_id}:scenario-{index}",
                name=f"Acceptance scenario {index}",
                given=match.group(1).strip(),
                when=match.group(2).strip(),
                then=match.group(3).strip(),
            )
        )
    return rules


def _missing_source_result(source: Path, source_type: RequirementSourceType) -> RequirementContextImportResult:
    return RequirementContextImportResult(
        diagnostics=[
            RequirementContextDiagnostic(
                severity=RequirementContextDiagnosticSeverity.ERROR,
                code="source-missing",
                message=f"Required {source_type.value} source does not exist.",
                source_locator=str(source),
            )
        ]
    )


def _unsupported_source_result(
    source: Path,
    source_type: RequirementSourceType,
    message: str,
) -> RequirementContextImportResult:
    return RequirementContextImportResult(
        diagnostics=[
            RequirementContextDiagnostic(
                severity=RequirementContextDiagnosticSeverity.ERROR,
                code="unsupported-source-schema",
                message=message,
                source_locator=str(source),
            )
        ]
    )


def _readiness_error_result(
    source: Path,
    source_type: RequirementSourceType,
    code: str,
    message: str,
) -> RequirementContextImportResult:
    return RequirementContextImportResult(
        diagnostics=[
            RequirementContextDiagnostic(
                severity=RequirementContextDiagnosticSeverity.ERROR,
                code=code,
                message=message,
                source_locator=str(source),
            )
        ]
    )


def _load_schema_name(path: Path) -> str | None:
    try:
        if not path.is_file():
            return None
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return "<invalid>"
    if not isinstance(data, dict):
        return "<invalid>"
    schema = cast(dict[str, object], data).get("schema")
    return "<invalid>" if "schema" in data and not isinstance(schema, str) else cast(str | None, schema)


def _openspec_compatibility_error(change_dir: Path, spec_paths: list[Path]) -> RequirementContextImportResult | None:
    config_paths = (change_dir.parent.parent / "config.yaml", change_dir / ".openspec.yaml")
    for config_path in config_paths:
        schema = _load_schema_name(config_path)
        if schema is not None and schema != _DEFAULT_OPENSPEC_SCHEMA:
            return _unsupported_source_result(
                config_path,
                RequirementSourceType.OPENSPEC_CHANGE,
                "OpenSpec schema is not supported by the default evidence import profile.",
            )
    if not spec_paths:
        return _unsupported_source_result(
            change_dir,
            RequirementSourceType.OPENSPEC_CHANGE,
            "OpenSpec change has no default-profile spec.md artifact to import.",
        )
    for spec_path in spec_paths:
        content = spec_path.read_text(encoding="utf-8")
        if not (_OPENSPEC_REQUIREMENT_PATTERN.search(content) and _OPENSPEC_SCENARIO_PATTERN.search(content)):
            return _unsupported_source_result(
                spec_path,
                RequirementSourceType.OPENSPEC_CHANGE,
                "OpenSpec artifact does not match the supported default requirement/scenario Markdown profile.",
            )
    return None


def _speckit_project_root(feature_dir: Path) -> Path | None:
    for directory in (feature_dir.parent, *feature_dir.parents):
        if (directory / ".specify").is_dir():
            return directory
    return None


def _speckit_compatibility_error(
    feature_dir: Path, spec_path: Path, content: str
) -> RequirementContextImportResult | None:
    project_root = _speckit_project_root(feature_dir)
    if project_root:
        for customization_root in _SPECKIT_CUSTOMIZATION_ROOTS:
            path = project_root / customization_root
            if path.exists():
                return _unsupported_source_result(
                    path,
                    RequirementSourceType.SPECKIT_SPEC,
                    "Spec Kit template customization is not supported by the default evidence import profile.",
                )
    if not (_SPECKIT_TITLE_PATTERN.search(content) and _SPECKIT_REQUIREMENT_PATTERN.search(content)):
        return _unsupported_source_result(
            spec_path,
            RequirementSourceType.SPECKIT_SPEC,
            "Spec Kit artifact does not match the supported default Markdown template profile.",
        )
    return None


def _speckit_readiness_error(spec_path: Path, content: str) -> RequirementContextImportResult | None:
    if not _SPECKIT_TITLE_PATTERN.search(content):
        return None
    if any(marker in content for marker in _SPECKIT_TEMPLATE_MARKERS) or _SPECKIT_NEEDS_CLARIFICATION_MARKER in content:
        return _readiness_error_result(
            spec_path,
            RequirementSourceType.SPECKIT_SPEC,
            "incomplete-source-template",
            "Spec Kit source still contains a supported official scaffold placeholder.",
        )
    if not _SPECKIT_REQUIREMENT_PATTERN.search(content):
        return _readiness_error_result(
            spec_path,
            RequirementSourceType.SPECKIT_SPEC,
            "source-incomplete",
            "Spec Kit source has no substantive Functional Requirement.",
        )
    if _SPECKIT_USER_STORY_PATTERN.search(content) and not _speckit_rules("readiness", content):
        return _readiness_error_result(
            spec_path,
            RequirementSourceType.SPECKIT_SPEC,
            "source-incomplete",
            "Spec Kit source has user stories but no meaningful Given/When/Then acceptance scenario.",
        )
    return None


def _openspec_native_validation_error(
    change_dir: Path,
    *,
    profile: RequirementContextValidationProfile | None,
    project_root: Path | None,
) -> RequirementContextImportResult | None:
    if not requires_native_openspec_validation(profile=profile, project_root=project_root):
        return None
    try:
        completed = subprocess.run(
            ["openspec", "validate", change_dir.name, "--strict", "--json"],
            cwd=change_dir.parents[2],
            capture_output=True,
            check=False,
            text=True,
            timeout=_OPENSPEC_VALIDATOR_TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        return _readiness_error_result(
            change_dir,
            RequirementSourceType.OPENSPEC_CHANGE,
            "upstream-validator-unavailable",
            "Required native OpenSpec validator is unavailable.",
        )
    except (OSError, subprocess.TimeoutExpired):
        return _readiness_error_result(
            change_dir,
            RequirementSourceType.OPENSPEC_CHANGE,
            "source-invalid",
            "Required native OpenSpec validation did not complete successfully.",
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        payload = None
    if completed.returncode != 0 or not _native_openspec_result_valid(payload, change_dir.name):
        return _readiness_error_result(
            change_dir,
            RequirementSourceType.OPENSPEC_CHANGE,
            "source-invalid",
            "Required native OpenSpec validation reported the source invalid.",
        )
    return None


def _native_openspec_result_valid(payload: object, change_name: str) -> bool:
    if not isinstance(payload, dict):
        return False
    result = cast(dict[str, object], payload)
    items = result.get("items")
    if not isinstance(items, list):
        return False
    return any(
        isinstance(item, dict)
        and cast(dict[str, object], item).get("id") == change_name
        and cast(dict[str, object], item).get("valid") is True
        for item in items
    )


def _import_result_has_requirements(result: RequirementContextImportResult) -> bool:
    return all(isinstance(record, RequirementInput) for record in result.requirements)


@require(lambda change_dir: isinstance(change_dir, Path), "change_dir must be a Path")
@require(lambda profile: profile is None or isinstance(profile, str), "profile must be text when provided")
@require(
    lambda project_root: project_root is None or isinstance(project_root, Path),
    "project_root must be a Path when provided",
)
@ensure(_import_result_has_requirements)
@beartype
def import_openspec_change(
    change_dir: Path,
    *,
    profile: RequirementContextValidationProfile | None = None,
    project_root: Path | None = None,
) -> RequirementContextImportResult:
    """Normalize one native OpenSpec change directory without modifying it."""
    if not change_dir.is_dir():
        return _missing_source_result(change_dir, RequirementSourceType.OPENSPEC_CHANGE)

    native_validation_error = _openspec_native_validation_error(
        change_dir,
        profile=profile,
        project_root=project_root,
    )
    if native_validation_error:
        return native_validation_error

    spec_paths = sorted((change_dir / "specs").glob("*/spec.md"))
    compatibility_error = _openspec_compatibility_error(change_dir, spec_paths)
    if compatibility_error:
        return compatibility_error

    parser = OpenSpecParser()
    requirements: list[RequirementInput] = []
    diagnostics: list[RequirementContextDiagnostic] = []
    seen_requirement_ids: set[str] = set()
    for spec_path in spec_paths:
        parsed = parser.parse_change_spec_delta(spec_path)
        if parsed is None:
            diagnostics.append(
                RequirementContextDiagnostic(
                    severity=RequirementContextDiagnosticSeverity.ERROR,
                    code="source-missing",
                    message="OpenSpec delta specification could not be read.",
                    source_locator=str(spec_path),
                )
            )
            continue
        content = str(parsed.get("raw_content", ""))
        capability = spec_path.parent.name
        source = RequirementSourceReference(
            source_type=RequirementSourceType.OPENSPEC_CHANGE,
            locator=str(spec_path),
            title=capability,
            revision=_source_revision(spec_path),
        )
        for match in re.finditer(
            r"^### Requirement:\s*(.+?)\n(.*?)(?=^### Requirement:|\Z)", content, re.MULTILINE | re.DOTALL
        ):
            title = match.group(1).strip()
            requirement_id = _unique_requirement_id(
                f"openspec:{change_dir.name}:{capability}:{_slug(title)}",
                seen_requirement_ids,
            )
            body = match.group(2).strip()
            summary = body.split("#### Scenario:", maxsplit=1)[0].strip() or None
            requirements.append(
                RequirementInput(
                    schema_version="1",
                    requirement_id=requirement_id,
                    title=title,
                    summary=summary,
                    sources=[source],
                    business_rules=_scenario_rules(requirement_id, body),
                )
            )
    return RequirementContextImportResult(requirements=requirements, diagnostics=diagnostics)


@require(lambda feature_dir: isinstance(feature_dir, Path), "feature_dir must be a Path")
@ensure(_import_result_has_requirements)
@beartype
def import_speckit_feature(feature_dir: Path) -> RequirementContextImportResult:
    """Normalize one native Spec Kit feature directory without modifying it."""
    spec_path = feature_dir / "spec.md"
    if not feature_dir.is_dir() or not spec_path.is_file():
        return _missing_source_result(feature_dir, RequirementSourceType.SPECKIT_SPEC)

    content = spec_path.read_text(encoding="utf-8")
    readiness_error = _speckit_readiness_error(spec_path, content)
    if readiness_error:
        return readiness_error
    compatibility_error = _speckit_compatibility_error(feature_dir, spec_path, content)
    if compatibility_error:
        return compatibility_error

    parsed = SpecKitScanner(feature_dir.parent).parse_spec_markdown(spec_path)
    if parsed is None:
        return _missing_source_result(spec_path, RequirementSourceType.SPECKIT_SPEC)

    source = RequirementSourceReference(
        source_type=RequirementSourceType.SPECKIT_SPEC,
        locator=str(spec_path),
        title=str(parsed.get("feature_title") or feature_dir.name),
        revision=_source_revision(spec_path),
    )
    requirements: list[RequirementInput] = []
    seen_requirement_ids: set[str] = set()
    raw_requirements = cast(list[object], parsed.get("requirements", []))
    diagnostics: list[RequirementContextDiagnostic] = []
    for index, raw_requirement in enumerate(raw_requirements):
        if not isinstance(raw_requirement, dict):
            diagnostics.append(
                RequirementContextDiagnostic(
                    severity=RequirementContextDiagnosticSeverity.WARNING,
                    code="source-missing",
                    message="Spec Kit requirement entry is not a mapping.",
                    source_locator=str(spec_path),
                    record_index=index,
                )
            )
            continue
        requirement_values = cast(dict[str, object], raw_requirement)
        summary = str(requirement_values.get("text", "")).strip()
        if not summary:
            diagnostics.append(
                RequirementContextDiagnostic(
                    severity=RequirementContextDiagnosticSeverity.WARNING,
                    code="source-missing",
                    message="Spec Kit requirement entry has no text.",
                    source_locator=str(spec_path),
                    record_index=index,
                )
            )
            continue
        requirement_id = _unique_requirement_id(
            f"speckit:{feature_dir.name}:{_slug(summary)}",
            seen_requirement_ids,
        )
        requirements.append(
            RequirementInput(
                schema_version="1",
                requirement_id=requirement_id,
                title=summary[:1].upper() + summary[1:],
                summary=summary,
                sources=[source],
                business_rules=_speckit_rules(requirement_id, content),
            )
        )
    return RequirementContextImportResult(requirements=requirements, diagnostics=diagnostics)
