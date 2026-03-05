# core-decoupling-cleanup Specification

## Purpose
TBD - created by archiving change module-migration-06-core-decoupling-cleanup. Update Purpose after archive.
## Requirements
### Requirement: Core Package Ownership Boundary

The `specfact-cli` core package SHALL include only components required for permanent core runtime responsibilities and SHALL not retain bundle-only implementation structures after module extraction/slimming.

#### Scenario: Residual bundle-only components are identified and removed from core

- **GIVEN** module extraction and core slimming are complete
- **WHEN** the decoupling cleanup runs
- **THEN** components in core that are only needed by extracted bundles are either moved out or replaced by stable interfaces.

#### Scenario: Boundary regression tests prevent re-coupling

- **GIVEN** the decoupling cleanup is complete
- **WHEN** tests validate core import boundaries
- **THEN** tests fail if new bundle-only couplings are introduced into core.

#### Scenario: User-facing command behavior remains stable

- **GIVEN** internal decoupling refactors are applied
- **WHEN** users run supported core and installed-bundle commands
- **THEN** observable command behavior remains compatible with current migration topology.

### Requirement: Core Must Not Import From Bundle Packages

The `specfact-cli` core (`src/specfact_cli/`) SHALL NOT import from bundle packages (`backlog_core`, `bundle_mapper`, or other extracted bundle namespaces). Core modules (init, module_registry, upgrade) and shared infrastructure (models, utils, adapters, registry) must remain decoupled from bundle implementation details.

#### Scenario: Core import boundary is enforced by regression tests

- **GIVEN** core and bundle packages coexist in the repository
- **WHEN** boundary tests run
- **THEN** any file under `src/specfact_cli/` that imports from `backlog_core` or `bundle_mapper` causes the test to fail.

### Requirement: Migration Acceptance Criteria

The decoupling cleanup SHALL meet documented acceptance checks before archive and spec sync are finalized.

#### Scenario: Archive readiness checks are satisfied

- **GIVEN** migration implementation artifacts and boundary tests are complete
- **WHEN** archive validation evaluates migration acceptance checks
- **THEN** inventory/classification documentation exists
- **AND** core import boundary tests pass
- **AND** quality-gate status and documentation updates are recorded for the change.

### Requirement: MIGRATE-Tier Enforcement

Core modules (init, module_registry, upgrade) SHALL NOT import from MIGRATE-tier paths. MIGRATE-tier code (agents, analyzers, backlog, sync, etc.) lives in specfact-cli-modules. Regression test `test_core_modules_do_not_import_migrate_tier` enforces this.

#### Scenario: Core module imports from MIGRATE-tier paths are blocked

- **GIVEN** core modules (`init`, `module_registry`, `upgrade`) are validated in CI and local quality gates
- **WHEN** any of those modules imports from a MIGRATE-tier path
- **THEN** `test_core_modules_do_not_import_migrate_tier` fails and prevents merge until the coupling is removed.

### Requirement: Package-Specific Artifact Removal

Package-specific artifacts not required by CLI core SHALL be removed from specfact-cli and live in respective packages (specfact-cli-modules). `MIGRATION_REMOVAL_PLAN.md` documents phased removal. Phase 1: remove dead code (e.g. `templates.bridge_templates`).

#### Scenario: Sync-runtime unit tests are owned by modules repo

- **GIVEN** `sync_runtime` implementation is owned by `specfact-project` in specfact-cli-modules
- **WHEN** decoupling migration updates test ownership
- **THEN** legacy core tests under `specfact-cli/tests/unit/sync/` are migrated to `specfact-cli-modules/tests/unit/specfact_project/sync_runtime/` and core boundary test `test_core_repo_does_not_host_sync_runtime_unit_tests` enforces this.

