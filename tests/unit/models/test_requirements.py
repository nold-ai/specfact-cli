"""Tests for requirement evidence input models."""

from __future__ import annotations

import json

import pytest
from icontract import ViolationError
from pydantic import ValidationError

from specfact_cli.models.requirements import (
    BusinessRule,
    RequirementCompletenessFinding,
    RequirementCompletenessSeverity,
    RequirementConstraint,
    RequirementConstraintType,
    RequirementEvidenceLink,
    RequirementEvidenceLinkType,
    RequirementInput,
    RequirementSourceReference,
    RequirementSourceType,
    load_requirements_input_extension,
    requirements_input_extension_payload,
)


def test_requirement_input_serializes_source_backed_evidence() -> None:
    """Requirement inputs preserve source references and evidence links."""
    requirement = RequirementInput(
        requirement_id="REQ-123",
        schema_version="1",
        title="Checkout preserves selected currency",
        sources=[
            RequirementSourceReference(
                source_type=RequirementSourceType.ISSUE,
                locator="https://github.com/nold-ai/specfact-cli/issues/238",
                title="Requirements Evidence Input Model",
            )
        ],
        business_rules=[
            BusinessRule(
                rule_id="RULE-1",
                name="Currency stays stable",
                given="a shopper selected EUR",
                when="checkout validation runs",
                then="the evidence references EUR as the expected currency",
                priority="must",
            )
        ],
        constraints=[
            RequirementConstraint(
                constraint_id="CON-1",
                constraint_type=RequirementConstraintType.COMPLIANCE,
                statement="Currency evidence must be auditable",
                validation_criteria=["evidence link exists"],
            )
        ],
        evidence_links=[
            RequirementEvidenceLink(
                link_type=RequirementEvidenceLinkType.TEST,
                target="tests/unit/models/test_requirements.py::test_requirement_input_serializes_source_backed_evidence",
                relation="validated-by",
            )
        ],
    )

    dumped = json.loads(requirement.model_dump_json())

    assert dumped["requirement_id"] == "REQ-123"
    assert dumped["sources"][0]["source_type"] == "issue"
    assert dumped["business_rules"][0]["rule_id"] == "RULE-1"
    assert dumped["constraints"][0]["constraint_type"] == "compliance"
    assert dumped["evidence_links"][0]["link_type"] == "test"


def test_requirement_input_requires_schema_version() -> None:
    """Requirement input validation rejects artifacts without schema_version."""
    with pytest.raises(ValidationError, match="schema_version"):
        RequirementInput.model_validate(
            {
                "requirement_id": "REQ-123",
                "title": "Missing schema version",
                "sources": [{"source_type": "issue", "locator": "https://example.test/issue/123"}],
            }
        )


def test_requirement_input_rejects_unknown_schema_version() -> None:
    """Requirement input validation rejects unsupported per-record schema versions."""
    with pytest.raises(ValidationError, match="schema_version"):
        RequirementInput.model_validate(
            {
                "requirement_id": "REQ-123",
                "schema_version": "999",
                "title": "Unsupported schema version",
                "sources": [{"source_type": "issue", "locator": "https://example.test/1"}],
            }
        )


def test_requirement_input_requires_at_least_one_source_reference() -> None:
    """Requirement inputs must preserve at least one upstream source reference."""
    with pytest.raises(ValidationError, match="sources"):
        RequirementInput(requirement_id="REQ-123", schema_version="1", title="No source", sources=[])


def test_profile_completeness_findings_are_advisory_evidence() -> None:
    """Profile findings are stored as evidence without blocking model creation."""
    requirement = RequirementInput(
        requirement_id="REQ-124",
        schema_version="1",
        title="Enterprise profile advisory",
        sources=[RequirementSourceReference(source_type=RequirementSourceType.DOCUMENT, locator="docs/product.md")],
        completeness_findings=[
            RequirementCompletenessFinding(
                profile="enterprise",
                severity=RequirementCompletenessSeverity.WARNING,
                field_path="regulatory_references",
                message="Enterprise profile should include regulatory references.",
            )
        ],
    )

    assert requirement.completeness_findings[0].profile == "enterprise"
    assert requirement.completeness_findings[0].severity == "warning"


def test_requirements_extension_payload_round_trips_records() -> None:
    """ProjectBundle extensions can carry requirement inputs as serializable payloads."""
    requirement = RequirementInput(
        requirement_id="REQ-125",
        schema_version="1",
        title="Extension payload",
        sources=[
            RequirementSourceReference(
                source_type=RequirementSourceType.OPENSPEC_CHANGE, locator="requirements-01-data-model"
            )
        ],
    )

    payload = requirements_input_extension_payload([requirement])
    loaded = load_requirements_input_extension(payload)

    assert payload["schema_version"] == "1"
    assert payload["requirements"][0]["requirement_id"] == "REQ-125"
    assert loaded == [requirement]


def test_requirements_extension_loader_rejects_invalid_payload_at_contract_boundary() -> None:
    """Invalid extension payloads fail before Pydantic validation internals."""
    with pytest.raises(ViolationError):
        load_requirements_input_extension({"schema_version": "1", "requirements": [{"requirement_id": "REQ-126"}]})


def test_requirements_extension_loader_rejects_unknown_payload_schema_version() -> None:
    """Invalid extension schema versions fail at the loader contract boundary."""
    with pytest.raises(ViolationError):
        load_requirements_input_extension({"schema_version": "999", "requirements": []})


def test_requirements_extension_loader_requires_payload_schema_version() -> None:
    """Extension payload validation rejects unversioned payload artifacts."""
    with pytest.raises(ViolationError):
        load_requirements_input_extension({"requirements": []})
