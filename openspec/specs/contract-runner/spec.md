# contract-runner Specification

## Purpose

TBD - created by archiving change code-review-04-contract-test-runners. Update Purpose after archive.

## Requirements

### Requirement: icontract Decorator AST Scan and CrossHair Fast Pass

The system SHALL AST-scan changed Python files for public functions missing `@require`/`@ensure` decorators, and run CrossHair (2s/path timeout) for counterexample discovery.

#### Scenario: Public function without @require produces contracts finding

- **GIVEN** a Python file with `def process_data(x):` without icontract decorators
- **WHEN** `run_contract_check(files=[...])` is called
- **THEN** a `ReviewFinding` is returned with `category="contracts"` and `severity="warning"`

#### Scenario: Public function with decorators produces no finding

- **GIVEN** a file with a public function decorated with both `@require` and `@ensure`
- **WHEN** `run_contract_check(files=[...])` is called
- **THEN** no contract-related finding is returned for that function

#### Scenario: Private functions excluded from scan

- **GIVEN** a file with `def _private_helper(x):` without decorators
- **WHEN** `run_contract_check(files=[...])` is called
- **THEN** no finding is produced for `_private_helper`

#### Scenario: CrossHair counterexample maps to contracts warning

- **GIVEN** CrossHair finds a counterexample for a function
- **WHEN** `run_contract_check(files=[...])` is called
- **THEN** a `ReviewFinding` is returned with `category="contracts"`, `severity="warning"`, `tool="crosshair"`

#### Scenario: CrossHair timeout or unavailability degrades gracefully

- **GIVEN** CrossHair hits the 2s timeout or is not installed
- **WHEN** `run_contract_check(files=[...])` is called
- **THEN** the AST scan still runs and no exception propagates
