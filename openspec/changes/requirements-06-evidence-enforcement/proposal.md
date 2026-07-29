# Change: Enforce Requirements Evidence in CLI Delivery Gates

## Why

The Requirements module can produce deterministic evidence reports, but the
core CLI does not yet enforce those reports before review or in pull-request
CI. Delivery can therefore proceed with invalid, unlinked, or absent
requirements evidence.

## What Changes

- Add a staged pre-commit requirements-evidence gate before code review and
  contract checks. It retains the module's JSON and Markdown remediation
  reports before returning a non-zero status.
- Add a matching pull-request CI gate that verifies the fixture, publishes a
  concise job summary, and uploads the report for either a passing or failing
  verdict.
- Consume only the released, SHA-pinned fixture from
  `nold-ai/specfact-cli-modules#361`; never execute a mutable checkout or an
  unverified module source.
- Preserve the module-owned evidence semantics, including its `--staged` and
  `--base-ref` modes. Core owns delivery-gate orchestration and artifact
  retention only.

## Capabilities

### New Capabilities

- `requirements-evidence-delivery-gate`: Enforce a released Requirements
  evidence result before core delivery gates while retaining auditable reports.

## Impact

- Affected delivery surfaces: `.pre-commit-config.yaml`,
  `scripts/pre-commit-quality-checks.sh`, `ci/module-fixture.lock.json`, and
  pull-request CI workflows.
- Affected tests: focused script/pre-commit and workflow-contract coverage.
- Affected documentation: delivery-gate and Requirements evidence guidance;
  command documentation remains owned by the modules repository.
- Compatibility: modules #361 was released as `specfact-requirements` 0.3.3
  at `2438372f8e34c96d4e474afa4c66c92a9cee7979`. Its public command requires
  `--output`, exactly one of `--staged` or `--base-ref`, and optionally accepts
  `--summary`; it writes requested reports before returning a red verdict.
- Rollback: remove the core hook and CI job, restore the previous fixture lock,
  and retain previously uploaded CI artifacts. No upstream source is changed.

## Source Tracking

- **GitHub Issue**: #657
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/657>
- **Parent Feature**: #374 End-to-End Integration Proof
- **Parent Epic**: #258 Evidence dogfooding and governance
- **Paired Modules Issue**: nold-ai/specfact-cli-modules#361
- **Last Synced Status**: open / Todo (2026-07-29)
- **Released Fixture**: `specfact-requirements` 0.3.3 at
  `2438372f8e34c96d4e474afa4c66c92a9cee7979` (modules PR #365)
- **Resolved Dependency**: modules #361, closed 2026-07-29
