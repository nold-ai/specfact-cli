# Change: Core Decoupling Cleanup After Module Extraction

## Why

After module extraction (`module-migration-02`) and core slimming (`module-migration-03`), some non-core structures can still remain in `specfact-cli` core and stay coupled to extracted module behavior (for example, models/helpers/utilities only used by bundles now hosted in `specfact-cli-modules`).

Keeping this coupling in core increases maintenance burden and blurs core boundaries. The core package should own only runtime/lifecycle/security/bootstrap responsibilities required by permanent core commands.

## What Changes

- **INVENTORY** residual non-core components still in `specfact-cli` that are tied to extracted bundles.
- **CLASSIFY** each component as: keep-in-core (true shared/core), move-to-modules-repo, or replace with stable interface contract.
- **MOVE/REFACTOR** residual non-core components out of core where appropriate (without changing user-visible command behavior).
- **UPDATE** imports and boundaries so core no longer depends on bundle-only internals.
- **ADD** regression tests and boundary checks preventing reintroduction of non-core coupling.
- **UPDATE** docs/architecture notes for the final ownership boundary between `specfact-cli` and `specfact-cli-modules`.

## Capabilities

### New Capabilities

- `core-decoupling-boundary`: explicit, test-enforced boundary ensuring `specfact-cli` core excludes bundle-only components.

### Modified Capabilities

- `module-migration-boundaries`: finalized ownership map for models/helpers/utilities shared between core and bundles.

## Impact

- **Affected specs**:
  - `core-decoupling-cleanup` (new)
- **Affected code**:
  - `src/specfact_cli/models/` (candidate subset)
  - `src/specfact_cli/utils/` (candidate subset)
  - `src/specfact_cli/registry/` (interface-only boundary updates)
  - `tests/unit/`, `tests/integration/` boundary and regression tests
- **Integration points**:
  - `specfact-cli-modules` package imports and shared abstractions
  - migration-05 dependency-decoupling outputs
- **Backward compatibility**:
  - No user-facing command topology changes intended.
  - Internal import-path changes may require test and module fixture migration.
- **Blocked by**:
  - `module-migration-03-core-slimming`
  - `module-migration-05-modules-repo-quality` baseline for bundle ownership and tests

## Baseline (from migration-03 handoff)

- Full-suite deferred baseline log:
  - `logs/tests/test_run_20260303_194459.log`
  - Captured on 2026-03-03 from `smart-test-full` path: `2738` collected, `359 failed`, `19 errors`, `22 skipped`.
- Priority buckets to address in this change:
  - residual core<->bundle coupling surfaces (models/helpers/utilities),
  - compatibility shims/import references keeping non-core assumptions in core tests/utilities,
  - shared boundary contracts needed by `specfact-cli-modules` without pulling bundle-owned internals back into core.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #338
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/338>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
- **Sanitized**: false
