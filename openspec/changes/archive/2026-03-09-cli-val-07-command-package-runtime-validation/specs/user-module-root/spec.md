## ADDED Requirements

### Requirement: Canonical User Root Discovery Is Silent During Normal Startup

The system SHALL treat `<user-home>/.specfact/modules` as the canonical default user module root and SHALL not emit duplicate or shadow warnings when that root is being used normally.

#### Scenario: Running from user home does not warn about canonical user modules

- **GIVEN** the current working directory is `<user-home>`
- **AND** `<user-home>/.specfact/modules/<module-id>` contains installed modules
- **WHEN** module discovery runs during normal command startup
- **THEN** the module is discovered exactly once
- **AND** normal stdout/stderr contains no duplicate-module or shadow warning for that canonical user root
- **AND** command availability remains unchanged.

#### Scenario: Equivalent canonical-path observations are deduplicated silently

- **GIVEN** module discovery encounters the same canonical user module root through equivalent resolved paths
- **WHEN** discovery normalizes and prioritizes module roots
- **THEN** the equivalent observations are deduplicated silently
- **AND** no user-facing warning is emitted for the canonical default path.
