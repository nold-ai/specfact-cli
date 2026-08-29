# Change: Deterministic Pre-Implementation Design Contract Core

## Why

Implementation can start from change artifacts that are individually plausible but collectively stale, incomplete, contradictory, or wider than the approved intent. The core repository needs a stable, runtime-neutral contract for representing what was reviewed, what remained unknown, what was approved, and whether the reviewed inputs have changed.

## What Changes

- **NEW**: Core-only specifications for a normalized pre-implementation design contract, including source identities, role-classified implementation scope, component ownership, approved influence mappings or justified no-impact dispositions for every non-excluded sealed input, assumptions, unknowns, dependencies, interfaces, acceptance criteria, risk dimensions, verification stages, test intent, and rollback intent.
- **NEW**: Seal-bound references to the existing Requirements maturity, verification-case, exact pytest-selector when test-authored, plan-digest, and evidence contracts; planned cases remain sealable before selectors exist and no second selector schema is defined.
- **NEW**: Core-only specifications for deterministic validation results with stable finding identity, severity, ownership, and readiness semantics.
- **NEW**: Core-only specifications for canonical digests and an approval seal that binds one exact contract, validation result, source snapshot, and immutable implementation-lineage origin preserved across successor seals.
- **NEW**: A verifier interface contract that can detect stale, mismatched, incomplete, or unapproved inputs without owning CLI, persistence, rendering, or validator execution.
- **CLARIFY**: A seal proves identity and recorded approval of reviewed material; it does not prove semantic correctness, implementation correctness, or that an LLM understood the change.

## Capabilities

### New Capabilities

- `preflight-assurance-contracts`: Stable data and verification interfaces for deterministic pre-implementation assurance.

### Modified Capabilities

(none)

## Impact

- Planning artifacts only in this phase. No production or test code, CLI command, module package, manifest, signature, generated seal, skill, plugin, adapter, hook, workflow, or dependency file is created.
- Later core implementation is limited to reusable models, canonicalization rules, digest helpers, and verifier interfaces. Executable validators and user workflows remain modules-owned.
- Existing architecture, governance evidence, traceability, and native OpenSpec/Spec Kit import contracts remain upstream inputs and are not redefined here.

## Dependencies

- Parent Feature: [#681](https://github.com/nold-ai/specfact-cli/issues/681), under Epic [#285](https://github.com/nold-ai/specfact-cli/issues/285).
- Upstream contract inputs: `architecture-01-solution-layer`, `governance-01-evidence-output`, `traceability-01-index-and-orphans`, and `openspec-01-intent-trace`.
- Blocks the modules change `preflight-02-assurance-runtime`.

## Explicit Non-Goals

- No CLI, rendering, persistence, policy-pack execution, Python validator implementation, skill content, external harness packaging, publication, checkpoint execution, or implementation-conformance behavior.
- No automatic refinement or approval of an ambiguous change.
- No replacement for OpenSpec, Spec Kit, AGENTS.md, architecture records, GitHub hierarchy, tests, or human review.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #682
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/682>
- **Last Synced Status**: proposed
- **Sanitized**: true
