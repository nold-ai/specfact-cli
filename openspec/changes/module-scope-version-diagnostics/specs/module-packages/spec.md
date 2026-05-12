## MODIFIED Requirements

### Requirement: Module registration enforces versioned module dependencies

The system SHALL skip registering an enabled module when its declared versioned module dependency is absent, disabled, or present at a version that does not satisfy the declared specifier.

#### Scenario: Enabled dependency version is too old

- **GIVEN** an enabled module declares a dependency on another module with a minimum version
- **AND** the dependency is enabled but its manifest version is below that minimum
- **WHEN** module package commands are registered
- **THEN** the dependent module is skipped
- **AND** diagnostics report the required version and the discovered version

#### Scenario: Dependency version satisfies the declared range

- **GIVEN** an enabled module declares a versioned module dependency
- **AND** the dependency is enabled and its version satisfies the declared range
- **WHEN** module package commands are registered
- **THEN** the dependent module remains eligible for registration
