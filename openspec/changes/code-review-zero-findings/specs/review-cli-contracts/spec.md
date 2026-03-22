## ADDED Requirements

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
