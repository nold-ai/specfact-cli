## ADDED Requirements

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
