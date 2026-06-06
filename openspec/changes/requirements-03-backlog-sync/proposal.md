# Change: Backlog Requirement Drift Evidence

## Why

Backlog items and local validation inputs often drift apart. The useful product
value for SpecFact is to detect and explain that drift before code merges, not
to become the bidirectional source-of-truth sync layer for product management.

## Ownership Alignment (2026-06-06)

- Repository assignment: `split/rescope`
- Core-owned scope retained here: drift evidence contracts, adapter semantics,
  conflict classification, and duplicate-creation safeguards.
- Bundle-owned follow-up required: runtime import/drift commands belong to the
  canonical project/backlog module surfaces.
- Target modules-repo follow-up issue: [#166](https://github.com/nold-ai/specfact-cli-modules/issues/166)
- Implementation MUST NOT depend on backlog write-back for validation value.

## What Changes

- **NEW**: Read-first backlog import and drift detection contract.
- **NEW**: Evidence categories for missing acceptance criteria, stale local
  records, changed issue status, missing source links, and ambiguous mappings.
- **NEW**: Preview-only write-back MAY exist as a later adapter feature, but it
  remains outside the validation critical path and requires explicit write
  confirmation.
- **EXTEND**: Backlog adapters provide source-attributed requirement fields for
  validation.
- **EXTEND**: Spec Kit backlog extension awareness prevents duplicate issue
  creation when imported upstream artifacts already contain tracker mappings.

## Capabilities

### New Capabilities

- `backlog-requirement-drift-evidence`: Read-first detection of drift between
  backlog items and normalized validation inputs.

### Modified Capabilities

- `backlog-adapter`: Extended with source-attributed requirement field import and
  drift classification hooks.
- `requirements-validation-commands`: Extended with backlog drift evidence.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #244
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/244>
- **Paired Modules Runtime Issue**: nold-ai/specfact-cli-modules#166
- **Paired Modules Scope**: requirements-backlog drift runtime
- **Last Synced Status**: proposed
- **Sanitized**: false
