"""Generic core artifact evidence index contracts and requirements adapter."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Sequence, Set
from enum import StrEnum
from typing import Literal

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, Field

from specfact_cli.models.project import ProjectBundle
from specfact_cli.models.requirements import RequirementInput
from specfact_cli.requirements.context import (
    KNOWN_REQUIREMENT_CONTEXT_PROFILES,
    STRICT_REQUIREMENT_CONTEXT_PROFILES,
    RequirementContextValidationProfile,
    load_requirements_from_bundle,
)


class ArtifactKind(StrEnum):
    """Normalized kinds that adapters may contribute to the evidence index."""

    REQUIREMENT = "requirement"
    ARCHITECTURE = "architecture"
    SPECIFICATION = "specification"
    CODE = "code"
    TEST = "test"
    CONTRACT = "contract"
    OPENSPEC = "openspec"
    SPECKIT = "speckit"
    BACKLOG = "backlog"
    ADR = "adr"
    POLICY = "policy"
    REVIEW = "review"
    VALIDATION = "validation"


@beartype
class ArtifactLink(BaseModel):
    """Directed relationship between stable artifact identities."""

    target: str = Field(..., min_length=1)
    relation: str = Field(default="references", min_length=1)


@beartype
class ArtifactRecord(BaseModel):
    """Adapter-neutral evidence artifact with stable identity and fingerprint."""

    identity: str = Field(..., min_length=1)
    kind: ArtifactKind
    locator: str = Field(..., min_length=1)
    fingerprint: str = Field(..., min_length=1)
    links: list[ArtifactLink] = Field(default_factory=list)


@beartype
class ArtifactEvidenceIndex(BaseModel):
    """Deterministic core index; callers own persistence and rendering."""

    schema_version: Literal["1"] = "1"
    artifacts: list[ArtifactRecord] = Field(default_factory=list)

    @ensure(lambda result: isinstance(result, str), "result must be JSON text")
    def to_json(self) -> str:
        """Return canonical JSON suitable for a modules-owned persistence layer."""
        return json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))


@beartype
class TraceabilityFinding(BaseModel):
    """Bounded index finding."""

    code: str = Field(..., min_length=1)
    identity: str = Field(..., min_length=1)
    severity: Literal["warning", "error"]
    location: str = Field(..., min_length=1)

    @property
    @ensure(lambda result: isinstance(result, str), "result must be text")
    def requirement_id(self) -> str:
        """Compatibility identifier for requirements-first callers."""
        return self.identity.removeprefix("requirement:")


@beartype
class ArtifactIndexBuildResult(BaseModel):
    """Index plus deterministic classifications and incremental rebuild facts."""

    index: ArtifactEvidenceIndex
    orphans: list[TraceabilityFinding] = Field(default_factory=list)
    drift: list[TraceabilityFinding] = Field(default_factory=list)
    ambiguities: list[TraceabilityFinding] = Field(default_factory=list)
    contradictions: list[TraceabilityFinding] = Field(default_factory=list)
    changed_identities: list[str] = Field(default_factory=list)
    removed_identities: list[str] = Field(default_factory=list)


TraceabilityResult = ArtifactIndexBuildResult


def _severity(profile: str) -> Literal["warning", "error"]:
    return "error" if profile in STRICT_REQUIREMENT_CONTEXT_PROFILES else "warning"


def _finding(code: str, identity: str, severity: Literal["warning", "error"]) -> TraceabilityFinding:
    return TraceabilityFinding(code=code, identity=identity, severity=severity, location=f"artifacts[{identity}]")


def _canonical_records(records: Sequence[ArtifactRecord]) -> tuple[list[ArtifactRecord], list[str]]:
    grouped: dict[str, list[ArtifactRecord]] = {}
    for record in records:
        grouped.setdefault(record.identity, []).append(
            record.model_copy(update={"links": sorted(record.links, key=lambda link: (link.target, link.relation))})
        )
    duplicates = sorted(identity for identity, values in grouped.items() if len(values) > 1)
    canonical = [sorted(values, key=_record_signature)[0] for _, values in sorted(grouped.items())]
    return canonical, duplicates


def _record_signature(record: ArtifactRecord) -> str:
    return json.dumps(record.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))


def _incoming_links(records: Sequence[ArtifactRecord], identities: set[str]) -> Counter[str]:
    return Counter(
        link.target
        for record in records
        for link in record.links
        if link.target in identities and link.target != record.identity
    )


def _orphan_findings(
    records: Sequence[ArtifactRecord], incoming: Counter[str], severity: Literal["warning", "error"]
) -> list[TraceabilityFinding]:
    return [
        _finding("unlinked_artifact", record.identity, severity)
        for record in records
        if not record.links and not incoming[record.identity]
    ]


def _classify_record_links(
    record: ArtifactRecord, identities: set[str], severity: Literal["warning", "error"]
) -> list[TraceabilityFinding]:
    findings: list[TraceabilityFinding] = []
    for link in record.links:
        if link.target == record.identity:
            findings.append(_finding("self_referential_link", record.identity, severity))
        elif link.target not in identities:
            findings.append(_finding("dangling_link", record.identity, severity))
    return findings


def _link_findings(
    records: Sequence[ArtifactRecord], identities: set[str], severity: Literal["warning", "error"]
) -> tuple[list[TraceabilityFinding], list[TraceabilityFinding]]:
    findings = [finding for record in records for finding in _classify_record_links(record, identities, severity)]
    return (
        [finding for finding in findings if finding.code == "dangling_link"],
        [finding for finding in findings if finding.code == "self_referential_link"],
    )


def _rebuild_delta(
    records: Sequence[ArtifactRecord], previous_index: ArtifactEvidenceIndex | None
) -> tuple[list[str], list[str]]:
    prior = {record.identity: record for record in (previous_index.artifacts if previous_index else [])}
    current = {record.identity: record for record in records}
    changed = sorted(
        identity
        for identity, record in current.items()
        if identity not in prior or _record_signature(record) != _record_signature(prior[identity])
    )
    return changed, sorted(set(prior) - set(current))


@require(
    lambda records: all(isinstance(record, ArtifactRecord) for record in records),
    "records must contain ArtifactRecord values",
)
@ensure(lambda result: isinstance(result, ArtifactIndexBuildResult), "result must be an ArtifactIndexBuildResult")
@beartype
def build_artifact_index(
    records: Sequence[ArtifactRecord],
    *,
    previous_index: ArtifactEvidenceIndex | None = None,
    profile: RequirementContextValidationProfile = "startup",
) -> ArtifactIndexBuildResult:
    """Build a generic deterministic index without collecting or persisting artifacts."""
    severity = _severity(profile)
    canonical, duplicates = _canonical_records(records)
    identities = {record.identity for record in canonical}
    incoming = _incoming_links(canonical, identities)
    drift, contradictions = _link_findings(canonical, identities, severity)
    changed, removed = _rebuild_delta(canonical, previous_index)
    return ArtifactIndexBuildResult(
        index=ArtifactEvidenceIndex(artifacts=canonical),
        orphans=_orphan_findings(canonical, incoming, severity),
        drift=drift,
        ambiguities=[_finding("duplicate_identity", identity, severity) for identity in duplicates],
        contradictions=contradictions,
        changed_identities=changed,
        removed_identities=removed,
    )


@require(
    lambda requirements: all(isinstance(requirement, RequirementInput) for requirement in requirements),
    "requirements must contain RequirementInput values",
)
@beartype
def requirements_to_artifact_records(requirements: Sequence[RequirementInput]) -> list[ArtifactRecord]:
    """Map normalized requirements into generic core artifacts without parsing sources."""
    return [
        ArtifactRecord(
            identity=f"requirement:{requirement.requirement_id}",
            kind=ArtifactKind.REQUIREMENT,
            locator=requirement.requirement_id,
            fingerprint=json.dumps(requirement.model_dump(mode="json"), sort_keys=True, separators=(",", ":")),
            links=[
                ArtifactLink(target=f"{link.link_type}:{link.target}", relation=link.relation)
                for link in requirement.evidence_links
            ],
        )
        for requirement in requirements
    ]


def _known_target_records(requirements: Sequence[RequirementInput], known_targets: Set[str]) -> list[ArtifactRecord]:
    kinds_by_target: dict[str, set[ArtifactKind]] = {}
    link_kind_map = {
        "architecture": ArtifactKind.ARCHITECTURE,
        "spec": ArtifactKind.SPECIFICATION,
        "code": ArtifactKind.CODE,
        "test": ArtifactKind.TEST,
        "validation": ArtifactKind.VALIDATION,
        "requirement": ArtifactKind.REQUIREMENT,
    }
    for requirement in requirements:
        for link in requirement.evidence_links:
            if link.target in known_targets:
                kinds_by_target.setdefault(link.target, set()).add(link_kind_map[str(link.link_type)])
    return [
        ArtifactRecord(
            identity=f"{kind_prefix}:{target}",
            kind=kind,
            locator=target,
            fingerprint=target,
        )
        for target in sorted(known_targets)
        for kind in sorted(kinds_by_target.get(target, {ArtifactKind.CODE}), key=lambda item: item.value)
        for kind_prefix in [next(prefix for prefix, value in link_kind_map.items() if value is kind)]
    ]


@require(lambda bundle: isinstance(bundle, ProjectBundle), "bundle must be a ProjectBundle")
@require(lambda profile: isinstance(profile, str) and bool(profile.strip()), "profile must not be empty")
@require(
    lambda profile: profile in KNOWN_REQUIREMENT_CONTEXT_PROFILES, "profile must be a supported validation profile"
)
@ensure(lambda result: isinstance(result, TraceabilityResult), "result must be a TraceabilityResult")
@beartype
def analyze_requirement_traceability(
    bundle: ProjectBundle,
    *,
    profile: RequirementContextValidationProfile,
    known_targets: Set[str] | None = None,
) -> TraceabilityResult:
    """Compatibility helper that supplies requirements and optional known targets to the generic index."""
    requirements = load_requirements_from_bundle(bundle)
    records = requirements_to_artifact_records(requirements)
    if known_targets is not None:
        records.extend(_known_target_records(requirements, known_targets))
    return build_artifact_index(records, profile=profile)
