# Change: Architecture Boundary Review Layer

## Owner-approved agentic SDLC amendment — 2026-10-04

Keep the architecture-01 delivery plus one complete real usage cycle prerequisite. The first Python analyzer slice consumes Import Linter outputs for declared dependency rules instead of building an import-graph engine. Associate original rule/configuration/tool/source-snapshot identities and findings with approved boundary/component/ADR records. A planted forbidden dependency must be detected; unavailable or incomplete extraction stays UNKNOWN. Broader runtime tracing, predictive graph analysis and polyglot analyzers require demonstrated need. Determine core_compatibility from actually delivered contracts and installed-pair tests; a reserved >=1.0.0 range is not evidence that 1.0-only APIs are necessary.

This planning amendment supersedes conflicting scope and prerequisite wording below. It changes no runtime behavior and completes no implementation task. See [roadmap](../../AGENTIC_SDLC_ROADMAP.md).

## Blocked Status

BLOCKED ON: `architecture-01-solution-layer` shipped plus one complete usage
cycle with real validation evidence.

## Why

Architecture review is useful when it strengthens validation evidence: boundary
violations, interface leaks, layer inversions, missing ADR links, and coupling
hotspots that explain why a code change is risky. This change stays downstream
of the architecture-boundary input model and does not generate or prescribe
architecture.

## What Changes

- **NEW**: `architecture-review` capability covering boundary findings, review
  contracts, and interface-diff evidence.
- **NEW**: Finding categories for boundary violations, interface leaks, layer
  inversion, coupling hotspots, missing ADR links, and selected Well-Architected
  review dimensions.
- **NEW**: CLI/report surface to classify interface changes as breaking,
  non-breaking, additive, or evidence-missing.
- **EXTEND**: ADR-to-code traceability rules so architecture context can emit
  review findings.
- **EXTEND**: Shared review-report integration so architecture findings can live
  beside code quality, security, resiliency, and validation graph evidence.

**Backward-compatible envelope:** The existing `ReviewReport` envelope stays
stable for legacy parsers. Implementations add an optional top-level
`architecture` object, or an optional `extensions.architecture` object if a
single extension map lands first.

## Capabilities

### New Capabilities

- `architecture-review`: Architecture-boundary review findings, interface-diff
  contract, and ADR traceability enforcement.

### Modified Capabilities

- `architecture-boundary-validation-inputs`: Extended so ADR and interface
  metadata can feed the architecture review surface.

## Impact

- Depends on `architecture-01-solution-layer`, `review-finding-model`, and
  `review-report-model`.
- Supplies the contract consumed by the modules-side
  `architecture-02-module-well-architected` bundle.
- Affects docs and future governance evidence flows; no existing API is removed.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #524
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/524>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open
- **Parent Feature**: #514
- **Parent Feature URL**: <https://github.com/nold-ai/specfact-cli/issues/514>
- **Sanitized**: false

## Planning validation

See [AGENTIC_SDLC_VALIDATION.md](../../AGENTIC_SDLC_VALIDATION.md) for actual proposal checks and the explicit Python-only analyzer applicability exception. Runtime review and release tasks remain pending.
