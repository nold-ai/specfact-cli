# Tasks: module-migration-07-test-migration-cleanup

## 1. Scope and baseline

- [x] 1.1 Capture baseline from latest `hatch run smart-test-full` failure log
- [x] 1.2 Classify failures: import-path migration, command topology migration, signing/script fixture issues, unrelated
- [x] 1.3 Exclude unrelated failures not caused by module migration topology

## 2. Spec and tests first

- [x] 2.1 Add spec delta for test migration cleanup behavior and acceptance criteria
- [x] 2.2 Add/update focused tests for each migration bucket; run and record failing evidence in `TDD_EVIDENCE.md`

## 3. Implementation

- [x] 3.1 Replace legacy removed import paths in tests with supported interfaces
- [x] 3.2 Update E2E/integration tests to grouped command topology
- [x] 3.3 Harden signing/script fixtures with deterministic test assets
- [x] 3.4 Re-run targeted tests and capture passing evidence
- [x] 3.5 Re-home extracted-module E2E/integration tests from `specfact-cli` to `specfact-cli-modules`
- [x] 3.6 Retire or rewrite obsolete flat-topology tests that no longer map to supported runtime commands

## 4. Quality gates

- [x] 4.1 `hatch run format`
- [x] 4.2 `hatch run type-check`
- [x] 4.3 `hatch run lint`
- [x] 4.4 `hatch run contract-test`
- [x] 4.5 `hatch run smart-test`
- [x] 4.6 `hatch run smart-test-full` in `specfact-cli` (core-only migration verification pass)
- [x] 4.7 full modules test run in `specfact-cli-modules` (`hatch run test -q`) (module test ownership verification pass)

## 5. Closure

- [ ] 5.1 Update CHANGELOG migration notes if test command expectations changed
- [x] 5.2 Open coordinated PRs to `dev` in both repos and link migration-03/-04/-05 dependencies
