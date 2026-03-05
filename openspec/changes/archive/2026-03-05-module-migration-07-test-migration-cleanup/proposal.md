# Change: Test Migration Cleanup After Core Slimming

## Why

After core slimming and shim removal, broad `smart-test-full` failures remain in `specfact-cli` that are not direct regressions of the migrated runtime behavior. These failures are primarily migration debt in legacy test assumptions (flat command paths, removed in-repo module imports, and signing fixture expectations).

`module-migration-04` and `module-migration-05` have explicit scope boundaries:

- migration-04: shim removal behavior only
- migration-05: modules-repo quality parity and bundle-test migration

This follow-up change owns residual `specfact-cli` suite cleanup so migration work can be completed without mixing unrelated refactors.

## What Changes

- Migrate remaining legacy test imports from removed paths (for example `specfact_cli.modules.*`) to supported grouped/bundle interfaces.
- Re-home module behavior E2E/integration tests from `specfact-cli` to `specfact-cli-modules` where they logically belong after extraction.
- Keep only core-runtime contract tests in `specfact-cli` (bootstrap, module lifecycle, grouped command mounting, compatibility/deprecation shims).
- Update or retire tests that still assume removed flat command topology where no supported runtime surface exists anymore.
- Harden script/signing fixtures to avoid environment-coupled failures (for example malformed/missing test PEM inputs).
- Establish deterministic test selectors and independent green gates for `specfact-cli` and `specfact-cli-modules`.

## Scope

- **In scope**:
  - `specfact-cli` test cleanup limited to core runtime ownership
  - migration of extracted-module tests to `specfact-cli-modules`
  - fixture hardening tied to post-migration command/module topology
- **Out of scope**: feature behavior changes in runtime command implementations (those belong to feature changes).

## Baseline (from migration-03 handoff)

- Latest migration-03 evidence reference:
  - `openspec/changes/module-migration-03-core-slimming/TDD_EVIDENCE.md`
- Full-suite failure baseline reference:
  - `logs/tests/test_run_20260303_194459.log`
  - Captured on 2026-03-03 from `smart-test-full` path: `2738` collected, `359 failed`, `19 errors`, `22 skipped`.
- Deferred failure buckets for this change:
  - import-path migration (`specfact_cli.modules.*` references in tests),
  - command topology migration (flat command assumptions vs grouped/available commands),
  - repository ownership migration (module tests moved out of core repo),
  - signing/script fixture hardening (deterministic local assets in CI).

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #339
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/339>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
- **Sanitized**: false
