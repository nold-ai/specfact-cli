# Change: Zero-finding code review — dogfooding specfact review on specfact-cli

## Why

SpecFact CLI's `specfact review` command is our flagship code-quality enforcement tool, yet the branch began from a failing dogfood self-review baseline recorded in `TDD_EVIDENCE.md`. This worktree is remediating that backlog across core source files, scripts, and tools so the repository can prove the tool works end-to-end on itself.

The branch already contains broad remediation work. The OpenSpec artifacts therefore need to preserve the branch-local implementation tracking while also reflecting the now-authoritative proposal scope and the new clean-code compliance delta added after the 2026-03-22 plan review.

## What Changes

- **FIX** type-safety, contract, logging, and complexity findings in the files touched by this remediation branch until the dogfood review scenarios pass.
- **ADD** dogfood self-review acceptance criteria and spec deltas for the repository reviewing itself.
- **ADD** task tracking for the active remediation branch, including existing failing-first evidence and remaining validation work already performed in this worktree.
- **EXTEND** once the baseline review reaches zero findings, run the expanded clean-code categories (`naming`, `kiss`, `yagni`, `dry`, `solid`) so this branch stays aligned with the downstream `clean-code-01-principle-gates` prerequisite.
- **FIX** branch-local regressions introduced during remediation so the branch remains internally consistent while the wider review backlog is reduced.

## Capabilities

### New Capabilities

- `dogfood-self-review`: specification for running and passing `specfact review` against the specfact-cli repo itself, including the clean-code follow-on proof.

### Modified Capabilities

- `code-review-module`: the review tool must be able to scan itself without self-referential failures.
- `debug-logging`: print-to-logger remediation in touched files must stay compatible with the dogfood proof.
- `contract-runner`: branch remediation expands missing icontract coverage in the touched files.
- `review-cli-contracts`: review CLI command behavior must remain compatible with the type-safe, contract-enforced codebase.

## Impact

- **Files**: broad remediation across `src/specfact_cli/`, `scripts/`, `tools/`, and touched module paths already present in this branch.
- **CI**: this change remains the prerequisite proof before the downstream clean-code principle gate can harden repo-wide enforcement.
- **Sequencing**: branch-local implementation tracking stays authoritative for what is already done in this worktree, while proposal scope now matches the updated main-repo change record.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #423
- **Issue URL**: https://github.com/nold-ai/specfact-cli/issues/423
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open
