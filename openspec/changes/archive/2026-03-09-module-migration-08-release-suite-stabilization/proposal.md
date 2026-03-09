# Change: Release Suite Stabilization After Module Migration

## Why

After merging the module migration wave into `dev`, the current `specfact-cli` test baseline still contains broad unit, integration, and end-to-end failures. The failures are clustered around post-migration ownership and command-topology drift:

- tests still invoke removed flat or pre-grouped command paths,
- tests still assume extracted bundle code remains inside `specfact-cli`,
- tests that belong to `specfact-cli-modules` are still executed in core,
- a smaller subset of core runtime tests now expose real regressions in `init`, grouped command mounting, and deterministic signing fixtures.

The release PR for `v0.40.0` cannot be finalized while the core branch is red. This change owns the residual stabilization work needed to bring the merged migration branch back to a valid release baseline.

## What Changes

- Reclassify failing unit/integration/E2E tests into:
  - core-runtime ownership that must keep passing in `specfact-cli`,
  - extracted bundle behavior that must move to `specfact-cli-modules` or be retired from core,
  - genuine core regressions that need implementation fixes.
- Update stale tests to the supported grouped command surface and lean-core behavior.
- Remove or rewrite core tests that still depend on removed in-repo bundle modules or obsolete command shims.
- Fix genuine core regressions in bundle mounting / init / fixture behavior uncovered by the failing suites.
- Record pre-fix and post-fix evidence for representative failure buckets and the broader reruns.

## Scope

- **In scope**:
  - residual red tests in `specfact-cli` after migration merge,
  - core runtime regressions exposed by those tests,
  - migration of incorrect test expectations to current grouped command and lean-core semantics,
  - deterministic signing/test fixture cleanup needed for green CI.
- **Out of scope**:
  - new end-user features,
  - adding back removed flat command shims,
  - implementing missing extracted-bundle behavior in core instead of moving/adjusting ownership.

## Baseline

- Unit baseline: `logs/tests/unit_test_run_20260306_005445.log` with `73 failed, 702 passed, 2 skipped`.
- Integration baseline: `logs/tests/integration_test_run_20260306_005734.log` with `118 failed, 64 passed`.
- Representative failure buckets observed:
  - `No such command 'code'`, `No such command 'plan'`, `No such command 'policy'`
  - removed file-path assumptions under `src/specfact_cli/modules/...`
  - stale flat-command or pre-modularized suggestions/assertions
  - `init` bundle-install tests not invoking the installer as expected
  - signing fixture failure due malformed PEM test input.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
- **Sanitized**: false
