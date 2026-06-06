# Change: Requirements Import and Validation Commands

## Why

SpecFact needs user-facing commands that can import, normalize, validate, and
inspect upstream requirement context for evidence. It should not position itself
as the authoring stack for requirements, since teams may already use Spec Kit,
OpenSpec, Jira, GitHub Issues, Azure DevOps, Linear, documents, or another
planning source.

## Ownership Alignment (2026-06-06)

- Repository assignment: `split/rescope`
- Core-owned scope retained here: shared requirements input contracts, schemas,
  adapter semantics, and validation result boundaries.
- Bundle-owned follow-up required: runtime commands belong to the canonical
  grouped module command model.
- Target modules-repo follow-up issue: [#165](https://github.com/nold-ai/specfact-cli-modules/issues/165)
- Implementation MUST NOT ship requirement authoring as the critical path.

## What Changes

- **NEW**: Import and normalization contract for upstream requirement-like
  sources, including backlog items, OpenSpec proposals, Spec Kit feature
  folders, and local markdown/YAML records.
- **NEW**: Validation command behavior that checks completeness, source
  freshness, and evidence usefulness by profile.
- **NEW**: Coverage inspection over normalized inputs, architecture boundaries,
  contracts, code, tests, and review findings.
- **NEW**: Adapter hooks that return bounded, source-attributed records rather
  than free-form planning prose.
- **REMOVED FROM CRITICAL PATH**: Interactive authoring templates and broad
  requirement lifecycle management.

## Capabilities

### New Capabilities

- `requirements-validation-commands`: Commands for importing, normalizing,
  validating, and inspecting upstream requirement context as validation evidence.

### Modified Capabilities

- `module-io-contract`: Requirements implementations expose import,
  normalization, and validation hooks for evidence, not full lifecycle sync.
- `backlog-adapter`: Backlog adapters can provide source-attributed requirement
  snippets for validation.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #239
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/239>
- **Paired Modules Runtime Issue**: nold-ai/specfact-cli-modules#165
- **Paired Modules Scope**: requirements runtime commands
- **Last Synced Status**: proposed
- **Sanitized**: false
