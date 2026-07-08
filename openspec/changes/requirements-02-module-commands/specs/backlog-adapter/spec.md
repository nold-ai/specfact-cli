## MODIFIED Requirements

### Requirement: Backlog Adapter

The system SHALL define source-attributed backlog requirement snippets that
requirements runtime adapters can normalize without provider-specific parsing in
core command handlers.

#### Scenario: Adapter returns source fields for requirement context import

- **GIVEN** a backlog item selected for requirement context import
- **WHEN** the requirements adapter receives source fields
- **THEN** the adapter can return title, description, acceptance-criteria text, and item identity
- **AND** normalization proceeds without provider-specific parsing in core helpers.

#### Scenario: Missing acceptance criteria is surfaced explicitly

- **GIVEN** a backlog item with no acceptance criteria
- **WHEN** requirements context normalization runs
- **THEN** the item is reported as incomplete input
- **AND** diagnostics include the backlog item identifier.
