# module-development-guide Specification

## Purpose

TBD - created by archiving change arch-08-documentation-discrepancies-remediation. Update Purpose after archive.

## Requirements

### Requirement: Required module structure documented

The module development guide SHALL describe the required directory structure (e.g. modules/<name>/, module-package.yaml, src/<name>/__init__.py, main.py, commands) and file roles.

#### Scenario: Developer creates new module

- __GIVEN__ the module development guide
- __WHEN__ a developer creates a new module
- __THEN__ the guide describes the required directory structure
- __AND__ file roles are explained

### Requirement: Manifest and contract requirements documented

The module development guide SHALL document the module-package.yaml schema (name, version, commands, dependencies, schema_extensions, service_bridges) and SHALL mention contract requirements (@icontract, @beartype) for public APIs.

#### Scenario: Developer configures module

- __GIVEN__ the module development guide
- __WHEN__ a developer configures a module
- __THEN__ the guide documents the module-package.yaml schema
- __AND__ contract requirements for public APIs are mentioned

### Requirement: Module guide discoverable

The module development guide SHALL be reachable from the docs navigation (e.g. Guides or Reference) and from the architecture or module system documentation.

#### Scenario: User looks for module development

- __GIVEN__ the published docs (e.g. docs.specfact.io)
- __WHEN__ a user looks for how to develop modules
- __THEN__ the guide is reachable from the docs navigation
- __AND__ from the architecture or module system documentation

### Requirement: Module development docs reflect the dedicated modules repository model

The module development guide SHALL describe that official bundle implementation lives in `specfact-cli-modules`, while `specfact-cli` owns the lean runtime, registry, marketplace lifecycle, and shared contracts needed by installed bundles.

#### Scenario: Developer reads module development docs after modularization

- __WHEN__ a contributor reads the module development guide
- __THEN__ the guide explains the current two-repository model
- __AND__ it identifies which code and documentation concerns belong in `specfact-cli` versus `specfact-cli-modules`

### Requirement: Directory and dependency docs reflect bundle boundaries

Module development, directory-structure, and dependency documentation SHALL describe the current bundle/package layout, canonical repository ownership, and bundle dependency relationships introduced by marketplace-installed official bundles.

#### Scenario: Contributor checks structure and dependency guidance

- __WHEN__ a contributor reads directory or dependency documentation related to modules
- __THEN__ the docs show the current bundle/package boundaries and repository ownership
- __AND__ dependency explanations match the marketplace-installed bundle model rather than the former in-repo bundled module layout
