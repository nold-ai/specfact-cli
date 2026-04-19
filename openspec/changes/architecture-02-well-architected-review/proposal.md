# Change: Well-Architected and Clean-Architecture Review Layer

## Why

`architecture-01-solution-layer` establishes solution architecture as a modeled layer, but it does not yet score designs against boundary, interface, and well-architected review rules. This change turns architecture from passive documentation into an active review pillar that catches layer violations and missing ADR traceability before implementation drifts.

## What Changes

- **NEW**: `architecture-review` capability covering architecture findings, review contracts, and `specfact architecture diff`.
- **NEW**: Finding categories for boundary violations, interface leaks, layer inversion, coupling hotspots, missing ADR links, and Well-Architected review dimensions.
- **NEW**: CLI surface to diff interface changes and classify them as breaking, non-breaking, or additive.
- **EXTEND**: ADR-to-code traceability rules so the architecture layer can emit review findings, not just references.
- **EXTEND**: Shared review-report integration so architecture findings can live beside code quality, security, and resiliency pillars.

**Backward-compatible envelope:** The existing `ReviewReport` envelope stays stable for legacy parsers: required sections and field names used today remain unchanged. Implementations add an optional top-level `architecture` object (or, if we standardize a single extension map first, an optional `extensions.architecture` object) so older consumers ignore unknown keys while new consumers read the pillar. Serialized contract for review runs: **review runs MUST include an `architecture` section in the shared envelope while preserving other review sections unchanged** (e.g., `code_quality`, `security`, `resiliency` keys and their payloads stay as today). Example shape: `ReviewReport { ..., "architecture"?: { "findings": [...], "summary": {...} } }` — exact inner fields follow `specs/architecture-review/spec.md`; parsers MUST treat missing `architecture` as “no architecture findings” until emitters roll out.

## Capabilities

### New Capabilities

- `architecture-review`: Architecture review findings, interface-diff contract, and ADR traceability enforcement.

### Modified Capabilities

- `solution-architecture`: Extend the solution layer so ADR and interface metadata can feed the architecture review surface.

## Impact

- Depends on `architecture-01-solution-layer`, `review-finding-model`, and `review-report-model`.
- Supplies the contract consumed by the modules-side `architecture-02-module-well-architected` bundle.
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
