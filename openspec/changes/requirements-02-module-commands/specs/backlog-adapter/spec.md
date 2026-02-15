## MODIFIED Requirements

### Requirement: Backlog Adapter
The system SHALL expose backlog acceptance-criteria content to requirements extraction workflows.

#### Scenario: Adapter returns acceptance criteria payload for extraction
- **GIVEN** a backlog item selected for extraction
- **WHEN** requirements extraction requests source fields
- **THEN** adapter returns title, description, acceptance-criteria text, and item identity
- **AND** extraction proceeds without provider-specific parsing in command handlers.

#### Scenario: Missing acceptance criteria is surfaced explicitly
- **GIVEN** a backlog item with no acceptance criteria
- **WHEN** extraction runs
- **THEN** item is reported as incomplete input
- **AND** command output includes the backlog item identifier.
