# Change: Artifact Evidence Index and Orphan Detection

## Why

Validation evidence decays when artifacts are added, renamed, or deleted without
their upstream and downstream references changing with them. Teams need a fast
index that can answer whether a code path, test, contract, backlog item,
OpenSpec change, Spec Kit feature, or ADR still has useful evidence around it.

This change keeps traceability as a validation capability. It is not a ceremony,
dashboard, or planning-authoring feature.

## Ownership Alignment (2026-06-06)

- Repository assignment: `split/rescope`
- Core-owned scope retained here: artifact identity, linkage semantics, orphan
  classifications, and graph index contracts.
- Bundle-owned follow-up required: the runtime query and reporting surface belongs
  to the canonical module command model.
- Target modules-repo follow-up issue: [#170](https://github.com/nold-ai/specfact-cli-modules/issues/170)
- Implementation MUST NOT revive the legacy flat `specfact trace ...` package
  layout without the paired module change.

## What Changes

- **NEW**: Artifact evidence index stored as generated state under `.specfact/`.
- **NEW**: Link model for upstream inputs and downstream implementation evidence:
  Spec Kit, OpenSpec, backlog, ADRs, contracts, specs, code, tests, policy
  results, and code-review findings.
- **NEW**: Orphan and drift categories for artifacts with missing, stale,
  ambiguous, or contradicted evidence.
- **NEW**: Incremental rebuild contract so validation runs can update affected
  entries without reindexing an entire repository when possible.
- **NEW**: JSON export shape consumed by `validation-02-full-chain-engine` and
  `governance-01-evidence-output`.

## Capabilities

### New Capabilities

- `artifact-evidence-index`: Generated index for artifact identity, evidence
  links, orphan detection, and drift classification across existing inputs.

### Modified Capabilities

(none)

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #242
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/242>
- **Paired Modules Runtime Issue**: nold-ai/specfact-cli-modules#170
- **Paired Modules Scope**: traceability runtime queries and orphan detection
- **Last Synced Status**: proposed
- **Sanitized**: false
