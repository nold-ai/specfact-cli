"""Tests for native OpenSpec and Spec Kit requirement evidence imports."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

from specfact_cli.importers.speckit_scanner import SpecKitScanner
from specfact_cli.models.plan import Product
from specfact_cli.models.project import BundleManifest, BundleVersions, ProjectBundle
from specfact_cli.models.requirements import (
    BusinessRule,
    RequirementEvidenceLink,
    RequirementEvidenceLinkType,
    RequirementInput,
    RequirementSourceReference,
    RequirementSourceType,
)
from specfact_cli.requirements import (
    attach_requirements_to_bundle,
    import_openspec_change,
    import_speckit_feature,
    validate_requirement_context,
)
from specfact_cli.requirements.context import RequirementContextValidationProfile


def _bundle() -> ProjectBundle:
    """Return a minimal bundle that can carry requirements evidence."""
    return ProjectBundle(
        manifest=BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"),
            schema_metadata=None,
            project_metadata=None,
        ),
        bundle_name="test",
        product=Product(themes=[], releases=[]),
    )


def _write_openspec_change(change_dir: Path) -> Path:
    """Create one native OpenSpec change fixture."""
    spec_file = change_dir / "specs" / "widgets" / "spec.md"
    spec_file.parent.mkdir(parents=True)
    (change_dir / "proposal.md").write_text("# Change: Widget evidence\n", encoding="utf-8")
    (change_dir / "tasks.md").write_text("# Tasks: Widget evidence\n", encoding="utf-8")
    spec_file.write_text(
        """## ADDED Requirements

### Requirement: Widget rendering

The system SHALL render a widget.

#### Scenario: Render a valid widget

- **GIVEN** a valid widget request
- **WHEN** rendering runs
- **THEN** the widget is returned
""",
        encoding="utf-8",
    )
    return spec_file


def _write_speckit_feature(feature_dir: Path) -> Path:
    """Create one native Spec Kit feature fixture."""
    spec_file = feature_dir / "spec.md"
    feature_dir.mkdir(parents=True)
    spec_file.write_text(
        """# Feature Specification: Widget rendering

## User Scenarios & Testing

### User Story 1 - Render widgets (Priority: P1)

As a user, I want widgets rendered so that I can see them.

**Acceptance Scenarios**:

1. **Given** a valid widget request, **When** rendering runs, **Then** the widget is returned

## Requirements

