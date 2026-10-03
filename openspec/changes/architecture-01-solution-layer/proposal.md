# Change: Architecture Boundary Validation Inputs

## Owner-approved agentic SDLC amendment — 2026-10-04

First import approved boundaries, ownership and ADR references as optional context with exact source identity. Structural readiness is not design-quality approval. Replace architecture derivation/authoring scenarios in this change with bounded import and evidence association. Missing traceability is missing association/evidence, not proof of absent behavior. Broader analyzer review remains after architecture input delivery and one complete real usage cycle. At that stage consume maintained Import Linter Python dependency-rule results, preserving rule/configuration/version/snapshot identity, declared boundary association and original artifacts; do not build a second import-graph engine. Plant a forbidden dependency in fixtures and require its reported violation; unavailable/incomplete extraction is UNKNOWN.

This planning amendment supersedes conflicting scope and prerequisite wording below. It changes no runtime behavior and completes no implementation task. See [roadmap](../../AGENTIC_SDLC_ROADMAP.md).

## Why

Architecture context is valuable to SpecFact when it helps validate code reality:
boundary violations, missing ADR evidence, stale component ownership, and
contracts that no longer match the intended design. SpecFact should not compete
with planning or architecture-generation tools.

This change narrows the old solution-layer proposal to architecture-boundary
records and drift evidence used by validation.

## Ownership Alignment (2026-06-06)

- Repository assignment: `split/rescope`
- Core-owned scope retained here: architecture input schema, namespace extension
  ownership, and validation hooks.
- Bundle-owned follow-up required: runtime delivery belongs to the canonical
  grouped module command model.
- Target modules-repo follow-up issue: [#164](https://github.com/nold-ai/specfact-cli-modules/issues/164)
- Implementation MUST NOT ship architecture generation as the product path.

## What Changes

- **NEW**: Architecture-boundary input models for components, ownership,
  interfaces, data-flow hints, ADR references, and validation constraints.
- **NEW**: Storage/import convention for architecture records that originate from
  existing ADRs, diagrams, docs, Spec Kit plans, or OpenSpec design notes.
- **NEW**: Coverage checks that classify missing ADR links, interface leaks,
  component ownership gaps, and mismatched contract boundaries.
- **EXTEND**: `ProjectBundle` receives an optional architecture-boundary
  namespace through the schema extension system.
- **REMOVED FROM CRITICAL PATH**: AI-assisted architecture derivation and
  template-based architecture authoring.

## Capabilities

### New Capabilities

- `architecture-boundary-validation-inputs`: Architecture records and validation
  hooks for boundary, ADR, interface, and component drift evidence.

### Modified Capabilities

- `data-models`: ProjectBundle extended with an optional architecture-boundary
  namespace.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #240
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/240>
- **Paired Modules Runtime Issue**: nold-ai/specfact-cli-modules#164
- **Paired Modules Scope**: architecture runtime delivery
- **Last Synced Status**: proposed
- **Sanitized**: false

## Planning validation

See [AGENTIC_SDLC_VALIDATION.md](../../AGENTIC_SDLC_VALIDATION.md) for actual proposal checks and the explicit Python-only analyzer applicability exception. Runtime review and release tasks remain pending.
