## ADDED Requirements

### Requirement: Solution Architecture
The system SHALL provide architecture derive, coverage validation, and trace outputs linked to requirements.

#### Scenario: Derive architecture from requirements
- **GIVEN** `specfact architecture derive --requirements .specfact/requirements/ --interactive`
- **WHEN** derive completes
- **THEN** an `.arch.yaml` artifact is created
- **AND** components and ADR entries reference requirement rules.

#### Scenario: Validate architecture coverage
- **GIVEN** requirements and architecture artifacts exist
- **WHEN** `specfact architecture validate-coverage` runs
- **THEN** unmapped business rules are reported
- **AND** missing ADRs for architectural constraints are reported.

#### Scenario: Trace command exports architecture linkage
- **GIVEN** architecture and requirements data
- **WHEN** `specfact architecture trace --format json` runs
- **THEN** output includes requirement-to-component-to-ADR mappings
- **AND** output is consumable by full-chain validation.
