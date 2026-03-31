# review-cli-contracts Specification

## Purpose
TBD - created by archiving change code-review-08-review-run-integration. Update Purpose after archive.
## Requirements
### Requirement: cli-val-01 Scenario YAML Files for All Three Command Groups
The system SHALL provide cli-val-01 compliant scenario YAML files for `specfact code review run`, `ledger`, and `rules` command groups.

#### Scenario: review-run scenarios cover happy path and anti-patterns
- **GIVEN** `tests/cli-contracts/specfact-code-review-run.scenarios.yaml` exists
- **WHEN** parsed against the cli-val-01 schema
- **THEN** it contains at least one happy-path scenario (exit 0 on clean file) and one anti-pattern scenario

#### Scenario: ledger scenarios cover pipe flow, status, and reset guard
- **GIVEN** `tests/cli-contracts/specfact-code-review-ledger.scenarios.yaml` exists
- **WHEN** parsed
- **THEN** it covers `ledger update` happy path, `ledger update` invalid JSON anti-pattern, `ledger status` happy path, and `ledger reset` missing --confirm anti-pattern

#### Scenario: rules scenarios cover all three subcommands
- **GIVEN** `tests/cli-contracts/specfact-code-review-rules.scenarios.yaml` exists
- **WHEN** parsed
- **THEN** it covers `rules show`, `rules update`, and `rules init` happy paths plus error cases

#### Scenario: All scenario files conform to cli-val-01 schema
- **GIVEN** all three scenario YAML files
- **WHEN** validated against the cli-val-01 behavior contract schema
- **THEN** no validation errors are reported

### Requirement: Review CLI commands carry icontract and beartype decorators
All public command functions in the review module (`specfact code review run`, `ledger`, `rules`) SHALL have `@require` / `@ensure` decorators (icontract) and `@beartype` on their signatures, consistent with the project-wide contract-first standard.

#### Scenario: review run command has precondition on repo_path
- **WHEN** `specfact code review run` is invoked with an invalid `repo_path`
- **THEN** an icontract `ViolationError` is raised before any tool runner is invoked
- **AND** the error message references the violated precondition

#### Scenario: review CLI contracts are consistent with typed signatures
- **WHEN** `hatch run contract-test` is executed after type annotations are applied to the review CLI module
- **THEN** `contract_runner` reports zero `MISSING_ICONTRACT` findings for review command functions
- **AND** `basedpyright` reports zero type errors for the review CLI module

#### Scenario: Contract validation scenarios cover review run with CI flag
- **GIVEN** `tests/cli-contracts/specfact-code-review-run.scenarios.yaml` exists
- **WHEN** a scenario exercising `review run --ci` with a clean target is added
- **THEN** the scenario validates exit code 0 and presence of `.specfact/code-review.json`

