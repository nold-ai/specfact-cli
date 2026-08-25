# Change: Sealed-Contract Implementation Conformance Core

## Why

Pre-implementation assurance freezes what was reviewed and approved, but it deliberately does not prove that later code matches that contract. A separate, later core contract is needed to compare implementation evidence to the sealed design without widening the preflight MVP or confusing approval identity with delivery proof.

## What Changes

- **NEW**: Core-only specifications for an implementation snapshot bound to repository revision, changed paths, public interfaces, test evidence, and traceability records.
- **NEW**: Core-only conformance result and finding contracts for missing, unexpected, modified, stale, and unverifiable implementation-to-contract mappings.
- **NEW**: A side-effect-free conformance verifier interface that consumes a valid preflight seal plus normalized implementation evidence.
- **CLARIFY**: Conformance is a postimplementation comparison and cannot satisfy or replace the pre-implementation readiness gate.
- **CLARIFY**: Passing tests are evidence inputs; the contract does not infer semantic correctness or complete requirement coverage from exit code alone.

## Capabilities

### New Capabilities

- `preflight-implementation-conformance-contracts`: Stable implementation snapshot, conformance result, drift finding, and verifier interfaces.

### Modified Capabilities

(none)

## Impact

- Planning artifacts only in this phase. No production or test code, runtime command, generated snapshot/result, module, skill, adapter, manifest, signature, version, or dependency is created.
- This change is explicitly outside the preflight MVP and starts only after the stable preflight module handoff.
- Modules owns executable comparison, evidence extraction, rendering, and persistence in the paired change.

## Dependencies

- Parent Feature: core [#681](https://github.com/nold-ai/specfact-cli/issues/681).
- Blocked by the stable modules `preflight-03-dogfood-hardening-and-release` handoff.
- Blocks the paired modules `preflight-05-implementation-conformance` runtime story [#434](https://github.com/nold-ai/specfact-cli-modules/issues/434).

## Explicit Non-Goals

- No pre-implementation validator or approval behavior.
- No code execution, test runner, coverage engine, architecture analyzer, or GitHub merge gate in core.
- No automatic acceptance of implementation drift or automatic rewrite of the sealed contract.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #684
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/684>
- **Cross-Repository Counterpart**: <https://github.com/nold-ai/specfact-cli-modules/issues/434>
- **Last Synced Status**: proposed
- **Sanitized**: true
