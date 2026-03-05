# Tasks: module-migration-06-core-decoupling-cleanup

## 1. Create git worktree branch from dev

- [x] 1.1 `git fetch origin`
- [x] 1.2 `git worktree add ../specfact-cli-worktrees/feature/module-migration-06-core-decoupling-cleanup -b feature/module-migration-06-core-decoupling-cleanup origin/dev`
- [x] 1.3 `cd ../specfact-cli-worktrees/feature/module-migration-06-core-decoupling-cleanup`
- [x] 1.4 `hatch env create`

## 2. Spec and tests first (TDD required)

- [x] 2.1 Add/update spec delta under `specs/core-decoupling-cleanup/spec.md` for ownership boundary and migration acceptance criteria.
- [x] 2.2 Add failing tests that detect residual non-core coupling (imports/usage paths from core into bundle-only components).
- [x] 2.3 Record failing evidence in `TDD_EVIDENCE.md`.

## 3. Decoupling implementation

- [x] 3.1 Produce inventory/classification table for candidate core components (keep/move/interface).
- [x] 3.2 Move/refactor components classified as non-core out of `specfact-cli` core (or replace with interface contracts).
- [x] 3.3 Update dependent imports in core and tests.
- [x] 3.4 Re-run tests and record passing evidence in `TDD_EVIDENCE.md`.

## 4. Quality gates

- [x] 4.1 `hatch run format`
- [x] 4.2 `hatch run type-check`
- [x] 4.3 `hatch run lint`
- [x] 4.4 `hatch run contract-test`
- [x] 4.5 `hatch run smart-test`

## 5. Documentation and closure

- [x] 5.1 Update docs/architecture boundary notes for core vs modules-repo ownership.
- [x] 5.2 Update `openspec/CHANGE_ORDER.md` status/dependencies if scope changes.
- [x] 5.3 Create PR to `dev` with migration evidence and compatibility notes.

## 6. Extended scope: migrate package-specific artifacts (per #338)

- [x] 6.1 Add `MIGRATION_REMOVAL_PLAN.md` with phased removal of MIGRATE-tier code.
- [x] 6.2 Add `test_core_modules_do_not_import_migrate_tier` — core modules must not add MIGRATE imports.
- [x] 6.3 Remove `templates.bridge_templates` (dead code; only tests used it; specfact-project has sync_runtime).
- [x] 6.4 Remove `tests/unit/templates/test_bridge_templates.py`.
- [x] 6.5 Update `CORE_DECOUPLING_INVENTORY.md` with MIGRATE-tier removal status.
- [x] 6.6 Run quality gates; record evidence.

## 7. Cross-repo test migration continuation (2026-03-05)

- [x] 7.1 Add failing core boundary test `test_core_repo_does_not_host_sync_runtime_unit_tests`.
- [x] 7.2 Migrate legacy core sync-runtime unit tests from `tests/unit/sync/` to modules repo path `tests/unit/specfact_project/sync_runtime/`.
- [x] 7.3 Remove migrated sync-runtime unit tests from `specfact-cli` core repository.
- [x] 7.4 Verify post-migration: core boundary test passes and migrated modules tests pass.
- [x] 7.5 Update `TDD_EVIDENCE.md`, `CORE_DECOUPLING_INVENTORY.md`, and `MIGRATION_REMOVAL_PLAN.md`.
