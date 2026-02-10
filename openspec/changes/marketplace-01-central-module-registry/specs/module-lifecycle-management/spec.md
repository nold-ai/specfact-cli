# module-lifecycle-management Delta Specification

## ADDED Requirements

### Requirement: Registration handles modules from multiple sources

The system SHALL extend registration to handle modules from built-in, marketplace, and custom sources with appropriate lifecycle rules.

#### Scenario: Marketplace modules can be uninstalled
- **WHEN** module from marketplace is registered
- **THEN** system SHALL mark it as uninstallable
- **AND** SHALL allow removal via uninstall command

#### Scenario: Built-in modules cannot be uninstalled
- **WHEN** module from built-in source is registered
- **THEN** system SHALL mark it as non-uninstallable
- **AND** SHALL prevent removal via uninstall command

#### Scenario: Registration validates namespace for marketplace modules
- **WHEN** marketplace module is registered
- **THEN** system SHALL validate id uses "namespace/name" format
- **AND** SHALL log warning if flat name used
