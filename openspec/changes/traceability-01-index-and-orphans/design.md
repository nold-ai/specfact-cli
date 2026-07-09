## Context

This change completes core issue #242 after the product focus moved from
planning and architecture authoring toward validation evidence. Core therefore
provides a reusable, deterministic artifact-evidence index; it does not
collect every domain itself or expose a runtime command surface.

## Goals / Non-Goals

**Goals:**

- Define stable, generic records, identities, links, fingerprints, and finding
  classifications that downstream validators can consume.
- Integrate `requirements.inputs` as the first producer without making
  architecture input mandatory.
- Preserve offline-first, deterministic behavior and public contract-first APIs.

**Non-Goals:**

- No core collector/parser for every artifact domain.
- No `.specfact` persistence, flags, grouped commands, rendering, or query UX.
- No policy-pack behavior; profile configuration only determines finding
  severity defaults.

## Decisions

- Model every input as an `ArtifactRecord` with a stable identity, artifact
  kind, location, fingerprint, and typed links. Domain owners may create these
  normalized records without coupling core to their parser or storage format.
- Canonically sort records and findings before returning them. Emit a
  JSON-serializable `ArtifactEvidenceIndex` so downstream governance and
  validation changes share a contract rather than a private representation.
- Classify unlinked artifacts as orphans, unknown link targets as drift,
  duplicate identities as ambiguity, and self-links as contradictions.
- Accept the prior in-memory index for rebuild comparison and report changed
  and removed identities. Persistence belongs to modules #170.
- Map `requirements.inputs` into `ArtifactRecord` values as the first adapter.
  Architecture and all other domains are optional: they participate only when
  an owning change supplies normalized records.
- Keep public APIs contract-first with `@icontract` and runtime type
  enforcement. Preserve the legacy requirements helper as a compatibility
  adapter while routing it through the generic index.

## Risks / Trade-offs

- [Unstable identifiers create noisy rebuilds] -> Mitigation: require stable
  identities and use canonical serialized fingerprints for comparisons.
- [Optional adapters become false orphan sources] -> Mitigation: only classify
  supplied records; absence of architecture records creates no architecture
  finding.
- [Core/runtime ownership blurs again] -> Mitigation: specify modules #170 as
  the owner of persistence and command UX in proposal, spec, docs, and tasks.

## Migration Plan

1. Revalidate existing change artifacts and GitHub issue #242 against current
   ownership; record the product decision to complete generic core scope.
2. Add tests from spec scenarios and capture failing-first evidence.
3. Implement the smallest generic core index and requirements adapter needed
   for passing scenarios.
4. Update contracts and navigation docs, then run quality gates and open a PR
   to `dev` that closes #242 on merge.

## Dependency Resolution

- `requirements-02-module-commands` is the only required integrated input and
  is shipped.
- Architecture records are optional and have no bearing on a requirements-only
  result.
- `governance-01-evidence-output` and `validation-02-full-chain-engine` are
  downstream consumers/producers of this contract, not prerequisites.
- Modules #170 is a paired runtime-delivery follow-up and does not block
  closing core issue #242.
