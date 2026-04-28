## ADDED Requirements

### Requirement: Enterprise Budget Routing

The system SHALL support enterprise routing metadata for budget-approval decisions while preserving the local gate contract.

#### Scenario: Enterprise approval route is attached to paused run

- **GIVEN** enterprise budget routing is configured and a run requires approval
- **WHEN** the budget gate pauses execution
- **THEN** the wait-state record includes the enterprise routing target and required approval tier
- **AND** the local resume-token workflow remains intact.

#### Scenario: Missing enterprise routing falls back deterministically

- **GIVEN** enterprise routing is configured but unavailable at decision time
- **WHEN** the gate evaluates the run
- **THEN** the configured fallback behavior is applied deterministically
- **AND** the event is recorded for audit.

### Requirement: Chargeback Reporting Contract

The system SHALL emit chargeback-ready summaries keyed on stable team or cost-center identifiers.

#### Scenario: Chargeback summary aggregates spend by team

- **WHEN** an enterprise chargeback report is generated
- **THEN** cost, tokens, outcomes, and approval counts are grouped by the configured stable team identifier
- **AND** the report can be serialized for downstream reporting systems.