- **FR-001**: System MUST render a widget
""",
        encoding="utf-8",
    )
    return spec_file


def test_import_openspec_change_normalizes_scenarios_hashes_and_preserves_source(tmp_path: Path) -> None:
    """OpenSpec imports derive stable requirements without changing source artifacts."""
    change_dir = tmp_path / "openspec" / "changes" / "widget-evidence"
    spec_file = _write_openspec_change(change_dir)
    before = spec_file.read_bytes()

    result = import_openspec_change(change_dir)

    assert result.diagnostics == []
    assert [record.requirement_id for record in result.requirements] == [
        "openspec:widget-evidence:widgets:widget-rendering"
    ]
    requirement = result.requirements[0]
    assert requirement.sources[0].source_type == RequirementSourceType.OPENSPEC_CHANGE
    assert requirement.sources[0].locator == str(spec_file)
    assert requirement.sources[0].revision is not None
    assert requirement.sources[0].revision.startswith("sha256:")
    assert requirement.business_rules[0].model_dump() == {
        "rule_id": "openspec:widget-evidence:widgets:widget-rendering:render-a-valid-widget",
        "name": "Render a valid widget",
        "given": "a valid widget request",
        "when": "rendering runs",
        "then": "the widget is returned",
        "priority": None,
    }
    assert import_openspec_change(change_dir).model_dump() == result.model_dump()
    assert spec_file.read_bytes() == before


def test_import_openspec_change_preserves_wrapped_scenario_clauses(tmp_path: Path) -> None:
    """Indented Markdown continuation lines remain part of the scenario clause."""
    change_dir = tmp_path / "openspec" / "changes" / "widget-evidence"
    spec_file = _write_openspec_change(change_dir)
    spec_file.write_text(
        spec_file.read_text(encoding="utf-8").replace(
            "a valid widget request", "a valid widget request\n  with an active account"
        ),
        encoding="utf-8",
    )

    result = import_openspec_change(change_dir)

    assert result.requirements[0].business_rules[0].given == "a valid widget request with an active account"


def test_import_speckit_feature_normalizes_requirement_and_scenario(tmp_path: Path) -> None:
    """Spec Kit imports use the existing scanner while preserving G/W/T evidence."""
    feature_dir = tmp_path / "specs" / "001-widget-rendering"
    spec_file = _write_speckit_feature(feature_dir)

    result = import_speckit_feature(feature_dir)

    assert result.diagnostics == []
    assert [record.requirement_id for record in result.requirements] == ["speckit:001-widget-rendering:render-a-widget"]
    requirement = result.requirements[0]
    assert requirement.sources[0].source_type == RequirementSourceType.SPECKIT_SPEC
    assert requirement.sources[0].locator == str(spec_file)
    assert requirement.sources[0].revision is not None
    assert requirement.sources[0].revision.startswith("sha256:")
    assert requirement.business_rules[0].given == "a valid widget request"
    assert requirement.business_rules[0].when == "rendering runs"
    assert requirement.business_rules[0].then == "the widget is returned"


def test_import_speckit_feature_rejects_pristine_v01218_scaffold(tmp_path: Path) -> None:
    """The pinned official Spec Kit scaffold cannot produce placeholder evidence."""
    feature_dir = tmp_path / "specs" / "001-widget-rendering"
    spec_file = feature_dir / "spec.md"
    feature_dir.mkdir(parents=True)
    fixture = Path(__file__).parents[2] / "fixtures" / "speckit" / "spec-template-v0.12.18.md"
    spec_file.write_bytes(fixture.read_bytes())
    before = spec_file.read_bytes()

    result = import_speckit_feature(feature_dir)

    assert result.requirements == []
    assert [(diagnostic.code, diagnostic.severity) for diagnostic in result.diagnostics] == [
        ("incomplete-source-template", "error")
    ]
    assert result.diagnostics[0].source_locator == str(spec_file)
    assert spec_file.read_bytes() == before


@pytest.mark.parametrize(
    "source",
    [
        """# Feature Specification: Widget rendering

## Requirements

### Functional Requirements
""",
        """# Feature Specification: Widget rendering

## User Scenarios & Testing

### User Story 1 - Render widgets (Priority: P1)

As a user, I want widgets rendered so that I can see them.

## Requirements

### Functional Requirements

- **FR-001**: System MUST render a widget
""",
    ],
    ids=["missing-functional-requirement", "story-without-acceptance-scenario"],
)
def test_import_speckit_feature_rejects_structurally_incomplete_source(tmp_path: Path, source: str) -> None:
    """Sources missing Functional Requirements or story scenarios fail atomically."""
    feature_dir = tmp_path / "specs" / "001-widget-rendering"
    spec_file = feature_dir / "spec.md"
    feature_dir.mkdir(parents=True)
    spec_file.write_text(source, encoding="utf-8")

    result = import_speckit_feature(feature_dir)

    assert result.requirements == []
    assert [(diagnostic.code, diagnostic.severity) for diagnostic in result.diagnostics] == [
        ("source-incomplete", "error")
    ]


@pytest.mark.parametrize(
    ("returncode", "stdout"),
    [(1, '{"valid": false}'), (0, '{"valid": false}'), (0, "not-json"), (0, "")],
    ids=["validator-failure", "zero-exit-invalid-item", "malformed-json", "empty-json"],
)
@pytest.mark.parametrize("profile", ["enterprise", "strict", "enterprise_full_stack"])
def test_import_openspec_change_rejects_invalid_required_native_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    returncode: int,
    stdout: str,
    profile: RequirementContextValidationProfile,
) -> None:
    """Required-profile imports reject failed or unusable native validation results."""
    change_dir = tmp_path / "openspec" / "changes" / "widget-evidence"
    spec_file = _write_openspec_change(change_dir)
    before = spec_file.read_bytes()
    monkeypatch.setattr(
        "specfact_cli.requirements.importers.subprocess.run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout),
    )

    result = import_openspec_change(change_dir, profile=profile, project_root=tmp_path)

    assert result.requirements == []
    assert [(diagnostic.code, diagnostic.severity) for diagnostic in result.diagnostics] == [
        ("source-invalid", "error")
    ]
    assert spec_file.read_bytes() == before


def test_import_openspec_change_rejects_timed_out_required_native_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A required native validation timeout fails closed without changing the source."""
    change_dir = tmp_path / "openspec" / "changes" / "widget-evidence"
    spec_file = _write_openspec_change(change_dir)
    before = spec_file.read_bytes()
    monkeypatch.setattr(
        "specfact_cli.requirements.importers.subprocess.run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(subprocess.TimeoutExpired(cmd="openspec", timeout=10)),
    )

    result = import_openspec_change(change_dir, profile="enterprise", project_root=tmp_path)

    assert result.requirements == []
    assert [(diagnostic.code, diagnostic.severity) for diagnostic in result.diagnostics] == [
        ("source-invalid", "error")
    ]
    assert spec_file.read_bytes() == before


