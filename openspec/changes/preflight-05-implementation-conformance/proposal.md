# Change: Seal-Bound Implementation Assurance Core

## Why

Pre-implementation assurance freezes what was reviewed and approved, but it deliberately does not prove that later code matches that contract. Core needs one reusable comparison boundary for cheap local implementation checkpoints and final immutable-range conformance without allowing local evidence to masquerade as pull-request authority.

## What Changes

- **NEW**: Core-only specifications for `worktree`, `index`, and immutable `range` implementation snapshots with complete path manifests, exact policy-authorized current delivery-target identity, and producer/policy/toolchain/evidence identities.
- **NEW**: Core-only obligation mapping that requires the canonical latest seal-lineage tip plus `DevelopmentCheckpointResult` and `ImplementationConformanceResult` contracts.
- **NEW**: Closed finding classes for missing, unexpected, modified, violated, stale, and unverifiable implementation-to-contract evidence.
- **NEW**: A side-effect-free assurance verifier interface that receives the upstream contract, validation result, selected seal, canonical lineage-tip identity, policy, current source and delivery-target identities, plus normalized implementation evidence; stale or mismatched upstream inputs fail closed before obligation comparison.
- **CLARIFY**: Local worktree/index checkpoints have only local authority and can never be promoted or described as protected PR-range evidence.
- **CLARIFY**: Passing tests are evidence inputs; the contract does not infer semantic correctness or complete requirement coverage from exit code alone.

## Capabilities

### New Capabilities

- `preflight-implementation-conformance-contracts`: Stable implementation snapshot, checkpoint/conformance result, finding, obligation-map, and verifier interfaces.

### Modified Capabilities

(none)

## Impact

- Planning artifacts only in this phase. No production or test code, runtime command, generated snapshot/result, module, skill, adapter, manifest, signature, version, or dependency is created.
- This change starts after the stable preflight module handoff and before generic skill installation, generated instructions, or harness adapters.
- Modules owns checkpoint/conformance execution, evidence extraction, rendering, bounded agent handoff, persistence, and release in the paired change.

## Dependencies

- Parent Feature: core [#681](https://github.com/nold-ai/specfact-cli/issues/681).
- Blocked by the stable modules `preflight-03-dogfood-hardening-and-release` handoff.
- Blocks the paired modules `preflight-05-implementation-conformance` runtime story [#434](https://github.com/nold-ai/specfact-cli-modules/issues/434).

## Explicit Non-Goals

- No pre-implementation validator or approval behavior and no mutation of the approved seal.
- No code execution, test runner, coverage engine, architecture analyzer, or GitHub merge gate in core.
- No automatic acceptance of implementation drift or automatic rewrite of the sealed contract.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #684
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/684>
- **Cross-Repository Counterpart**: <https://github.com/nold-ai/specfact-cli-modules/issues/434>
- **Last Synced Status**: proposed
- **Sanitized**: true
