# Capability: core-cli-reference

Dedicated reference pages for each core CLI command (init, module, upgrade).

## ADDED Requirements

### Requirement: Core CLI reference pages exist

The system SHALL provide dedicated reference pages for core CLI commands.

#### Scenario: Init reference page documents all subcommands and options

- **GIVEN** the docs/core-cli/init.md page exists
- **WHEN** a user reads the page
- **THEN** it documents: specfact init, init --profile, init --install, init ide, init --install-deps
- **AND** all documented commands match the actual --help output

#### Scenario: Module reference page documents all subcommands

- **GIVEN** the docs/core-cli/module.md page exists
- **WHEN** a user reads the page
- **THEN** it documents: module install, module uninstall, module list, module show, module search, module upgrade, module alias, module add-registry, module list-registries, module remove-registry, module enable, module disable
- **AND** all documented commands match the actual --help output

#### Scenario: Upgrade reference page documents the command

- **GIVEN** the docs/core-cli/upgrade.md page exists
- **WHEN** a user reads the page
- **THEN** it documents the specfact upgrade command and its options