def test_import_openspec_change_reports_missing_required_native_validator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Enterprise imports name a missing required OpenSpec executable."""
    change_dir = tmp_path / "openspec" / "changes" / "widget-evidence"
    _write_openspec_change(change_dir)
    monkeypatch.setattr(
        "specfact_cli.requirements.importers.subprocess.run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(FileNotFoundError()),
    )

    result = import_openspec_change(change_dir, profile="enterprise", project_root=tmp_path)

    assert result.requirements == []
    assert [(diagnostic.code, diagnostic.severity) for diagnostic in result.diagnostics] == [
        ("upstream-validator-unavailable", "error")
    ]


def test_import_openspec_change_honors_layered_native_validation_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A repository policy can require validation outside the enterprise tier."""
    change_dir = tmp_path / "openspec" / "changes" / "widget-evidence"
    _write_openspec_change(change_dir)
    config_dir = tmp_path / ".specfact"
    config_dir.mkdir()
    (config_dir / "config.yaml").write_text(
        """profile: startup
validation:
  openspec:
    require_native_validation: true
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "specfact_cli.requirements.importers.subprocess.run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(args=[], returncode=1, stdout='{"valid": false}'),
    )

    result = import_openspec_change(change_dir, project_root=tmp_path)

    assert result.requirements == []
    assert result.diagnostics[0].code == "source-invalid"


def test_import_openspec_change_does_not_probe_native_validator_when_not_required(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Portable imports do not depend on an ambient OpenSpec executable."""
    change_dir = tmp_path / "openspec" / "changes" / "widget-evidence"
    _write_openspec_change(change_dir)
    monkeypatch.setattr(
        "specfact_cli.requirements.importers.subprocess.run",
        lambda *_args, **_kwargs: pytest.fail("portable import must not probe openspec"),
    )

    result = import_openspec_change(change_dir, profile="startup", project_root=tmp_path)

    assert len(result.requirements) == 1
    assert result.diagnostics == []


def test_import_speckit_feature_reports_malformed_requirement_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Malformed scanner entries remain auditable without dropping valid requirements."""
    feature_dir = tmp_path / "specs" / "001-widget-rendering"
    spec_file = _write_speckit_feature(feature_dir)
    monkeypatch.setattr(
        SpecKitScanner,
        "parse_spec_markdown",
        lambda _self, _path: {
            "feature_title": "Widget rendering",
            "requirements": ["not-a-mapping", {"text": ""}, {"text": "System MUST render a widget"}],
        },
    )

    result = import_speckit_feature(feature_dir)

    assert [requirement.requirement_id for requirement in result.requirements] == [
        "speckit:001-widget-rendering:system-must-render-a-widget"
    ]
    assert [(diagnostic.code, diagnostic.severity, diagnostic.record_index) for diagnostic in result.diagnostics] == [
        ("source-missing", "warning", 0),
        ("source-missing", "warning", 1),
    ]
    assert {diagnostic.source_locator for diagnostic in result.diagnostics} == {str(spec_file)}


def test_import_openspec_change_rejects_custom_schema_without_partial_records(tmp_path: Path) -> None:
    """Custom OpenSpec schemas fail closed until a core profile explicitly supports them."""
    change_dir = tmp_path / "openspec" / "changes" / "widget-evidence"
    _write_openspec_change(change_dir)
    (change_dir.parent.parent / "config.yaml").write_text("schema: company-custom\n", encoding="utf-8")

    result = import_openspec_change(change_dir)

    assert result.requirements == []
    assert [(diagnostic.code, diagnostic.severity) for diagnostic in result.diagnostics] == [
        ("unsupported-source-schema", "error")
    ]


def test_import_openspec_change_rejects_change_local_custom_schema_without_partial_records(tmp_path: Path) -> None:
    """A change-local OpenSpec schema declaration is as authoritative as project configuration."""
    change_dir = tmp_path / "openspec" / "changes" / "widget-evidence"
    _write_openspec_change(change_dir)
    (change_dir / ".openspec.yaml").write_text("schema: company-custom\n", encoding="utf-8")

    result = import_openspec_change(change_dir)

    assert result.requirements == []
    assert result.diagnostics[0].code == "unsupported-source-schema"


@pytest.mark.parametrize("schema_value", ["123", "true", "null", "{profile: default}"])
def test_import_openspec_change_rejects_non_string_schema_without_partial_records(
    tmp_path: Path,
    schema_value: str,
) -> None:
    """Malformed schema declarations cannot fall through to the default profile."""
    change_dir = tmp_path / "openspec" / "changes" / "widget-evidence"
    _write_openspec_change(change_dir)
    (change_dir.parent.parent / "config.yaml").write_text(f"schema: {schema_value}\n", encoding="utf-8")

    result = import_openspec_change(change_dir)

    assert result.requirements == []
    assert result.diagnostics[0].code == "unsupported-source-schema"


def test_import_openspec_change_rejects_invalid_utf8_schema_without_partial_records(tmp_path: Path) -> None:
    """Unreadable schema configuration fails closed instead of crashing the import."""
    change_dir = tmp_path / "openspec" / "changes" / "widget-evidence"
    _write_openspec_change(change_dir)
    (change_dir.parent.parent / "config.yaml").write_bytes(b"schema: \xff\n")

    result = import_openspec_change(change_dir)

    assert result.requirements == []
    assert result.diagnostics[0].code == "unsupported-source-schema"


@pytest.mark.parametrize(
    "customization_root",
    [
        Path(".specify/templates/overrides"),
        Path(".specify/presets"),
        Path(".specify/extensions"),
    ],
)
def test_import_speckit_feature_rejects_template_customization_without_partial_records(
    tmp_path: Path,
    customization_root: Path,
) -> None:
    """Spec Kit override roots fail closed rather than being parsed with default assumptions."""
    feature_dir = tmp_path / "specs" / "001-widget-rendering"
    _write_speckit_feature(feature_dir)
    (tmp_path / customization_root).mkdir(parents=True)

    result = import_speckit_feature(feature_dir)

    assert result.requirements == []
    assert [(diagnostic.code, diagnostic.severity) for diagnostic in result.diagnostics] == [
        ("unsupported-source-schema", "error")
    ]


def test_imports_reject_unknown_default_profile_markers_without_partial_records(tmp_path: Path) -> None:
    """Unrecognized Markdown markers cannot silently produce an empty or partial import."""
    change_dir = tmp_path / "openspec" / "changes" / "widget-evidence"
    open_spec_file = _write_openspec_change(change_dir)
    open_spec_file.write_text("## ADDED Functional Requirements\n", encoding="utf-8")
    feature_dir = tmp_path / "specs" / "001-widget-rendering"
    speckit_file = _write_speckit_feature(feature_dir)
    speckit_file.write_text("# Product Requirements\n\n- Render a widget\n", encoding="utf-8")

    openspec_result = import_openspec_change(change_dir)
    speckit_result = import_speckit_feature(feature_dir)

    assert openspec_result.requirements == []
    assert speckit_result.requirements == []
    assert openspec_result.diagnostics[0].code == "unsupported-source-schema"
    assert speckit_result.diagnostics[0].code == "unsupported-source-schema"


def test_importers_disambiguate_duplicate_derived_requirement_ids(tmp_path: Path) -> None:
    """Repeated upstream titles and summaries retain distinct deterministic identities."""
    change_dir = tmp_path / "openspec" / "changes" / "widget-evidence"
    openspec_spec = _write_openspec_change(change_dir)
    openspec_spec.write_text(
        openspec_spec.read_text(encoding="utf-8")
        + """

### Requirement: Widget rendering

The system SHALL render a fallback widget.

#### Scenario: Render a fallback widget

- **GIVEN** a fallback widget request
- **WHEN** rendering runs
- **THEN** the fallback widget is returned
""",
        encoding="utf-8",
    )
    feature_dir = tmp_path / "specs" / "001-widget-rendering"
    speckit_spec = _write_speckit_feature(feature_dir)
    speckit_spec.write_text(
        speckit_spec.read_text(encoding="utf-8") + "\n- **FR-002**: System MUST render a widget\n",
        encoding="utf-8",
    )

    openspec_result = import_openspec_change(change_dir)
    speckit_result = import_speckit_feature(feature_dir)

    assert [record.requirement_id for record in openspec_result.requirements] == [
        "openspec:widget-evidence:widgets:widget-rendering",
        "openspec:widget-evidence:widgets:widget-rendering-2",
    ]
    assert [record.requirement_id for record in speckit_result.requirements] == [
        "speckit:001-widget-rendering:render-a-widget",
        "speckit:001-widget-rendering:render-a-widget-2",
    ]


def test_validation_reports_import_gates_and_profile_required_field_advisories(tmp_path: Path) -> None:
    """Validation distinguishes import failures from unsupported profile metadata."""
    source_file = tmp_path / "missing-after-import.md"
    requirement = _imported_requirement(
        source_file,
        revision="sha256:0123456789abcdef",
        with_test_link=True,
    )
    bundle = attach_requirements_to_bundle(_bundle(), [requirement])

    report = validate_requirement_context(bundle, profile="enterprise", project_root=tmp_path)

    assert report.status == "failed"
    assert {violation["code"] for violation in report.violations} >= {
        "source-missing",
        "unsupported-profile-field",
    }
    assert all(
        violation["code"] != "required-field-missing"
        or violation["location"] != f"requirements.inputs[{requirement.requirement_id}].owner"
        for violation in report.violations
    )


def _imported_requirement(source_file: Path, *, revision: str, with_test_link: bool) -> RequirementInput:
    """Return an imported requirement fixture with one G/W/T scenario."""
    evidence_links = (
        [
            RequirementEvidenceLink(
                link_type=RequirementEvidenceLinkType.TEST,
                target="tests/unit/requirements/test_upstream_evidence_imports.py",
            )
        ]
        if with_test_link
        else []
    )
    return RequirementInput(
        schema_version="1",
        requirement_id="openspec:widget-evidence:widgets:widget-rendering",
        title="Widget rendering",
        sources=[
            RequirementSourceReference(
                source_type=RequirementSourceType.OPENSPEC_CHANGE,
                locator=str(source_file),
                revision=revision,
            )
        ],
        business_rules=[
            BusinessRule(
                rule_id="rule-1",
                name="Render a valid widget",
                given="a valid widget request",
                when="rendering runs",
                then="the widget is returned",
            )
        ],
        evidence_links=evidence_links,
    )


def test_validation_reports_scenario_stale_and_ambiguous_import_gates(tmp_path: Path) -> None:
    """Every deterministic import gate is surfaced without heuristic matching."""
    source_a = tmp_path / "source-a.md"
    source_b = tmp_path / "source-b.md"
    source_a.write_text("source A", encoding="utf-8")
    source_b.write_text("source B", encoding="utf-8")
    requirements = [
        _imported_requirement(source_a, revision="sha256:outdated", with_test_link=False),
        _imported_requirement(source_b, revision="sha256:outdated", with_test_link=True),
    ]
    bundle = attach_requirements_to_bundle(_bundle(), requirements)

    report = validate_requirement_context(bundle, profile="solo", project_root=tmp_path)

    assert {violation["code"] for violation in report.violations} >= {
        "scenario-unverified",
        "stale-import",
        "ambiguous-mapping",
    }


def test_validation_resolves_relative_source_locator_from_project_root(tmp_path: Path) -> None:
    """Validation uses project_root rather than the process working directory for relative locators."""
    source_file = tmp_path / "source.md"
    source_file.write_text("source", encoding="utf-8")
    requirement = _imported_requirement(
        source_file,
        revision=f"sha256:{hashlib.sha256(source_file.read_bytes()).hexdigest()}",
        with_test_link=True,
    ).model_copy(
        update={
            "sources": [
                RequirementSourceReference(
                    source_type=RequirementSourceType.OPENSPEC_CHANGE,
                    locator="source.md",
                    revision=f"sha256:{hashlib.sha256(source_file.read_bytes()).hexdigest()}",
                )
            ]
        }
    )

    report = validate_requirement_context(
        attach_requirements_to_bundle(_bundle(), [requirement]),
        profile="solo",
        project_root=tmp_path,
    )

    assert report.status == "passed"


def test_validation_ignores_malformed_optional_config(tmp_path: Path) -> None:
    """Unreadable optional configuration cannot prevent requirements validation."""
    source_file = tmp_path / "source.md"
    source_file.write_text("source", encoding="utf-8")
    config_dir = tmp_path / ".specfact"
    config_dir.mkdir()
    (config_dir / "config.yaml").write_text("profile: [\n", encoding="utf-8")
    requirement = _imported_requirement(
        source_file,
        revision=f"sha256:{hashlib.sha256(source_file.read_bytes()).hexdigest()}",
        with_test_link=True,
    )

    report = validate_requirement_context(
        attach_requirements_to_bundle(_bundle(), [requirement]),
        profile="solo",
        project_root=tmp_path,
    )

    assert report.status == "passed"


def test_validation_ignores_invalid_utf8_optional_config(tmp_path: Path) -> None:
    """Binary optional configuration cannot prevent requirements validation."""
    source_file = tmp_path / "source.md"
    source_file.write_text("source", encoding="utf-8")
    config_dir = tmp_path / ".specfact"
    config_dir.mkdir()
    (config_dir / "config.yaml").write_bytes(b"profile: \xff\n")
    requirement = _imported_requirement(
        source_file,
        revision=f"sha256:{hashlib.sha256(source_file.read_bytes()).hexdigest()}",
        with_test_link=True,
    )

    report = validate_requirement_context(
        attach_requirements_to_bundle(_bundle(), [requirement]), project_root=tmp_path
    )

    assert report.status == "passed"


def test_omitted_profile_uses_layered_configuration_and_explicit_profile_wins(tmp_path: Path) -> None:
    """Profile resolution changes severity only when callers do not specify one."""
    source_file = tmp_path / "source.md"
    source_file.write_text("source", encoding="utf-8")
    config_dir = tmp_path / ".specfact"
    config_dir.mkdir()
    (config_dir / "config.yaml").write_text(
        "profile: enterprise\nrequirements_schema:\n  required_fields: [owner]\n",
        encoding="utf-8",
    )
    bundle = attach_requirements_to_bundle(
        _bundle(),
        [_imported_requirement(source_file, revision="sha256:outdated", with_test_link=False)],
    )

    configured_report = validate_requirement_context(bundle, project_root=tmp_path)
    explicit_report = validate_requirement_context(bundle, profile="solo", project_root=tmp_path)

    assert configured_report.status == "failed"
    assert explicit_report.status == "warnings"
    assert not any(violation["code"] == "required-field-missing" for violation in explicit_report.violations)
