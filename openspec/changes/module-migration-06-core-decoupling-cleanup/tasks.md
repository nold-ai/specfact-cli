# Tasks: module-migration-06-core-decoupling-cleanup

## 1. Create git worktree branch from dev

- [ ] 1.1 `git fetch origin`
- [ ] 1.2 `git worktree add ../specfact-cli-worktrees/feature/module-migration-06-core-decoupling-cleanup -b feature/module-migration-06-core-decoupling-cleanup origin/dev`
- [ ] 1.3 `cd ../specfact-cli-worktrees/feature/module-migration-06-core-decoupling-cleanup`
- [ ] 1.4 `hatch env create`

## 2. Spec and tests first (TDD required)

- [ ] 2.1 Add/update spec delta under `specs/core-decoupling-cleanup/spec.md` for ownership boundary and migration acceptance criteria.
- [ ] 2.2 Add failing tests that detect residual non-core coupling (imports/usage paths from core into bundle-only components).
- [ ] 2.3 Record failing evidence in `TDD_EVIDENCE.md`.

## 3. Decoupling implementation

- [ ] 3.1 Produce inventory/classification table for candidate core components (keep/move/interface).
- [ ] 3.2 Move/refactor components classified as non-core out of `specfact-cli` core (or replace with interface contracts).
- [ ] 3.3 Update dependent imports in core and tests.
- [ ] 3.4 Re-run tests and record passing evidence in `TDD_EVIDENCE.md`.

## 4. Quality gates

- [ ] 4.1 `hatch run format`
- [ ] 4.2 `hatch run type-check`
- [ ] 4.3 `hatch run lint`
- [ ] 4.4 `hatch run contract-test`
- [ ] 4.5 `hatch run smart-test`

## 5. Documentation and closure

- [ ] 5.1 Update docs/architecture boundary notes for core vs modules-repo ownership.
- [ ] 5.2 Update `openspec/CHANGE_ORDER.md` status/dependencies if scope changes.
- [ ] 5.3 Create PR to `dev` with migration evidence and compatibility notes.
