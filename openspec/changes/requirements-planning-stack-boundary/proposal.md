# Change: Validate planning layers above a verified native stack root

## Why

Stack #759 contains an implemented security root followed by unrelated planning proposals. Selecting the
entire stack at one implementation maturity applies a single accepted mapping to all sources and blocks
legitimate deferred planning. Accepting or claiming execution for those proposals would be incorrect.

## What Changes

- Authenticate the existing native ancestry and an exact-root successful Requirements execution and
  member-authority run before selecting an additional planning-only boundary.
- Allow that boundary only when every root-to-child path is a regular non-executable OpenSpec planning
  file and no root-covered OpenSpec source changes. Runtime, tests, workflow, delivery, canonical specs,
  executables, symlinks and changes to inherited security sources retain the full existing proof path.
- Preserve protected dev/main as the trust boundary for validator materialization. Select the root head
  only as the planning diff boundary, independently and consistently in producer, execution and verdict.
- Keep the inherited verified implementation and child planned maturity distinct; do not relabel RED,
  alter provider semantics, infer acceptance, skip checks or change fixture pins.

## Capabilities

### New Capabilities

- `requirements-planning-stack-evidence`: authenticated closed-scope planning above verified runtime.

### Modified Capabilities

None. Existing full-plan RED reconciliation remains mandatory for implementation layers.

## Impact

Affected code: protected stack context helper, one stdlib planning-boundary helper and Requirements
workflow selection. Existing exact-head authority, frozen delivery, independent checks and review remain.
Requires a reviewed prerequisite merge before candidates can use protected helper bytes, then restacking
and fresh proof. Existing upstream modules #481/#483 contracts and deferred roadmap implementation are
unaffected. One bugfix version bump will be synchronized at final implementation publication.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- GitHub issue: #760, <https://github.com/nold-ai/specfact-cli/issues/760>.
- Parent feature: #355; project: SpecFact CLI/Todo; labels: bug, security, change-proposal.
- Owner authorized protective fixes for stack #759, preserving required gates and leaving its PRs unmerged.
- Native blocked-by/blocking lists are empty. Prerequisite merge and fresh exact-head grants require owner
  authorization after a concrete validated result is ready for review.
