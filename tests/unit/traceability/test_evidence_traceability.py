"""Contract tests for core evidence and traceability helpers."""

from typing import Any, cast

import pytest
from icontract.errors import ViolationError

from specfact_cli.evidence import EvidenceEnvelope, EvidenceResultSummary
from specfact_cli.models.plan import Product
from specfact_cli.models.project import BundleManifest, BundleVersions, ProjectBundle
from specfact_cli.models.requirements import (
    RequirementEvidenceLink,
    RequirementEvidenceLinkType,
    RequirementInput,
    RequirementSourceReference,
    RequirementSourceType,
)
from specfact_cli.requirements.context import attach_requirements_to_bundle
from specfact_cli.traceability import analyze_requirement_traceability


def _requirement(*, links: list[RequirementEvidenceLink]) -> RequirementInput:
    return RequirementInput(
        schema_version="1",
        requirement_id="REQ-1",
        title="Trace me",
        sources=[RequirementSourceReference(source_type=RequirementSourceType.ISSUE, locator="https://example.test/1")],
        evidence_links=links,
    )


def _bundle() -> ProjectBundle:
    return ProjectBundle(
        manifest=BundleManifest(
            versions=BundleVersions(schema="1.0", project="0.1.0"), schema_metadata=None, project_metadata=None
        ),
        bundle_name="test",
        product=Product(themes=[], releases=[]),
    )


def test_requirements_only_trace_does_not_require_architecture() -> None:
    bundle = attach_requirements_to_bundle(
        _bundle(),
        [
            _requirement(
                links=[RequirementEvidenceLink(link_type=RequirementEvidenceLinkType.CODE, target="src/app.py")]
            )
        ],
    )

    result = analyze_requirement_traceability(bundle, profile="startup", known_targets={"src/app.py"})

    assert result.orphans == []
    assert result.drift == []


def test_known_targets_preserve_requirement_link_kind() -> None:
    bundle = attach_requirements_to_bundle(
        _bundle(),
        [
            _requirement(
                links=[RequirementEvidenceLink(link_type=RequirementEvidenceLinkType.TEST, target="tests/test_app.py")]
            )
        ],
    )

    result = analyze_requirement_traceability(bundle, profile="startup", known_targets={"tests/test_app.py"})

    assert result.drift == []
    assert result.index.artifacts[-1].identity == "test:tests/test_app.py"


def test_traceability_reports_missing_and_stale_links_with_profile_severity() -> None:
    first = _requirement(links=[])
    second = first.model_copy(
        update={
            "requirement_id": "REQ-2",
            "evidence_links": [
                RequirementEvidenceLink(link_type=RequirementEvidenceLinkType.TEST, target="tests/missing.py")
            ],
        }
    )
    bundle = attach_requirements_to_bundle(_bundle(), [first, second])

    result = analyze_requirement_traceability(bundle, profile="enterprise", known_targets=set())

    assert [finding.code for finding in result.orphans] == ["unlinked_artifact"]
    assert result.orphans[0].severity == "error"
    assert [finding.code for finding in result.drift] == ["dangling_link"]


def test_traceability_rejects_unknown_profile() -> None:
    with pytest.raises(ViolationError):
        analyze_requirement_traceability(_bundle(), profile=cast(Any, "enterprize"))


def test_evidence_envelope_derives_ci_verdict_without_runtime_flags() -> None:
    envelope = EvidenceEnvelope(
        profile="enterprise",
        validation_results={"orphans": EvidenceResultSummary(pass_count=0, fail_count=1, advisory_count=0)},
    )

    assert envelope.overall_verdict == "FAIL"
    assert envelope.ci_exit_code == 1
    assert envelope.model_copy(update={"overall_verdict": "PASS"}).overall_verdict == "FAIL"
    with pytest.raises(AttributeError):
        envelope.overall_verdict = "PASS"  # type: ignore[misc]
    assert envelope.model_dump()["validation_results"]["orphans"] == {"pass": 0, "fail": 1, "advisory": 0}
