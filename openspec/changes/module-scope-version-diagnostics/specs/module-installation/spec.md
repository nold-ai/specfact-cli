## MODIFIED Requirements

### Requirement: Module install enforces versioned bundle dependencies

The system SHALL validate versioned bundle dependency declarations during module installation.

#### Scenario: Existing dependency version is too old

- **GIVEN** a module being installed declares a bundle dependency with a version range
- **AND** that dependency already exists in the target install root with a version outside the range
- **WHEN** the user installs the dependent module
- **THEN** install fails before accepting the dependency set
- **AND** the error identifies the dependency id, required version range, and installed version

#### Scenario: Newly installed dependency version is validated

- **GIVEN** a module being installed declares a missing bundle dependency with a version range
- **WHEN** dependency installation completes
- **THEN** the installed dependency version is validated against the declared range
- **AND** install fails if the installed dependency still does not satisfy the range
