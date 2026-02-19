## ADDED Requirements

### Requirement: Systematic Anti-Pattern Catalog

The system SHALL maintain an anti-pattern catalog for every command group documenting known misuse cases and their expected safe failure behavior.

#### Scenario: Each command group has anti-pattern scenarios

- **GIVEN** a command group registered in the CLI
- **WHEN** its anti-pattern catalog is loaded
- **THEN** at least 3 anti-pattern scenarios are defined
- **AND** each scenario specifies exact argv, expected non-zero exit, and error pattern.

#### Scenario: Anti-patterns cover common misuse categories

- **GIVEN** an anti-pattern catalog for a command group
- **WHEN** the catalog is reviewed
- **THEN** it includes scenarios for: missing required arguments, invalid flag values, nonexistent file paths, malformed input files, and forbidden option combinations where applicable.

### Requirement: Three-Property Safety Assertion

Every anti-pattern test SHALL assert three properties: non-zero exit, human-readable error, and no unintended side effects.

#### Scenario: Non-zero exit on invalid input

- **GIVEN** a CLI command invoked with an anti-pattern argv
- **WHEN** the command executes
- **THEN** the exit code is non-zero.

#### Scenario: Human-readable error without traceback

- **GIVEN** a CLI command invoked with an anti-pattern argv and `--debug` is NOT set
- **WHEN** the command produces error output
- **THEN** stderr contains a human-readable error message
- **AND** neither stdout nor stderr contains a Python traceback (`Traceback (most recent call last)`).

#### Scenario: No unintended filesystem side effects

- **GIVEN** a CLI command invoked with an anti-pattern argv inside a sandboxed `tmp_path` workspace
- **WHEN** the command fails
- **THEN** no files are created or modified in the workspace beyond what existed before invocation.

### Requirement: Hypothesis Property-Based Fuzzing

The system SHALL use Hypothesis to generate edge-case inputs for major command groups and assert safe failure.

#### Scenario: Fuzz testing with invalid enum values

- **GIVEN** a command that accepts enum-typed arguments
- **WHEN** Hypothesis generates values outside the valid enum set
- **THEN** the command exits non-zero with a descriptive error
- **AND** no crash or unhandled exception occurs.

#### Scenario: Fuzz testing with path edge cases

- **GIVEN** a command that accepts file path arguments
- **WHEN** Hypothesis generates paths with Unicode, spaces, empty strings, and deeply nested paths
- **THEN** the command exits non-zero for invalid paths
- **AND** no crash or unhandled exception occurs.

#### Scenario: Fuzz testing completes within time budget

- **GIVEN** Hypothesis strategies configured for CLI fuzzing
- **WHEN** the fuzz suite runs
- **THEN** all tests complete within 30 seconds per command group
- **AND** any failure is reported with a minimal reproducing example.
