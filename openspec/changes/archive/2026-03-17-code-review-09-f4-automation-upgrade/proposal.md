# Change: Integrate specfact code review into Pre-Commit and Portable Project Workflows

## Why

The current `specfact-cli` repository does not wire `specfact code review run`
into its own `.pre-commit-config.yaml`, so contributors can still commit code
without the governed review pass that the new module was built to provide.
There is also no grounded, copyable guidance for how other projects should add
the same gate before a commit is considered green.

This change replaces the stale F-4 automation framing with a repository-owned
integration: run code review as part of pre-commit in this repo, document the
same pattern for any project, and treat the reward ledger as local JSON by
default with optional backend persistence when configured.

## What Changes

- Add a repository-local pre-commit hook in `.pre-commit-config.yaml` that runs
  `specfact code review run` on the relevant staged files before a commit can
  pass.
- Add any repo-owned helper or wrapper logic needed to make the pre-commit
  review gate deterministic, actionable, and compatible with this repo's local
  environment.
- Document how to add the same review gate to any project later, including a
  copyable pre-commit example and commit-blocking semantics.
- Document optional `house_rules` workflow usage for projects that want the
  review gate to include project-specific guidance.
- Document that the reward ledger is expected to be local JSON in most cases,
  while Supabase or another database backend remains optional when configured.

## Capabilities

### New Capabilities

- `pre-commit-review-gate`: repository-local pre-commit enforcement using
  `specfact code review run`
- `portable-review-adoption`: reusable guidance for adding the review gate to
  other projects

### Modified Capabilities

- `reward-ledger`: document and validate JSON-first local usage with optional
  configured backend support

---

## Impact

- Depends on `code-review-01-module-scaffold`, `code-review-02-ruff-radon-runners`, `code-review-03-type-governance-runners`, `code-review-04-contract-test-runners`, `code-review-06-reward-ledger`
- Affects `.pre-commit-config.yaml`, review-gate integration helpers, and
  `docs/modules/code-review.md`
- Keeps the commit gate local and repo-owned instead of assuming external n8n
  workflow nodes that are not present in the current codebase
- Clarifies the recommended deployment posture for the ledger: local JSON by
  default, optional remote persistence when explicitly configured

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #393
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/393>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: synced after rewrite
