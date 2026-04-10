# dependency-decoupling Specification

## Purpose

TBD - created by archiving change module-migration-02-bundle-extraction. Update Purpose after archive.

## Requirements

### Requirement: No hardcoded imports of module-only specfact_cli code

Bundles in specfact-cli-modules SHALL NOT import from `specfact_cli.*` submodules that are used exclusively by bundle code. Such code SHALL be migrated to the appropriate bundle or a shared package in specfact-cli-modules.

#### Scenario: CORE imports are allowed

- **GIVEN** an import categorized as **CORE** (common, contracts, cli, registry, modes, runtime, telemetry, versioning, shared models)
- **WHEN** bundle code imports from that submodule
- **THEN** the import is allowed (bundles depend on specfact-cli as a pip package)
- **AND** the dependency is declared in the bundle's `pyproject.toml` or `module-package.yaml`

#### Scenario: MIGRATE imports are eliminated

- **GIVEN** an import categorized as **MIGRATE** (analyzers, backlog, comparators, enrichers, generators, importers, migrations, parsers, sync, validators, bundle-specific utils)
- **WHEN** dependency decoupling is complete
- **THEN** the source for that submodule SHALL be present in specfact-cli-modules (in the target bundle or shared package)
- **AND** bundle code SHALL import from the local path (e.g. `specfact_codebase.analyzers`) not `specfact_cli.analyzers`
- **AND** a lint/gate SHALL fail if new MIGRATE-tier imports are introduced

#### Scenario: Import gate enforced

- **GIVEN** the specfact-cli-modules repository
- **WHEN** CI or pre-commit runs
- **THEN** a check SHALL run that scans bundle code for `from specfact_cli.* import`
- **AND** the check SHALL fail if any import is not in the allowed (CORE) list
- **AND** `ALLOWED_IMPORTS.md` (or equivalent) SHALL document the allowed set
