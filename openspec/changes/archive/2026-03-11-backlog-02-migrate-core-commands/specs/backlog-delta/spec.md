# backlog-delta Specification

## ADDED Requirements

### Requirement: Restore backlog delta subcommands

The system SHALL provide `specfact backlog delta` with subcommands for backlog change analysis.

#### Scenario: Delta status shows backlog changes
- **WHEN** the user runs `specfact backlog delta status --project-id <id>`
- **THEN** current backlog state is compared to baseline
- **AND** added/updated/deleted items are listed

#### Scenario: Delta impact analyzes item effects
- **WHEN** the user runs `specfact backlog delta impact <item-id>`
- **THEN** dependent items and cascade effects are identified

#### Scenario: Delta cost-estimate calculates effort
- **WHEN** the user runs `specfact backlog delta cost-estimate`
- **THEN** story points and business value deltas are aggregated

#### Scenario: Delta rollback-analysis shows revert options
- **WHEN** the user runs `specfact backlog delta rollback-analysis`
- **THEN** safe rollback paths and risks are presented
