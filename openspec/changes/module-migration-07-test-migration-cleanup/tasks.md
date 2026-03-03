# Tasks: module-migration-07-test-migration-cleanup

## 1. Scope and baseline

- [ ] 1.1 Capture baseline from latest `hatch run smart-test-full` failure log
- [ ] 1.2 Classify failures: import-path migration, command topology migration, signing/script fixture issues, unrelated
- [ ] 1.3 Exclude unrelated failures not caused by module migration topology

## 2. Spec and tests first

- [ ] 2.1 Add spec delta for test migration cleanup behavior and acceptance criteria
- [ ] 2.2 Add/update focused tests for each migration bucket; run and record failing evidence in `TDD_EVIDENCE.md`

## 3. Implementation

- [ ] 3.1 Replace legacy removed import paths in tests with supported interfaces
- [ ] 3.2 Update E2E/integration tests to grouped command topology
- [ ] 3.3 Harden signing/script fixtures with deterministic test assets
- [ ] 3.4 Re-run targeted tests and capture passing evidence

## 4. Quality gates

- [ ] 4.1 `hatch run format`
- [ ] 4.2 `hatch run type-check`
- [ ] 4.3 `hatch run lint`
- [ ] 4.4 `hatch run contract-test`
- [ ] 4.5 `hatch run smart-test`
- [ ] 4.6 `hatch run smart-test-full` (migration cleanup verification pass)

## 5. Closure

- [ ] 5.1 Update CHANGELOG migration notes if test command expectations changed
- [ ] 5.2 Open PR to `dev` and link migration-03/-04/-05 dependencies
