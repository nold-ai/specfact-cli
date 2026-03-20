# Change: code-review-zero-findings

## Why

The `code-review-zero-findings` worktree is remediating the backlog of findings uncovered by the dogfood self-review baseline recorded in `TDD_EVIDENCE.md`. The change needs explicit OpenSpec scope because the branch already contains broad remediation work across core source files, scripts, and tools, but the original proposal/tasks/spec delta were never committed.

Without an explicit change record, the branch violates the repository's spec-first workflow and the remaining remediation work cannot be audited against a concrete success condition.

## What Changes

- **ADD** dogfood self-review acceptance criteria for the `specfact code review run --scope full` flow.
- **ADD** task tracking for the zero-findings remediation branch, including existing failing-first evidence and remaining validation.
- **FIX** type-safety, contract, and clean-code findings in the files touched by this change until the dogfood review scenarios pass.
- **FIX** branch-local regressions introduced during remediation so the branch remains internally consistent while the wider review backlog is reduced.

## Capabilities

### Modified Capabilities

- `review-run-command`: gains a dogfood scenario for running the review workflow against the SpecFact CLI repository itself.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: TBD
- **Issue URL**: TBD
- **Last Synced Status**: in_progress
- **Sanitized**: false
