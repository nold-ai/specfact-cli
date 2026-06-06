# Change: OpenSpec and Spec Kit Evidence Adapter

## Why

OpenSpec and Spec Kit already own large parts of upstream specification and
planning. SpecFact should consume their artifacts as validation inputs rather
than define a mandatory upstream intent schema that those projects must adopt.

This change reframes intent trace as an optional adapter convention: when
structured context exists, SpecFact imports it; when it does not, SpecFact still
validates code, contracts, tests, and artifact drift with source-attributed
evidence.

## Ownership Alignment (2026-06-06)

- Repository assignment: `split/rescope`
- Core-owned scope retained here: optional adapter schema, source attribution,
  task/reference parsing, and validation behavior when context is present.
- Bundle-owned follow-up required: runtime import behavior belongs to the
  canonical project-bundle sync/import owner.
- Target modules-repo follow-up issue: [#168](https://github.com/nold-ai/specfact-cli-modules/issues/168)
- Implementation MUST NOT require OpenSpec or Spec Kit to change their native
  authoring model.

## What Changes

- **NEW**: Optional adapter metadata convention for OpenSpec proposals and Spec
  Kit feature folders.
- **NEW**: Source-attributed import of outcomes, requirement references, tasks,
  spec deltas, acceptance checks, and evidence links when present.
- **NEW**: Strict validation of adapter metadata only when the optional metadata
  is present.
- **NEW**: Evidence pointers on archived changes MAY reference validation JSON
  produced during implementation.
- **EXTEND**: Bridge/import flows can map upstream artifacts into the
  requirements input model and evidence graph without creating duplicate
  planning artifacts.

## Capabilities

### New Capabilities

- `openspec-speckit-evidence-adapter`: Optional source-attributed adapter for
  OpenSpec and Spec Kit artifacts consumed by SpecFact validation.

### Modified Capabilities

- `openspec-bridge-adapter`: Extended to parse optional metadata and evidence
  links without requiring them.

## Impact

- OpenSpec and Spec Kit are documented as upstream inputs.
- Existing OpenSpec proposals remain valid when no adapter metadata exists.
- Depends on `requirements-01-data-model` and `requirements-02-module-commands`
  only for normalized evidence import.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #350
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/350>
- **Paired Modules Runtime Issue**: nold-ai/specfact-cli-modules#168
- **Paired Modules Scope**: OpenSpec and Spec Kit evidence import runtime
- **Last Synced Status**: proposed
- **Sanitized**: false
