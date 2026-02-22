# module-lifecycle-management Delta Specification

## ADDED Requirements

### Requirement: Registration loads and validates schema extensions

The system SHALL extend module registration to load schema_extensions from manifests, validate namespace uniqueness, and populate the global extension registry.

#### Scenario: Registration loads schema_extensions from manifest
- **WHEN** module registration loads module-package.yaml
- **THEN** system SHALL parse schema_extensions section if present
- **AND** SHALL extract target models, field names, types, descriptions

#### Scenario: Registration validates extension namespace uniqueness
- **WHEN** module declares schema extension with field name
- **THEN** system SHALL check global extension registry for conflicts
- **AND** SHALL reject registration if `module.field` already declared by another module
- **AND** SHALL log error with conflicting module name

#### Scenario: Registration populates global extension registry
- **WHEN** module registration succeeds with schema_extensions
- **THEN** system SHALL add extensions to global registry
- **AND** registry SHALL map module_name → extensions metadata

#### Scenario: Registration logs registered extensions
- **WHEN** module with schema_extensions completes registration
- **THEN** system SHALL log: "Module X registered N schema extensions for [Feature, ProjectBundle]"
- **AND** SHALL log at debug level the specific fields registered

#### Scenario: Registration skips invalid extension declarations
- **WHEN** module declares extension with malformed field name (e.g., contains dots)
- **THEN** system SHALL log warning
- **AND** SHALL skip that extension
- **AND** SHALL NOT fail entire module registration
