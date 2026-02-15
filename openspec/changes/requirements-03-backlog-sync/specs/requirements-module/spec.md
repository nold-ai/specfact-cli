## MODIFIED Requirements

### Requirement: Requirements Module
The requirements module SHALL include sync workflows backed by the sync kernel.

#### Scenario: Sync command uses shared session model
- **GIVEN** requirements sync starts
- **WHEN** session is created
- **THEN** sync output includes session ID and status
- **AND** unresolved conflicts can be resumed later.

#### Scenario: Sync command supports apply mode explicitly
- **GIVEN** preview output is accepted
- **WHEN** apply mode is requested
- **THEN** patch operations are executed with write guards
- **AND** resulting state is persisted for traceability.
