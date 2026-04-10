# module-development-guide Specification

A single, discoverable guide explains how to develop and package new modules so that contributors can extend the CLI consistently.

## ADDED Requirements

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
