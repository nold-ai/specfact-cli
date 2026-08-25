# Change: Preflight Dogfood Evidence and Readiness Decision

## Why

The preflight loop should not be stabilized or distributed based only on its own specification. It must first be used against the kind of dense, cross-repository change that exposed scope, dependency, ownership, and evidence drift. Core C14 adoption [#680](https://github.com/nold-ai/specfact-cli/issues/680) is the first bounded dogfood target and provides a concrete readiness gate before module hardening and publication.

## What Changes

- **NEW**: A core-owned dogfood evidence protocol for running the exact modules preflight loop against the current C14 core adoption change before implementation or further scope changes.
- **NEW**: Before/after records for input identities, findings, user-approved refinements, reruns, approval state, seal verification, elapsed operator steps, and false-positive/false-negative observations.
- **NEW**: Readiness criteria that distinguish contract defects, runtime defects, source-artifact defects, and documentation/instruction defects.
- **NEW**: A decision record that either authorizes evidence-backed modules hardening or blocks it with reproducible findings.
- **CLARIFY**: Dogfood may propose refinements to C14 artifacts, but only the C14 owner may authorize and apply them in its dedicated issue-linked session.

## Capabilities

### New Capabilities

- `preflight-dogfood-readiness`: Reproducible evidence and a bounded readiness decision for the preflight loop.

### Modified Capabilities

(none)

## Impact

- Planning artifacts only in this phase. No C14 worktree, production code, tests, generated preflight artifact, module package, skill, adapter, manifest, signature, version, or release is changed.
- Future execution is core-owned evidence work. Runtime fixes remain in the paired modules change and core contract fixes require an explicitly scoped core follow-up.
- This paired change ID has separate core and modules issues and OpenSpec artifacts because evidence ownership and release ownership differ.

## Dependencies

- Parent Feature: core [#681](https://github.com/nold-ai/specfact-cli/issues/681).
- Blocked by core C14 adoption [#680](https://github.com/nold-ai/specfact-cli/issues/680), which is blocked by modules `preflight-02-assurance-runtime` in the new ordering.
- Blocks the paired modules `preflight-03-dogfood-hardening-and-release` story [#432](https://github.com/nold-ai/specfact-cli-modules/issues/432).

## Explicit Non-Goals

- No edits to the existing C14 or C15 worktrees during planning setup.
- No automatic correction of C14, no expansion of C14 implementation scope, and no claim that one dogfood case proves universal correctness.
- No module signing, publication, adapter packaging, or implementation-conformance behavior.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #683
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/683>
- **Cross-Repository Counterpart**: <https://github.com/nold-ai/specfact-cli-modules/issues/432>
- **Last Synced Status**: proposed
- **Sanitized**: true
