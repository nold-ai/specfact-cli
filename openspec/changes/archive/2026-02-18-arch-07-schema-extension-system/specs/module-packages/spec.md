# module-packages Delta Specification

## ADDED Requirements

### Requirement: Module manifest declares schema extensions

The system SHALL extend `ModulePackageMetadata` to include optional `schema_extensions` field declaring fields the module adds to core models.

#### Scenario: Manifest schema includes schema_extensions

- **WHEN** module-package.yaml is parsed
- **THEN** it MAY include `schema_extensions` array
- **AND** each entry SHALL specify: target model name, field definitions with type/description

#### Scenario: Schema extension for Feature model

- **WHEN** module declares schema_extensions for Feature
- **THEN** manifest SHALL list fields being added
- **AND** each field SHALL include type hint and description
- **AND** module namespace is implicit from module name

#### Scenario: Schema extension for ProjectBundle model

- **WHEN** module declares schema_extensions for ProjectBundle
- **THEN** manifest SHALL list fields being added
- **AND** each field SHALL include type hint and description

#### Scenario: Module without schema_extensions remains valid

- **WHEN** module-package.yaml omits schema_extensions
- **THEN** module SHALL load successfully
- **AND** no extensions registered for that module
