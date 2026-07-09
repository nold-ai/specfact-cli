"""Tests for the generic core artifact evidence index."""

import json

from specfact_cli.models.requirements import (
    RequirementEvidenceLink,
    RequirementEvidenceLinkType,
    RequirementInput,
    RequirementSourceReference,
    RequirementSourceType,
)
from specfact_cli.traceability import (
    ArtifactKind,
    ArtifactLink,
    ArtifactRecord,
    build_artifact_index,
    requirements_to_artifact_records,
)


def _record(identity: str, *, links: list[ArtifactLink] | None = None, fingerprint: str = "v1") -> ArtifactRecord:
    return ArtifactRecord(
        identity=identity, kind=ArtifactKind.CODE, locator=identity, fingerprint=fingerprint, links=links or []
    )


def test_index_is_deterministic_and_classifies_orphans_and_drift() -> None:
    result = build_artifact_index(
        [
            _record("code:b", links=[ArtifactLink(target="code:a")]),
            _record("code:a"),
            _record("test:orphan"),
            _record("code:dangling", links=[ArtifactLink(target="code:missing")]),
        ]
    )

    assert [record.identity for record in result.index.artifacts] == [
        "code:a",
        "code:b",
        "code:dangling",
        "test:orphan",
    ]
    assert [finding.identity for finding in result.orphans] == ["test:orphan"]
    assert [finding.identity for finding in result.drift] == ["code:dangling"]


def test_index_canonicalizes_link_order() -> None:
    links = [ArtifactLink(target="code:z"), ArtifactLink(target="code:a")]

    result = build_artifact_index([_record("code:links", links=list(reversed(links)))])

    assert [link.target for link in result.index.artifacts[0].links] == ["code:a", "code:z"]


def test_index_classifies_duplicate_and_self_links() -> None:
    result = build_artifact_index(
        [
            _record("code:duplicate"),
            _record("code:duplicate", fingerprint="v2"),
            _record("code:self", links=[ArtifactLink(target="code:self")]),
        ]
    )

    assert [finding.identity for finding in result.ambiguities] == ["code:duplicate"]
    assert [finding.identity for finding in result.contradictions] == ["code:self"]


def test_rebuild_reports_changed_and_removed_identities() -> None:
    before = build_artifact_index([_record("code:stable"), _record("code:removed")]).index

    result = build_artifact_index(
        [_record("code:stable", fingerprint="v2"), _record("code:added")], previous_index=before
    )

    assert result.changed_identities == ["code:added", "code:stable"]
    assert result.removed_identities == ["code:removed"]
    assert [artifact["identity"] for artifact in json.loads(result.index.to_json())["artifacts"]] == [
        "code:added",
        "code:stable",
    ]


def test_requirements_map_to_stable_artifacts_and_links() -> None:
    requirement = RequirementInput(
        schema_version="1",
        requirement_id="REQ-1",
        title="Trace me",
        sources=[RequirementSourceReference(source_type=RequirementSourceType.ISSUE, locator="https://example.test/1")],
        evidence_links=[RequirementEvidenceLink(link_type=RequirementEvidenceLinkType.CODE, target="src/app.py")],
    )

    records = requirements_to_artifact_records([requirement])

    assert records[0].identity == "requirement:REQ-1"
    assert records[0].links[0].target == "code:src/app.py"
