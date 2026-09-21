# Change: Deliver Current-Run Requirements Evidence in Local and CI Gates

## Scope rescope — 2026-09-20

Unimplemented corrected R07 delivery ownership transfers to <https://github.com/nold-ai/specfact-cli/issues/740> and <https://github.com/nold-ai/specfact-cli-modules/issues/481>. Keep this issue open solely to reconcile the replacement after delivery; do not implement a competing R07 pipeline or wait for abandoned R08. Replace its old native blocker on closed modules #368 with <https://github.com/nold-ai/specfact-cli/issues/740>. Existing shipped behavior remains historical context.

This owner-requested scope amendment takes precedence over conflicting default-workflow or dependency wording below. It changes planning only; runtime policy is unchanged. [Replacement policy](../requirements-09-minimal-evidence/proposal.md).

## Why

Issue #662 asks SpecFact to execute exact tests linked to changed requirement scenarios and to report whether those tests were collected and passed in the current delivery run. The existing R07 implementation mixed that bounded observation with a stronger historical claim: proving that the tests failed earlier and remained unchanged through arbitrary Python and pytest dependency behavior.

That stronger claim caused the gate to grow into a static approximation of pytest execution. It also made a current-run Requirements result depend on historical evidence that issue #662 did not require. The two claims need independent contracts and independent statuses.

## Current scope

R07 is reconciliation-only. #740 and paired modules #481 own the corrected
current-run implementation, signed handoff and rollout. Do not implement the
former R07 correction or wait for abandoned R08.

After R09 delivery, verify that #662's useful current-run obligations are
covered and retire the superseded unimplemented deltas without applying them
to canonical specs. Preserve shipped behavior and historical evidence; do not
mark abandoned implementation tasks complete or archive them as implemented.

## Historical capability context

The former correction concerned `requirements-runtime-proof-delivery` and
`requirements-evidence-delivery-gate`. Their historical design/spec files are
comparison context only; R09 owns any reconciled canonical-spec changes.

## Impact

Planning and replacement reconciliation only. No independent R07 runtime,
workflow, fixture or report-schema implementation remains queued. Historical
evidence is unchanged. Reverting this planning edit restores the prior text.

## Explicit Non-Goals

- Prove historical failing-first chronology.
- Infer every input that could influence arbitrary Python or pytest execution.
- Prove that linked tests completely represent stakeholder intent.
- Prove overall correctness, architecture quality, security, or absence of defects.
- Replace full tests, contracts, static analysis, security checks, or independent review.
- Redefine generic Code Review changed-scope behavior; that is module-owned.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: [#662](https://github.com/nold-ai/specfact-cli/issues/662)
- **Repository**: `nold-ai/specfact-cli`
- **Issue Type**: User Story
- **Last Synced Status**: open / replacement reconciliation only, 2026-09-20
- **Parent Feature**: [#374](https://github.com/nold-ai/specfact-cli/issues/374)
- **Parent Epic**: [#258](https://github.com/nold-ai/specfact-cli/issues/258)
- **Blocked By**: replacement delivery [#740](https://github.com/nold-ai/specfact-cli/issues/740)
- **Paired Implementation**: [modules #481](https://github.com/nold-ai/specfact-cli-modules/issues/481)
- **Historical references only**: closed modules #368 and superseded correction PR #412; neither is an active release dependency.
- **R08**: abandoned, not a follow-up prerequisite.
- **Readiness**: refresh hierarchy/project/concurrency state before reconciliation work.
