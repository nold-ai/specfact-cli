## Recovery review — 2026-09-20

Recovered from uncommitted planning files on `feature/cli-val-07-code-review-gate-adoption`; the source worktree contains only this proposal and its change-order edit. Imported into local `dev` and the R09 planning worktree. No runtime changes were imported. Historical readiness and version identities below are dated context and must be revalidated before implementation. Recovery validation preserves existing staged-review scenarios and classifies previously nonexistent requirement headers as ADDED, avoiding invalid archive replacements. Canonical C14 follow-up reconciliation remains a prerequisite to final C15 specification promotion.

# Change Validation

## Repository reality

- Current core consumes legacy code-review reports and has no released C14
  protected schema 1.6 verifier on `dev`.
- No signed C15 schema 1.7 module release exists.
- Therefore production consumer tests/code cannot truthfully be implemented or
  validated against the planned interface yet.

## Sequential specification promotion

C15 modifies the existing pre-commit requirement and the protected-range and
green-check requirements introduced by C14. Apply these replacements only after prerequisite
C14 integration and native archival; do not archive C15 against today's missing
protected-range capability. The schema 1.7-only blocking policy then replaces,
rather than coexists with, C14's schema 1.6 acceptance rule.

## Decision

Validate and review the OpenSpec plan now. Keep production tests/code blocked
until the signed upstream contracts and public readiness tasks are complete.

## Planning review follow-up — 2026-09-20

Reopened implementation-time worktree readiness and ordered reviewed integration/authenticated verifier publication before protected C15 activation; strict OpenSpec and scoped Markdown/whitespace pass. Existing canonical C14-predecessor archive notice remains expected until its native integration/archival.
