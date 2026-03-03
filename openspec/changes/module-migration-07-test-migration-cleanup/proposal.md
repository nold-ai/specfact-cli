# Change: module-migration-07 - Test Migration Cleanup After Core Slimming

## Why

After core slimming and shim removal, broad `smart-test-full` failures remain in `specfact-cli` that are not direct regressions of the migrated runtime behavior. These failures are primarily migration debt in legacy test assumptions (flat command paths, removed in-repo module imports, and signing fixture expectations).

`module-migration-04` and `module-migration-05` have explicit scope boundaries:

- migration-04: shim removal behavior only
- migration-05: modules-repo quality parity and bundle-test migration

This follow-up change owns residual `specfact-cli` suite cleanup so migration work can be completed without mixing unrelated refactors.

## What Changes

- Migrate remaining legacy test imports from removed paths (for example `specfact_cli.modules.*`) to supported grouped/bundle interfaces.
- Update E2E and integration tests that still assume flat shim commands or bundled-in-core modules.
- Harden script/signing fixtures to avoid environment-coupled failures (for example malformed/missing test PEM inputs).
- Establish deterministic test selectors for migration-scope validation vs full-suite validation.

## Scope

- **In scope**: `specfact-cli` test code cleanup and fixture hardening tied to post-migration command/module topology.
- **Out of scope**: feature behavior changes in runtime command implementations (those belong to feature changes).

## Baseline (from migration-03 handoff)

- Latest migration-03 evidence reference:
  - `openspec/changes/module-migration-03-core-slimming/TDD_EVIDENCE.md`
- Full-suite failure baseline reference:
  - `logs/tests/test_run_20260303_194459.log`
  - Captured on 2026-03-03 from `smart-test-full` path: `2738` collected, `359 failed`, `19 errors`, `22 skipped`.
- Deferred failure buckets for this change:
  - import-path migration (`specfact_cli.modules.*` references in tests),
  - command topology migration (flat command assumptions vs grouped commands),
  - signing/script fixture hardening (deterministic local assets in CI).

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #339
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/339>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
- **Sanitized**: false
