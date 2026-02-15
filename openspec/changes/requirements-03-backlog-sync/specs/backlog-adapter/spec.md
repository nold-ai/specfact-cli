## MODIFIED Requirements

### Requirement: Backlog Adapter
The backlog adapter SHALL support requirement-aware pull and push sync operations.

#### Scenario: Pull sync maps backlog changes to requirements updates
- **GIVEN** backlog item acceptance criteria changed since last sync
- **WHEN** requirements sync pull runs
- **THEN** corresponding requirement artifact is updated in preview patch
- **AND** changed fields are listed in sync output.

#### Scenario: Push sync updates backlog fields from requirements
- **GIVEN** requirement has updated business value fields
- **WHEN** push sync apply runs
- **THEN** mapped backlog fields are updated through adapter write APIs
- **AND** optimistic concurrency checks prevent stale overwrites.
