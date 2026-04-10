# test-suite-stabilization Specification

## Purpose

TBD - created by archiving change module-migration-08-release-suite-stabilization. Update Purpose after archive.

## Requirements

### Requirement: Post-Migration Release Suite Stability

The `specfact-cli` repository SHALL keep only tests that match the lean-core runtime and supported grouped command surface after module migration.

#### Scenario: Core tests use supported grouped command topology

- **GIVEN** core tests that invoke command paths owned by `specfact-cli`
- **WHEN** the release suite is stabilized
- **THEN** those tests use the supported grouped command surface and do not rely on removed flat commands.

#### Scenario: Extracted bundle path assumptions are not required in core tests

- **GIVEN** tests in `specfact-cli` that reference removed in-repo bundle files or namespaces
- **WHEN** release-suite stabilization is complete
- **THEN** those tests are removed, rewritten, or redirected to supported core interfaces rather than failing on missing extracted paths.

#### Scenario: Genuine core regressions remain fixed

- **GIVEN** the lean-core runtime after module extraction
- **WHEN** grouped command mounting, `init` bundle installation, or shared fixtures regress
- **THEN** the underlying core behavior is fixed so retained tests pass without reintroducing removed bundle behavior into core.

#### Scenario: Deterministic release validation is possible in CI

- **GIVEN** the release branch validation suites run in non-interactive CI
- **WHEN** signing and installer-related tests execute
- **THEN** they use deterministic local fixtures and fail only on real behavior defects rather than environment-coupled artifacts.
