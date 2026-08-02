# Change: Deliver Empirical Requirements Proof in Local and CI Gates

## Why

The released core gate validates Requirements evidence before review and
contract checks, but that evidence proves source validity and declared test
links rather than current-run behavioral execution. The pull-request workflow
also runs only for a narrow path set, so a product-interface change can avoid an
explicit Requirements impact decision. Delivery needs a safe bridge from a
module-owned scenario test plan to current-run test results and review context.

## What Changes

- Extend staged pre-commit enforcement to validate changed scenario,
  touchpoint, and exact-test-plan completeness while keeping local execution
  bounded and fast.
- Extend pull-request CI to run for relevant product, contract, test, and
  requirement-source changes; emit an explicit auditable skipped result only
  after a deterministic no-impact decision.
- Consume only the reviewed, signed `nold-ai/specfact-requirements` 0.4.3
  release from modules #368/#369; validate its
  structured test plan, execute approved exact selectors without shell
  interpretation, retain JUnit output, and delegate reconciliation back to the
  released Requirements command.
- Pass only finalized Requirements proof into the released Code Review context
  interface, then run the existing contract gates.
- Publish the plan, JUnit results, final JSON/Markdown proof, review provenance,
  and concise job summary before enforcing the authoritative verdict.
- Keep Requirements semantics module-owned and keep cross-domain aggregation
  owned by `validation-02-full-chain-engine`.

## Capabilities

### New Capabilities

- `requirements-runtime-proof-delivery`: Safely execute a module-produced
  scenario proof plan and retain current-run evidence in local/CI delivery.
- `requirements-proof-review-handoff`: Supply finalized Requirements proof to
  Code Review without merging or replacing either verdict.

## Impact

- Affected delivery surfaces: pre-commit Block 2, the Requirements evidence
  workflow or PR orchestrator, immutable fixture lock/verification, frozen test
  execution, artifact upload, and branch-protection documentation.
- Affected tests: script, selector-safety, staged-index, workflow-contract,
  JUnit handoff, report-retention, review-order, and failure-order coverage.
- Affected documentation: core Requirements evidence adoption and Code Review
  delivery guidance; module command reference remains modules-owned.
- Dependencies: blocked by modules User Story
  [#368](https://github.com/nold-ai/specfact-cli-modules/issues/368), PR
  [#369](https://github.com/nold-ai/specfact-cli-modules/pull/369), and the
  signed immutable `nold-ai/specfact-requirements` 0.4.3 release. Produces a bounded Requirements signal consumable
  by, but does not implement, `validation-02-full-chain-engine`.
- Rollback: restore the current static evidence gate and remove targeted test
  execution/review context while retaining previously uploaded proof artifacts.

## Quality Standards

- Preserve module-owned verdicts and execute selectors only through validated
  argument arrays in the frozen environment; never use `eval`, shell-generated
  command text, or mutable module sources.
- Use spec-first, failing-before TDD for every gate behavior and retain
  actionable artifacts before any blocking exit.
- Run workflow lint, focused/full tests, contract gates, independent analysis,
  strict module verification, and fresh SpecFact code review before delivery.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: [#662](https://github.com/nold-ai/specfact-cli/issues/662)
- **GitHub Type**: User Story
- **Parent Feature**: [#374](https://github.com/nold-ai/specfact-cli/issues/374)
- **Parent Epic**: [#258](https://github.com/nold-ai/specfact-cli/issues/258)
- **Project**: SpecFact CLI (`Todo`)
- **Extends**: `requirements-06-evidence-enforcement`
- **Blocked By**: [nold-ai/specfact-cli-modules#368](https://github.com/nold-ai/specfact-cli-modules/issues/368) (native GitHub dependency)
- **Paired Modules Change**: `requirements-07-scenario-runtime-proof`
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed / Todo (2026-08-02)
