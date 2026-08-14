# Change: Deliver Current-Run Requirements Evidence in Local and CI Gates

## Why

Issue #662 asks SpecFact to execute exact tests linked to changed requirement scenarios and to report whether those tests were collected and passed in the current delivery run. The existing R07 implementation mixed that bounded observation with a stronger historical claim: proving that the tests failed earlier and remained unchanged through arbitrary Python and pytest dependency behavior.

That stronger claim caused the gate to grow into a static approximation of pytest execution. It also made a current-run Requirements result depend on historical evidence that issue #662 did not require. The two claims need independent contracts and independent statuses.

## What Changes

- Keep R07 responsible for lifecycle-derived planning maturity, accepted mappings, exact selector plans, safe current-run execution, JUnit reconciliation, explicit no-impact decisions, artifact publication, and the independent Code Review handoff.
- Define a current-run pass precisely: every required selector was collected exactly once and passed at the evaluated source revision in the pinned execution environment.
- Remove Git-bound failing-first proof, legacy-ledger migration, and static pytest/Python dependency-closure inference from R07.
- Move historical red-to-green proof to `requirements-08-bounded-red-green-proof`, where the red and final commits are replayed under an explicit bounded Git policy.
- Preserve Requirements and Code Review as independent verdicts. Requirements evidence is review context and provenance; it does not rewrite review findings or scores.

## Capabilities

### Modified Capabilities

- `requirements-runtime-proof-delivery`: Plan and safely execute exact Requirements selectors, then report current-run observations without implying historical chronology.
- `requirements-evidence-delivery-gate`: Pin the reviewed module release, retain artifacts, and enforce the current-run Requirements and Code Review decisions independently.

## Impact

- Planning scope: OpenSpec artifacts only in this commit. No runtime, workflow, test, fixture, or report-schema implementation changes are included.
- Later implementation may simplify or replace prior-red provenance code after R08 is ready; it must not add more AST rules for imports, plugins, configuration, data reads, aliases, mutation, or dynamic execution.
- The module-side R07 contract must first separate current execution from historical chronology and publish a signed release before core adopts the corrected report.
- Rollback: retain the current R07 runtime behind its existing branch while the corrected contract is implemented; the planning commit is reversible by reverting one commit.

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
- **Last Synced Status**: open, live-read 2026-08-13T21:49:59Z
- **Assignee**: `djm81`
- **Labels**: `enhancement`, `openspec`, `change-proposal`
- **Project Assignment / Project Status**: not exposed by the current connector; implementation is blocked until a fresh hierarchy-cache/project check verifies both and rules out concurrent work.
- **Parent Feature**: [#374](https://github.com/nold-ai/specfact-cli/issues/374)
- **Parent Epic**: [#258](https://github.com/nold-ai/specfact-cli/issues/258)
- **Blocked By**: [specfact-cli-modules#368](https://github.com/nold-ai/specfact-cli-modules/issues/368), closed/completed; the corrected signed release planned by modules PR #412 is the remaining implementation dependency.
- **Concurrency**: no current project status was available to prove whether #662 is already in progress; task B.3 is a mandatory stop condition before implementation.
- **Extends**: `requirements-06-evidence-enforcement`; archive R06 first, then apply this exact-name `MODIFIED` delta.
- **Paired Modules Change**: corrected `requirements-07-scenario-runtime-proof` and [modules PR #412](https://github.com/nold-ai/specfact-cli-modules/pull/412)
- **Follow-up**: `requirements-08-bounded-red-green-proof`
- **Planning correction date**: 2026-08-13

