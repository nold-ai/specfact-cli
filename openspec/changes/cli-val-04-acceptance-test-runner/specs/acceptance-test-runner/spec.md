## ADDED Requirements

### Requirement: Dual-Path Scenario Execution

The system SHALL execute CLI behavior scenarios via both in-process (CliRunner) and subprocess (installed binary) paths.

#### Scenario: Fast path executes scenario via CliRunner

- **GIVEN** a YAML scenario file with argv, expected exit code, and output patterns
- **WHEN** the runner executes the scenario in fast path mode
- **THEN** the scenario is invoked via `typer.testing.CliRunner`
- **AND** exit code and output assertions are verified
- **AND** execution completes in under 1 second per scenario.

#### Scenario: Black-box path executes scenario via subprocess

- **GIVEN** a YAML scenario file and the `specfact` binary is installed on PATH
- **WHEN** the runner executes the scenario in black-box mode
- **THEN** the scenario is invoked via `subprocess.run()`
- **AND** real exit code, stdout, and stderr are captured and asserted
- **AND** the test validates the installed binary, not the source tree.

#### Scenario: Filesystem diff verification in sandboxed workspace

- **GIVEN** a scenario with `fs.creates` and `fs.forbidden` expectations
- **WHEN** the runner executes the scenario in a sandboxed `tmp_path` workspace
- **THEN** expected files are verified as created
- **AND** forbidden files are verified as absent
- **AND** the workspace is isolated from the real filesystem.

### Requirement: YAML Scenario Loading

The system SHALL load and parse YAML scenario files following the cli-val-01 schema.

#### Scenario: Runner discovers and loads all scenario files

- **GIVEN** scenario YAML files exist in `tests/cli-contracts/`
- **WHEN** the runner initializes
- **THEN** all `.scenarios.yaml` files are discovered and parsed
- **AND** both pattern and anti-pattern scenarios are loaded.

#### Scenario: Runner skips scenarios with unmet context requirements

- **GIVEN** a scenario requiring context `requires: sample-bundle` and the workspace lacks a sample bundle
- **WHEN** the runner evaluates the scenario
- **THEN** the scenario is skipped with a descriptive message
- **AND** skipped scenarios do not count as failures.

### Requirement: Pytest Integration

The system SHALL integrate with pytest so acceptance tests appear in standard test reports.

#### Scenario: Acceptance tests collected by pytest

- **GIVEN** `tests/e2e/test_cli_acceptance.py` exists
- **WHEN** `pytest tests/e2e/test_cli_acceptance.py` is run
- **THEN** each scenario appears as a separate test case
- **AND** test names include the scenario name for identification.

#### Scenario: Black-box tests selectable via marker

- **GIVEN** acceptance tests with both fast and black-box paths
- **WHEN** `pytest -m "blackbox"` is run
- **THEN** only black-box (subprocess) tests execute
- **AND** fast-path tests are excluded.

### Requirement: Flagship Command Chain Tests

The system SHALL include living-documentation acceptance tests for 3-5 flagship command workflows.

#### Scenario: Init workflow tested end-to-end

- **GIVEN** an empty temporary directory
- **WHEN** `specfact init` is run followed by a validation command
- **THEN** the full workflow completes successfully
- **AND** the test serves as executable documentation of the expected workflow.
