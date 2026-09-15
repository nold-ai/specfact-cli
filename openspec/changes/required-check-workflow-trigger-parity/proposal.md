# Emit required workflow checks on every supported pull request

## Why

Docs Review and Contract Validation are required checks, but their workflow-level pull-request path filters suppress
runs on some documentation-only or ancestry-only changes. PR #732 cannot satisfy these checks for release PR #731.
GitHub excludes manually dispatched job checks from required pull-request status evaluation, even when they pass on
the same commit.

## What Changes

- Remove pull-request path filters from Docs Review and SpecFact CLI Validation.
- Preserve `main`/`dev` branch scope, complete push filters, validation behavior, immutable fixtures, permissions, and
  authority policy.
- Skip optional PR comment publication for forks and warn on API permission denial for other read-only tokens while
  retaining actual validation and its failure gate.
- Add prospective regression tests and authenticated failing-first/passing-after evidence for both required workflows.

## Impact

Affected specification: `required-check-workflow-triggers`. Production scope is two workflow trigger blocks and the
optional comment step condition. More PRs run the existing docs and contract jobs; CI cost increases by those existing
jobs per previously filtered PR. No runtime API, package version, dependency, or signed module content changes.
Rollback is a reviewed revert but restores the missing-check defect.

Documentation research: GitHub's required-status-check troubleshooting documentation, accessed 2026-09-15
Europe/Berlin, confirms `workflow_dispatch` is ineligible and workflow path filtering leaves required checks pending:
<https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks>.
End-user command documentation and navigation remain accurate; this change affects maintainer CI only.

## Source Tracking and Readiness

Bug #733 under existing Feature #355 / Epic #194. Owner djm81; labels bug, openspec, change-proposal, devops-backlog;
SpecFact CLI project In Progress owned by this task. No native blocked-by dependencies. High priority is recorded in
the issue because this project has no Priority field. This fix unblocks PR #732 and release PR #731. The completed
parent feature is not reopened.

Fresh cycle base: public dev `a4a04786588d61fbc9105137dbaf0236fce009ee`, tree
`a696d32965bdc1f702684f8d981dc28ece3e9ffd`. The earlier PR #732 attempt contained an ancestry merge and its RED
binding was rejected; this new branch excludes that merge, preserves the test/mapping bytes and does not rewrite
history. Existing documentation proof tests and retained evidence remain unchanged.
