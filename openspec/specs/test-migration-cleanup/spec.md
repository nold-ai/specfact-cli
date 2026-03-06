# test-migration-cleanup Specification

## Purpose
TBD - created by archiving change module-migration-07-test-migration-cleanup. Update Purpose after archive.
## Requirements
### Requirement: Post-Migration Test Topology Alignment

The test suite SHALL align with the category-group command topology and removed in-core module paths after module migration.

#### Scenario: Legacy flat command assumptions are removed from tests

- **GIVEN** tests that invoke removed flat commands
- **WHEN** migration cleanup is complete
- **THEN** tests use grouped command forms and pass under current CLI topology.

#### Scenario: Removed in-core module import paths are not referenced

- **GIVEN** tests that import from removed `specfact_cli.modules.*` paths
- **WHEN** migration cleanup is complete
- **THEN** tests import supported interfaces and no longer fail due to missing module paths.

#### Scenario: Signing/script fixtures are deterministic in CI

- **GIVEN** tests that validate signing and publishing scripts
- **WHEN** fixtures are executed in non-interactive CI environments
- **THEN** tests use deterministic local test assets and do not fail due to malformed or missing external key material.

#### Scenario: Extracted module behavior tests live in modules repository

- **GIVEN** E2E/integration tests that validate extracted bundle behavior (`project`, `backlog`, `codebase`, `spec`, `govern`)
- **WHEN** migration cleanup is complete
- **THEN** those tests are owned and executed in `specfact-cli-modules` rather than `specfact-cli`.

#### Scenario: Core repository keeps only core runtime test ownership

- **GIVEN** `specfact-cli` as slim core runtime
- **WHEN** migration cleanup is complete
- **THEN** `specfact-cli` test scope is limited to core bootstrap/module lifecycle/compatibility behaviors and no longer carries extracted bundle behavior suites.

#### Scenario: Obsolete flat command assertions are retired

- **GIVEN** tests that assert removed flat command topology as active behavior
- **WHEN** no supported runtime path exists for that assertion
- **THEN** those tests are removed or replaced with assertions against the supported grouped/runtime command surface.

