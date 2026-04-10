## ADDED Requirements

### Requirement: Core commands SHALL classify project artifact writes by ownership and mutation mode

The system SHALL require core init/setup flows to declare whether a target artifact is create-only, mergeable, append-managed, or explicit-replace before writing into a user repository.

#### Scenario: Partial-ownership artifact cannot use implicit full replacement

- **WHEN** a core command targets a user-project artifact that SpecFact owns only partially
- **THEN** the command SHALL use a partial-ownership write mode such as structured merge or managed-block append
- **AND** SHALL NOT replace the full file implicitly

#### Scenario: Unowned existing artifact fails safe

- **WHEN** a core command would modify an existing artifact with no declared SpecFact-owned section or full-file ownership
- **THEN** the command SHALL stop with an actionable conflict message
- **AND** SHALL NOT mutate the artifact unless an explicit replacement mode is requested

### Requirement: Lossy project artifact mutations SHALL create recovery material

The system SHALL create backup and recovery metadata for any lossy local artifact mutation initiated by a core command.

#### Scenario: Explicit replacement emits backup path

- **WHEN** a core command performs an explicit replace of an existing project artifact
- **THEN** a backup copy SHALL be created in a SpecFact-managed recovery location before replacement
- **AND** the command output SHALL identify the backup path and original target

#### Scenario: Failed structured merge leaves original file untouched

- **WHEN** structured reconciliation cannot be completed safely
- **THEN** the original project artifact SHALL remain unchanged
- **AND** the command SHALL report why reconciliation failed and how to proceed safely

### Requirement: CI SHALL detect unsafe core writes to user-project artifacts

The repository SHALL enforce a CI or quality gate that flags unsafe write paths for user-project artifacts touched by core init/setup flows.

#### Scenario: Raw overwrite path is rejected in CI

- **WHEN** a core init/setup code path writes a protected user-project artifact without using the sanctioned safe-write helper
- **THEN** the quality gate SHALL fail
- **AND** the failure output SHALL identify the offending path or call site

#### Scenario: Regression fixture preserves unrelated user configuration

- **WHEN** CI runs regression fixtures for existing user-owned project configs
- **THEN** init/setup commands SHALL preserve unrelated user-managed content
- **AND** only declared SpecFact-managed sections or keys may change
