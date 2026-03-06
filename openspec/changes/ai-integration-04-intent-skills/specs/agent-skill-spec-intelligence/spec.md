## MODIFIED Requirements

### Requirement: Agent Skill Installation
The system SHALL provide `specfact ide skill install` with a `--type {spec,intent,all}` option to install skill files to the IDE-appropriate location (modified to support skill type selection).

#### Scenario: Spec skill install without --type flag (backwards compatible)
- **GIVEN** a project with an active AI IDE configuration
- **WHEN** the user runs `specfact ide skill install` without a `--type` flag
- **THEN** spec-validation skills (from ai-integration-01) are installed as before
- **AND** no breaking change occurs to the existing install flow

#### Scenario: Skill list enumerates all available skill types
- **GIVEN** both spec skills (ai-integration-01) and intent skills (ai-integration-04) are available
- **WHEN** the user runs `specfact ide skill list`
- **THEN** both `spec` and `intent` skill types are listed with their descriptions
- **AND** each skill entry shows its installation status (installed / not installed)
