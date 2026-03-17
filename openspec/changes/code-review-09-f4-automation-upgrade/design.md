# Design: Pre-Commit Code Review Integration

## Context

The existing `code-review-09` proposal was based on an internal automation plan
that referenced `n8n` F-2/F-4 workflows and a `coding-workflow.js` script. That
integration surface is not grounded in the current `specfact-cli` repository.
What this repository does own is its `.pre-commit-config.yaml`, its
documentation, and the public guidance it gives other projects for adopting
`specfact code review run`.

The design therefore pivots from speculative external workflow nodes to a
portable repository-owned integration: run review during pre-commit, document
how to adopt the same gate elsewhere, and make the recommended ledger posture
explicit for local/offline use.

## Goals / Non-Goals

**Goals:**
- Gate commits in this repository on `specfact code review run`
- Keep the gate scoped to relevant staged files so it is fast enough for local
  use
- Provide copyable setup guidance for other projects
- Document optional `house_rules` integration without assuming a specific AI
  orchestration wrapper
- Treat local JSON ledger storage as the default deployment assumption in docs,
  while allowing optional configured backends

**Non-Goals:**
- Implementing or validating external `n8n` workflows
- Adding new review scoring semantics
- Making Supabase mandatory for local review-gate adoption

## Decisions

### Decision: Integrate through `.pre-commit-config.yaml`

The repository already uses pre-commit. Adding a local hook there is the most
grounded enforcement point because it exists in-repo, runs before commit
success, and maps cleanly to the user's request.

### Decision: Use a repo-owned wrapper when direct hook wiring is not enough

If the review command needs staged-file filtering, local runtime invocation, or
clearer setup errors than a raw hook entry can provide, the repo should own a
small wrapper script rather than embedding brittle shell logic directly in
`.pre-commit-config.yaml`.

### Decision: Document optional house-rules workflow usage, not a mandatory flag

Projects that maintain `house_rules` should be able to wire that guidance into
their broader review workflow, but this change should not claim a concrete
`--rules` flag or a coding-session wrapper contract that the repo does not
currently expose.

### Decision: Present the ledger as JSON-first in adoption guidance

The current ledger capability already supports local JSON fallback. For local
pre-commit adoption, the documentation should frame JSON storage as the normal
path and describe Supabase or another backend as optional when configured,
rather than as a required default dependency.

## Risks / Trade-offs

- [Risk] Running full review during pre-commit could be too slow for day-to-day
  use.
  Mitigation: scope the hook to relevant staged files and keep the command
  focused on commit-local changes.
- [Risk] Developers may see tool-setup failures as spurious commit blockers.
  Mitigation: provide actionable installation/setup guidance in the hook output
  and docs.
- [Risk] Documentation about optional ledger backends may drift from the
  existing reward-ledger implementation details.
  Mitigation: keep the guidance phrased in deployment terms and only widen the
  reward-ledger spec if an implementation change becomes necessary.

## Open Questions

1. Whether the pre-commit hook should call `specfact code review run --score-only`
   directly or a wrapper script that normalizes staged-file handling
2. Whether the repo should provide a first-party sample hook snippet in
   `docs/modules/code-review.md` only, or also as a checked-in reusable example
   file
