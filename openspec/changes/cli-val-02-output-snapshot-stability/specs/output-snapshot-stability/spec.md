## ADDED Requirements

### Requirement: Help Text Snapshots

The system SHALL maintain snapshot tests for all command `--help` outputs to detect unintentional changes.

#### Scenario: Help text snapshot matches for top-level command

- **GIVEN** the SpecFact CLI is installed
- **WHEN** `specfact --help` is invoked via CliRunner
- **THEN** the output matches the stored snapshot exactly
- **AND** any difference causes the test to fail.

#### Scenario: Help text snapshot matches for subcommands

- **GIVEN** the SpecFact CLI is installed
- **WHEN** each registered subcommand `--help` is invoked via CliRunner
- **THEN** each output matches its respective stored snapshot
- **AND** new commands automatically require a snapshot to be created.

### Requirement: Structured Output Snapshots

The system SHALL maintain snapshot tests for commands that produce machine-readable output (JSON/YAML).

#### Scenario: JSON output shape matches snapshot

- **GIVEN** a command that produces structured JSON output
- **WHEN** the command is invoked with a deterministic input
- **THEN** the JSON output structure matches the stored snapshot
- **AND** dynamic values (timestamps, absolute paths) are normalized before comparison.

### Requirement: Error Message Snapshots

The system SHALL maintain snapshot tests for key error message templates.

#### Scenario: Error messages for common failure modes are stable

- **GIVEN** a command invoked with a known-invalid input
- **WHEN** the command produces an error message
- **THEN** the error message matches the stored snapshot
- **AND** changes to error wording require explicit snapshot update.

### Requirement: Snapshot Update Workflow

The system SHALL provide an explicit workflow for updating snapshots that prevents accidental drift.

#### Scenario: Snapshot update requires explicit flag

- **GIVEN** a test run with snapshot mismatches
- **WHEN** tests are run without `--snapshot-update` flag
- **THEN** mismatching tests fail
- **AND** no snapshots are overwritten silently.

#### Scenario: Snapshot update with explicit flag succeeds

- **GIVEN** a test run with intentional output changes
- **WHEN** tests are run with `--snapshot-update` flag
- **THEN** snapshots are updated to match new output
- **AND** updated snapshot files appear in git diff for review.
