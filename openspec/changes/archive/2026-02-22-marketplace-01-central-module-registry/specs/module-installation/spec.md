# module-installation Specification

## Purpose

Defines CLI commands and infrastructure for installing, uninstalling, searching, listing, and upgrading modules from marketplace or custom sources.

## ADDED Requirements

### Requirement: Install command downloads and installs modules

The system SHALL provide `specfact module install <module-id>` command that downloads, verifies, and installs modules from the registry.

#### Scenario: Install module from marketplace

- **WHEN** user runs `specfact module install specfact/backlog`
- **THEN** system SHALL fetch registry index
- **AND** SHALL download module tarball
- **AND** SHALL verify checksum
- **AND** SHALL extract to ~/.specfact/marketplace-modules/backlog/
- **AND** SHALL register module
- **AND** SHALL display success message

#### Scenario: Install specific version

- **WHEN** user runs `specfact module install specfact/backlog --version 0.29.0`
- **THEN** system SHALL install specified version
- **AND** SHALL verify core_compatibility with current CLI version

#### Scenario: Install module already installed

- **WHEN** user installs module that is already installed
- **THEN** system SHALL display message "Module already installed (version X)"
- **AND** SHALL suggest using upgrade command

### Requirement: Uninstall command removes marketplace modules

The system SHALL provide `specfact module uninstall <module-name>` command that removes modules from marketplace path.

#### Scenario: Uninstall marketplace module

- **WHEN** user runs `specfact module uninstall backlog`
- **THEN** system SHALL check if module is from marketplace
- **AND** SHALL remove ~/.specfact/marketplace-modules/backlog/ directory
- **AND** SHALL remove module from registry
- **AND** SHALL display success message

#### Scenario: Attempt to uninstall built-in module

- **WHEN** user attempts to uninstall built-in module
- **THEN** system SHALL display error "Cannot uninstall built-in module"
- **AND** SHALL NOT modify module

### Requirement: Search command finds modules in registry

The system SHALL provide `specfact module search <query>` command that searches registry index by name, description, or tags.

#### Scenario: Search modules by keyword

- **WHEN** user runs `specfact module search backlog`
- **THEN** system SHALL fetch registry index
- **AND** SHALL filter modules matching query in name, description, or tags
- **AND** SHALL display results with module ID, description, latest version

### Requirement: List command shows installed modules

The system SHALL provide `specfact module list` command that displays modules from all sources with source indicators.

#### Scenario: List all modules

- **WHEN** user runs `specfact module list`
- **THEN** system SHALL show modules from built-in, marketplace, and custom paths
- **AND** SHALL indicate source (built-in/marketplace/custom) for each module

#### Scenario: List marketplace modules only

- **WHEN** user runs `specfact module list --source marketplace`
- **THEN** system SHALL show only marketplace-installed modules

### Requirement: Upgrade command updates installed modules

The system SHALL provide `specfact module upgrade <module-name>` command that upgrades marketplace modules to latest version.

#### Scenario: Upgrade marketplace module

- **WHEN** user runs `specfact module upgrade backlog`
- **THEN** system SHALL fetch registry index
- **AND** SHALL check if newer version available
- **AND** SHALL download and install newer version
- **AND** SHALL remove old version after successful install

#### Scenario: Upgrade reinstalls when module already exists

- **WHEN** user runs `specfact module upgrade backlog` and backlog is already installed
- **THEN** system SHALL replace existing installed files with the upgraded package
- **AND** SHALL NOT no-op due to existing install marker files

### Requirement: Installation extraction is path-safe

The system SHALL reject archive members that escape the intended extraction root.

#### Scenario: Installer blocks path traversal entries

- **WHEN** a downloaded marketplace tarball contains absolute paths or `..` traversal
- **THEN** install SHALL fail before extraction
- **AND** SHALL raise a validation error indicating unsafe archive content
