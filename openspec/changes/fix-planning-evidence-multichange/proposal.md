# Change: Honor planning maturity across Requirements workflow stages

## Why

The producer supports planning-only evidence, but later verification rejects multiple active changes before reaching the planned branch. This blocks coordinated specification maintenance such as PR #741.

## What Changes

- Use implementation review-evidence selection only above planned maturity in the producer, fresh consumer, and final verifier.
- Continue validating all selected planning sources and comparing independently regenerated plans.
- Preserve implementation scope restrictions, execution/provenance checks, trusted authority, and promotion verification.

## Capabilities

### New Capabilities

- `requirements-planning-workflow`: consistent planning-only review selection in all existing workflow stages.

## Impact

Only the Requirements workflow and its regression tests change. This is a prerequisite bug fix for planning integration, not R09 activation or a new approval mechanism. No CLI/API, module payload, or dependency changes. Contributor-facing behavior is documented by the scoped specification; README, published guides, and navigation remain accurate. Rollback is a revert of the workflow change, restoring the current planning restriction.

## Source Tracking

- **Repository**: nold-ai/specfact-cli
- **GitHub Issue**: #745
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/745>
- **Last Synced Status**: open
- **Parent Feature**: #366
- **Dependencies**: none; unblocks integration of #740 / PR #741.
