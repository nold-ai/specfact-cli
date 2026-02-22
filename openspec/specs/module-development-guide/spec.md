# module-development-guide Specification

## Purpose
TBD - created by archiving change arch-08-documentation-discrepancies-remediation. Update Purpose after archive.
## Requirements
### Requirement: Required module structure documented

The module development guide SHALL describe the required directory structure (e.g. modules/<name>/, module-package.yaml, src/<name>/__init__.py, main.py, commands) and file roles.

#### Scenario: Developer creates new module
- **GIVEN** the module development guide
- **WHEN** a developer creates a new module
- **THEN** the guide describes the required directory structure
- **AND** file roles are explained

### Requirement: Manifest and contract requirements documented

The module development guide SHALL document the module-package.yaml schema (name, version, commands, dependencies, schema_extensions, service_bridges) and SHALL mention contract requirements (@icontract, @beartype) for public APIs.

#### Scenario: Developer configures module
- **GIVEN** the module development guide
- **WHEN** a developer configures a module
- **THEN** the guide documents the module-package.yaml schema
- **AND** contract requirements for public APIs are mentioned

### Requirement: Module guide discoverable

The module development guide SHALL be reachable from the docs navigation (e.g. Guides or Reference) and from the architecture or module system documentation.

#### Scenario: User looks for module development
- **GIVEN** the published docs (e.g. docs.specfact.io)
- **WHEN** a user looks for how to develop modules
- **THEN** the guide is reachable from the docs navigation
- **AND** from the architecture or module system documentation

