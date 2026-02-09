# Spec: Module Packages

## ADDED Requirements

### Requirement: Module package manifest SHALL support publisher and integrity metadata

The system SHALL support structured publisher and integrity metadata in `module-package.yaml`.

#### Scenario: Manifest includes publisher identity

- **WHEN** manifest includes `publisher` metadata
- **THEN** parser SHALL capture `name`, `email`, and optional publisher attributes
- **AND** parsed metadata SHALL be available to trust-validation workflows.

#### Scenario: Manifest includes integrity metadata

- **WHEN** manifest includes `integrity` metadata
- **THEN** parser SHALL capture checksum and optional signature fields
- **AND** validation SHALL ensure checksum format correctness.

### Requirement: Manifest dependencies SHALL support versioned entries

The system SHALL support versioned dependency declarations for both module and pip dependencies.

#### Scenario: Versioned module dependency parsed

- **WHEN** manifest declares module dependency with name and version specifier
- **THEN** parser SHALL store both values in typed metadata
- **AND** version specifier SHALL be validated as a supported constraint format.

#### Scenario: Versioned pip dependency parsed

- **WHEN** manifest declares pip dependency with name and version specifier
- **THEN** parser SHALL preserve versioned dependency for installation-time resolution
- **AND** legacy list formats SHALL remain backward compatible when possible.
