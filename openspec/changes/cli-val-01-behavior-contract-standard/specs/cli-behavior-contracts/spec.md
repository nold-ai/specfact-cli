## ADDED Requirements

### Requirement: CLI Behavior Contract Schema

The system SHALL provide a YAML schema that defines the structure for CLI behavior scenario files, enabling machine-readable declaration of expected command behavior.

#### Scenario: Schema validates a well-formed scenario file

- **GIVEN** a scenario YAML file with feature name, argv list, expect block (exit code, stdout/stderr patterns), and fs block (creates/modifies)
- **WHEN** the schema validator runs against the file
- **THEN** validation passes with no errors
- **AND** all required fields are present and correctly typed.

#### Scenario: Schema rejects a scenario file missing required fields

- **GIVEN** a scenario YAML file missing the `argv` field in a scenario entry
- **WHEN** the schema validator runs against the file
- **THEN** validation fails with a descriptive error identifying the missing field
- **AND** the error message includes the scenario name and line context.

#### Scenario: Schema supports both pattern and anti-pattern categorization

- **GIVEN** a scenario YAML file with entries categorized as `type: pattern` and `type: anti-pattern`
- **WHEN** the file is parsed
- **THEN** patterns and anti-patterns are distinguishable programmatically
- **AND** anti-patterns require `exit_nonzero: true` in the expect block.

### Requirement: Pilot Scenario Files

The system SHALL include pilot scenario files for at least three command groups demonstrating the contract format across different command characteristics.

#### Scenario: Pilot covers a command with many arguments

- **GIVEN** a scenario file for a command group with multiple required and optional arguments
- **WHEN** the file includes happy-path and misuse scenarios
- **THEN** at least 3 pattern scenarios and 3 anti-pattern scenarios are defined
- **AND** each scenario records exact argv, expected exit code, and output patterns.

#### Scenario: Pilot covers a command with file I/O

- **GIVEN** a scenario file for a command that reads or writes files
- **WHEN** the file includes filesystem expectation blocks
- **THEN** the `fs.creates` and `fs.modifies` fields list expected file paths
- **AND** anti-patterns assert `fs.creates: []` and `fs.modifies: []` (no side effects on failure).

#### Scenario: Pilot covers a simple informational command

- **GIVEN** a scenario file for a command like `--help` or `--version`
- **WHEN** the file defines expected output
- **THEN** stdout patterns match documented help text structure
- **AND** exit code is 0 for valid invocation.

### Requirement: Schema Validation Tool

The system SHALL provide a validation tool that checks scenario YAML files against the schema and reports errors.

#### Scenario: Validation tool runs via hatch script

- **GIVEN** scenario files exist in `tests/cli-contracts/`
- **WHEN** `hatch run validate-cli-contracts` is executed
- **THEN** all scenario files are validated against the schema
- **AND** errors are reported with file path and line context
- **AND** exit code is 0 when all files pass, non-zero when any fail.
