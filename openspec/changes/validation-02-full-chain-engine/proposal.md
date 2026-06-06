# Change: Validation Evidence Graph Engine

## Why

SpecFact should not own the full upstream planning lifecycle. Spec Kit,
OpenSpec, backlog tools, ADRs, contracts, tests, and source code already produce
the artifacts teams plan and build from. The sharper product gap is that those
artifacts drift, AI-assisted code accumulates bloat, and CI evidence is often too
weak to prove what changed.

This change turns the old full-chain idea into a validation evidence graph: a
local, deterministic engine that consumes existing artifacts, detects missing or
weak links, classifies severity, and writes evidence that humans, CI, and AI IDEs
can trust.

## Ownership Alignment (2026-06-06)

- Repository assignment: `split/rescope`
- Core-owned scope retained here: evidence graph contracts, node/link semantics,
  severity aggregation, and governance/evidence integration boundaries.
- Bundle-owned runtime scope remains in `nold-ai/specfact-cli-modules` and MUST
  implement the engine through the canonical grouped command model.
- Target modules-repo follow-up issue: [#171](https://github.com/nold-ai/specfact-cli-modules/issues/171)
- Implementation MUST NOT proceed as a requirements-to-architecture-to-code
  lifecycle engine.

## What Changes

- **NEW**: Validation evidence graph model that normalizes upstream artifacts
  into nodes such as requirements input, architecture boundary, OpenSpec/Spec Kit
  change, contract, code unit, test, policy result, and code-review finding.
- **NEW**: Link and gap classification for missing evidence, stale references,
  orphaned implementation artifacts, uncovered contracts, weak tests, and
  AI-bloat remediation status.
- **NEW**: Severity aggregation tuned by profiles and policy modes without
  changing the evidence schema.
- **NEW**: Machine-readable evidence output that can be consumed by
  `governance-01-evidence-output`, CI gates, and AI IDE remediation loops.
- **EXTEND**: Existing validation flows SHALL expose a compatibility alias such as
  `--full-chain`, but the implementation language and evidence schema SHALL use
  validation graph terminology.
- **EXTEND**: Optional code-review side channel attaches clean-code and
  `ai_bloat` summaries to the graph without redefining upstream planning layers.

## Capabilities

### New Capabilities

- `validation-evidence-graph`: Deterministic validation graph over existing
  planning, spec, contract, code, test, policy, and review artifacts with
  severity aggregation and JSON evidence output.

### Modified Capabilities

- `sidecar-validation`: Extended to publish graph-compatible evidence for
  downstream governance and AI IDE remediation.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #241
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/241>
- **Paired Modules Runtime Issue**: nold-ai/specfact-cli-modules#171
- **Paired Modules Scope**: validation evidence graph runtime engine
- **Last Synced Status**: proposed
- **Sanitized**: false
