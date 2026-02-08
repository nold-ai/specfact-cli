# Spec: Module Packages

## ADDED Requirements

### Requirement: Module package manifests declare service bridges

The system SHALL allow `module-package.yaml` to declare `service_bridges` metadata for converter registration.

#### Scenario: Manifest includes service bridge declaration

- **WHEN** a module manifest includes `service_bridges`
- **THEN** each bridge entry SHALL include `id` and `converter_class`
- **AND** optional metadata such as `description` MAY be provided.

#### Scenario: Manifest without service bridges remains valid

- **WHEN** a legacy module manifest omits `service_bridges`
- **THEN** manifest validation SHALL still pass
- **AND** module lifecycle SHALL treat the module as having no bridge declarations.

### Requirement: Service bridge metadata is validated during manifest parsing

The system SHALL validate service bridge metadata structure before module registration.

#### Scenario: Invalid bridge metadata is rejected for registration

- **WHEN** a bridge entry is missing required keys or has malformed converter path
- **THEN** parser validation SHALL flag the declaration as invalid
- **AND** module registration SHALL skip only invalid bridge declarations.

#### Scenario: Valid bridge metadata is preserved in package model

- **WHEN** a manifest contains valid bridge declarations
- **THEN** the parsed `ModulePackageMetadata` SHALL expose those declarations for lifecycle registration.
