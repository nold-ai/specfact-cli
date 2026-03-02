# bundle-test-parity Specification (Delta)

## Purpose

Defines the requirement that working on bundle code in **specfact-cli-modules** has the same quality standards and test scripts as in **specfact-cli**. This spec delta closes the gap left by migration-02: source was moved to bundles but tests and quality tooling were not migrated.

## ADDED Requirements

### Requirement: Tests for bundle code live in specfact-cli-modules

All tests that exercise the 17 migrated modules (or their bundle namespaces) SHALL be inventoried in specfact-cli and SHALL be present in specfact-cli-modules so that they run against the canonical bundle source in `packages/*/src/`.

#### Scenario: Test inventory exists and maps tests to bundles

- **GIVEN** the 17 migrated modules and their bundle mapping (specfact-project, specfact-backlog, specfact-codebase, specfact-spec, specfact-govern)
- **WHEN** test migration is complete
- **THEN** an inventory document SHALL exist (e.g. `TEST_INVENTORY.md`) listing: specfact-cli test file path, bundle(s) exercised, and target path in specfact-cli-modules
- **AND** unit, integration, and (where applicable) e2e tests that touch bundle behavior SHALL be copied or migrated into specfact-cli-modules with imports and paths adjusted for bundle namespaces

#### Scenario: Tests run and pass in specfact-cli-modules

- **GIVEN** the migrated tests in specfact-cli-modules
- **WHEN** `hatch test` (or equivalent) is run from the specfact-cli-modules repo root
- **THEN** all migrated tests SHALL run with PYTHONPATH (or install) exposing `packages/*/src`
- **AND** tests SHALL pass; any intentionally skipped tests SHALL be documented with reason

### Requirement: Quality tooling parity

specfact-cli-modules SHALL provide the same quality gates as specfact-cli for bundle development: format, type-check, lint, test, coverage threshold, and (where feasible) contract-test and smart-test (or equivalent).

#### Scenario: Same quality scripts available

- **GIVEN** a developer working in specfact-cli-modules on bundle code
- **WHEN** they run the pre-commit checklist
- **THEN** `hatch run format`, `hatch run type-check`, `hatch run lint`, `hatch run test` SHALL be available and SHALL use config aligned with specfact-cli (ruff, basedpyright, pylint, pytest)
- **AND** coverage config SHALL be present with a defined threshold (e.g. 80%); contract-test and smart-test (or equivalent incremental/contract validation) SHALL be added or documented
- **AND** yaml-lint (or equivalent) SHALL validate `packages/*/module-package.yaml` and `registry/index.json`

#### Scenario: CI runs the same gates

- **GIVEN** the specfact-cli-modules repository
- **WHEN** CI runs on push/PR
- **THEN** workflows SHALL run format, type-check, lint, test (and contract-test, coverage threshold where applicable)
- **AND** Python version(s) SHALL match specfact-cli (e.g. 3.11, 3.12, 3.13) if a matrix is used

## References

- Proposal section: "Test migration and quality parity (gap)"
- Tasks: Section 18 (18.1–18.5) in `tasks.md`
