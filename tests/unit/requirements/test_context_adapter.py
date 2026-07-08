"""Tests for requirements context adapter helpers."""

from __future__ import annotations

import sys
from typing import Any, cast

import pytest
from beartype.roar import BeartypeCallHintParamViolation

from specfact_cli.models.plan import Product
from specfact_cli.models.project import BundleManifest, BundleVersions, ProjectBundle
from specfact_cli.models.requirements import (
    RequirementEvidenceLink,
    RequirementEvidenceLinkType,
    RequirementInput,
    RequirementSourceReference,
    RequirementSourceType,
)
from specfact_cli.requirements.context import (
    attach_requirements_to_bundle,
    inspect_requirement_context_coverage,
    load_requirements_from_bundle,
    normalize_requirement_records,
    validate_requirement_context,
)


def _source() -> RequirementSourceReference:
    return RequirementSourceReference(
        source_type=RequirementSourceType.ISSUE,
        locator="https://github.com/nold-ai/specfact-cli/issues/239",
        title="Requirements Context Adapter Commands",
    )


def _requirement(requirement_id: str = "REQ-239") -> RequirementInput:
    return RequirementInput(
        requirement_id=requirement_id,
        schema_version="1",
        title="Requirement context is source attributed",
        sources=[_source()],
        evidence_links=[
            RequirementEvidenceLink(
                link_type=RequirementEvidenceLinkType.TEST,
                target="tests/unit/requirements/test_context_adapter.py",
            )
        ],
    )


def _bundle() -> ProjectBundle:
    manifest = BundleManifest(
        versions=BundleVersions(schema="1.0", project="0.1.0"),
        schema_metadata=None,
        project_metadata=None,
    )
    return ProjectBundle(manifest=manifest, bundle_name="test", product=Product(themes=[], releases=[]))


def test_normalize_requirement_records_preserves_valid_records_and_bounds_diagnostics() -> None:
    """Normalization keeps valid records and reports malformed records deterministically."""
    result = normalize_requirement_records(
        [
            _requirement().model_dump(mode="json"),
            {"requirement_id": "REQ-BROKEN", "schema_version": "1", "title": "Missing sources"},
            {"schema_version": "1", "title": "Missing id and sources"},
        ],
        source_locator="fixtures/requirements.yaml",
    )

    assert [record.requirement_id for record in result.requirements] == ["REQ-239"]
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "invalid_requirement_input",
        "invalid_requirement_input",
    ]
    assert [diagnostic.requirement_id for diagnostic in result.diagnostics] == ["REQ-BROKEN", None]
    assert [diagnostic.record_index for diagnostic in result.diagnostics] == [1, 2]
    assert {diagnostic.source_locator for diagnostic in result.diagnostics} == {"fixtures/requirements.yaml"}


def test_normalize_requirement_records_preserves_diagnostics_when_crosshair_loaded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Diagnostic identity fields must not depend on test-tool imports."""
    monkeypatch.setitem(sys.modules, "crosshair", object())

    result = normalize_requirement_records(
        [{"requirement_id": "REQ-BROKEN", "schema_version": "1", "title": "Missing sources"}],
        source_locator="fixtures/requirements.yaml",
    )

    assert len(result.diagnostics) == 1
    assert result.diagnostics[0].requirement_id == "REQ-BROKEN"
    assert result.diagnostics[0].source_locator == "fixtures/requirements.yaml"


def test_bundle_helpers_attach_and_load_requirements_input_extension() -> None:
    """Normalized inputs are stored through the existing ProjectBundle extension namespace."""
    bundle = _bundle()
    requirement = _requirement()

    returned = attach_requirements_to_bundle(bundle, [requirement])

    assert returned is bundle
    loaded = load_requirements_from_bundle(bundle)
    assert [record.requirement_id for record in loaded] == ["REQ-239"]


def test_validate_requirement_context_reports_profile_aware_evidence_gaps() -> None:
    """Enterprise validation treats missing evidence links as failed evidence usefulness."""
    requirement = RequirementInput(
        requirement_id="REQ-NO-EVIDENCE",
        schema_version="1",
        title="Requirement lacks downstream evidence",
        sources=[_source()],
    )
    bundle = attach_requirements_to_bundle(_bundle(), [requirement])

    report = validate_requirement_context(bundle, profile="enterprise")

    assert report.status == "failed"
    assert report.summary == {"total_checks": 2, "passed": 1, "failed": 1, "warnings": 0}
    assert report.violations[0]["severity"] == "error"
    assert report.violations[0]["location"] == "requirements.inputs[REQ-NO-EVIDENCE].evidence_links"


def test_validate_requirement_context_rejects_unknown_profile() -> None:
    """Profile selection uses a shared bounded vocabulary to catch typos."""
    bundle = attach_requirements_to_bundle(_bundle(), [_requirement()])

    with pytest.raises(BeartypeCallHintParamViolation):
        validate_requirement_context(bundle, profile=cast(Any, "enterprize"))


def test_inspect_requirement_context_coverage_is_machine_readable() -> None:
    """Coverage inspection reports counts downstream command handlers can serialize."""
    requirement_with_repeated_test_links = _requirement("REQ-WITH-EVIDENCE")
    requirement_with_repeated_test_links.evidence_links.append(
        RequirementEvidenceLink(
            link_type=RequirementEvidenceLinkType.TEST,
            target="tests/unit/requirements/test_context_adapter.py::duplicate",
        )
    )
    requirements = [
        requirement_with_repeated_test_links,
        RequirementInput(
            requirement_id="REQ-WITHOUT-EVIDENCE",
            schema_version="1",
            title="Requirement lacks downstream evidence",
            sources=[_source()],
        ),
    ]

    coverage = inspect_requirement_context_coverage(requirements)

    assert coverage.model_dump() == {
        "total_requirements": 2,
        "with_business_rules": 0,
        "with_constraints": 0,
        "with_evidence_links": 1,
        "with_architecture_links": 0,
        "with_code_links": 0,
        "with_test_links": 1,
        "missing_evidence_requirement_ids": ["REQ-WITHOUT-EVIDENCE"],
    }
