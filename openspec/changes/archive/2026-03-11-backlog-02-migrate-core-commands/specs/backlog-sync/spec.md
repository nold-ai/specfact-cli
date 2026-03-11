# backlog-sync Specification

## ADDED Requirements

### Requirement: Restore backlog sync command functionality

The system SHALL provide `specfact backlog sync` command for bidirectional backlog synchronization.

#### Scenario: Sync from OpenSpec to backlog
- **WHEN** the user runs `specfact backlog sync --adapter github --project-id <repo>`
- **THEN** OpenSpec changes are exported to GitHub issues/ADO work items
- **AND** state mapping preserves status semantics

#### Scenario: Bidirectional sync with cross-adapter
- **WHEN** the user runs sync with cross-adapter configuration
- **THEN** state is mapped between adapters using canonical status
- **AND** lossless round-trip preserves content

#### Scenario: Sync with bundle integration
- **WHEN** sync is run within an OpenSpec bundle context
- **THEN** synced items update bundle state and source tracking

#### Scenario: Ceremony alias works
- **WHEN** the user runs `specfact backlog ceremony sync`
- **THEN** the command forwards to `specfact backlog sync`
