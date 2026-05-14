## ADDED Requirements

### Requirement: Module doctor reports effective and shadowed module copies

The system SHALL provide a `specfact module doctor` diagnostic that reports module origin, version, path, and shadowing state without importing module command code.

#### Scenario: Duplicate project and user module copies are visible

- **GIVEN** a module id exists in project scope and user scope with different versions
- **WHEN** the user runs `specfact module doctor <module-id>`
- **THEN** the output identifies the project copy as effective
- **AND** the output identifies the user copy as shadowed
- **AND** the output shows both versions and paths
- **AND** the output includes a recovery command for removing the stale user-scope copy

#### Scenario: Development source roots are disclosed

- **GIVEN** development source root environment variables are configured
- **WHEN** the user runs `specfact module doctor`
- **THEN** the output lists the configured development source roots that may influence import resolution
