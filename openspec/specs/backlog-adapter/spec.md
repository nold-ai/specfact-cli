# backlog-adapter Specification

## Purpose
TBD - created by archiving change add-generic-backlog-abstraction. Update Purpose after archive.
## Requirements
### Requirement: BacklogAdapter Interface

The system SHALL provide a standard `BacklogAdapter` interface that all backlog sources (GitHub, ADO, JIRA, GitLab, etc.) must implement.

#### Scenario: Case-insensitive filter matching

- **GIVEN** filters for state or assignee
- **WHEN** an adapter applies those filters
- **THEN** comparisons are case-insensitive and whitespace-normalized
- **AND** the adapter does not drop items due to case differences.

#### Scenario: Adapter-specific assignee normalization

- **GIVEN** an ADO work item with `System.AssignedTo` values (displayName, uniqueName, or mail)
- **WHEN** a user filters by assignee
- **THEN** the adapter matches against any of those identity fields (case-insensitive).

- **GIVEN** a GitHub issue with assignee login
- **WHEN** a user filters by assignee with or without leading `@`
- **THEN** the adapter matches login and display name when available (case-insensitive) and falls back to login-only.

#### Scenario: Sprint disambiguation for ADO

- **GIVEN** multiple iteration paths that contain the same sprint name
- **WHEN** a user filters with a name-only `--sprint`
- **THEN** the adapter reports ambiguity and prompts for a full iteration path
- **AND** does not default to the earliest matching sprint.

#### Scenario: Default to current iteration for ADO when sprint omitted

- **GIVEN** an ADO adapter with org/project/team context
- **WHEN** `--sprint` is not provided
- **THEN** the adapter resolves the current active iteration via the team iterations API
- **AND** uses the `$timeframe=current` query for the team iterations endpoint
- **AND** uses that iteration path for filtering when available.
- **AND** the team is taken from `--ado-team` when provided, otherwise defaults to the project team name.
- **AND** the team iterations endpoint format follows `/{org}/{project}/{team}/_apis/work/teamsettings/iterations?$timeframe=current`.

### Requirement: Adapter Extensibility

The system SHALL enable new backlog adapters to be added with minimal code (<500 LOC) without modifying existing adapters or core logic.

#### Scenario: Add new adapter (JIRA example)

- **WHEN** a developer wants to add JIRA support
- **THEN** they create a new class inheriting from `BacklogAdapter`, implement required methods, and register it (~300 LOC)

#### Scenario: New adapter works with existing features

- **WHEN** a new adapter is added
- **THEN** template detection (Plan A) and bundle mapping (Plan C) work automatically with the new adapter

### Requirement: Backward Compatibility

The system SHALL maintain backward compatibility when refactoring existing adapters to use the new interface.

#### Scenario: GitHub adapter refactoring

- **WHEN** GitHub adapter is refactored to inherit from `BacklogAdapter`
- **THEN** all existing functionality remains unchanged, and existing tests continue to pass

#### Scenario: ADO adapter refactoring

- **WHEN** ADO adapter is refactored to inherit from `BacklogAdapter`
- **THEN** all existing functionality remains unchanged, and existing tests continue to pass

#### Scenario: Lossless round-trip after refactoring

- **WHEN** existing adapters are refactored
- **THEN** round-trip tests confirm zero data loss (GitHub issue → BacklogItem → GitHub issue)

