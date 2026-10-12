# Change: Preserve finalized proof context for inherited Code Review

## Why

After protected #767, actual #743 run 38303860784 authenticates the root and passes planned
reconciliation, then Code Review correctly rejects the planning report because it is not a complete
finalized execution proof. Native CI reviews inherited Python changes against dev, so that review
must consume the authentic root execution proof rather than the child planning receipt.

## What Changes

- Independently reauthenticate native planning context and download the exact root Requirements artifact.
- Verify artifact repository, run, branch, head, name, expiry, digest and bounded archive/report identity.
- Require verified finalized root evidence; preserve its bytes and the separate child planning receipt.
- Retain full inherited Python review against protected dev in both independent and final consumers.
- Reject stale, forged, ambiguous, malformed or producer/planning context; preserve ordinary review.
- Keep provider pins, review enforcement, scope whitelist, signatures and every required check.

## Capabilities

### New Capabilities

- requirements-planning-review-context: authentic root final proof for inherited review.

### Modified Capabilities

None. No provider semantics, policy thresholds or deferred runtime delivery change.

## Impact

Protected workflow review-context selection and a stdlib-only artifact reader, focused actual workflow
controls, evidence and coherent bugfix metadata. Integration on dev is required before planning
children consume the protected helper. Target PRs #719/#743/#751 remain unmerged.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- Existing issue #760, parent #355, SpecFact CLI/Todo; bug/security/change-proposal; no native dependencies.
- #761 and #767 are merged; this fixes the next independently observed consumer boundary.
- Owner authorized stability/security protections and forbids convenient gate weakening.
- Exact mapping acceptance, verified-head grants and separately authorized protected merge remain required.
