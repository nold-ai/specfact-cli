## ADDED Requirements

### Requirement: End-to-End specfact code review run Command

The system SHALL provide a fully wired `specfact code review run` command that orchestrates all tool runners and returns a `ReviewReport` with correct exit codes (0=PASS/WARN, 1=BLOCK).

#### Scenario: Run on clean fixture produces PASS and exit 0

- **GIVEN** `tests/fixtures/review/clean_module.py` with no violations and passing tests
- **WHEN** `specfact code review run tests/fixtures/review/clean_module.py` is called
- **THEN** `overall_verdict` equals `"PASS"` and exit code is `0`

#### Scenario: Run on dirty fixture produces BLOCK and exit 1

- **GIVEN** `tests/fixtures/review/dirty_module.py` with violations and missing test file
- **WHEN** `specfact code review run tests/fixtures/review/dirty_module.py` is called
- **THEN** `overall_verdict` equals `"FAIL"` and exit code is `1`

#### Scenario: --json outputs valid ReviewReport JSON

- **GIVEN** any set of files
- **WHEN** `specfact code review run --json` is called
- **THEN** stdout contains valid JSON parseable as `ReviewReport` with all governance fields present

#### Scenario: --score-only prints only reward_delta integer

- **GIVEN** a run with `reward_delta=-5`
- **WHEN** `specfact code review run --score-only` is called
- **THEN** stdout contains exactly `-5` followed by a newline

#### Scenario: --fix applies ruff autofix then re-runs

- **GIVEN** files with auto-fixable ruff violations
- **WHEN** `specfact code review run --fix` is called
- **THEN** `ruff --fix` is applied and the review runs again on the fixed files

#### Scenario: No files provided uses git diff HEAD

- **GIVEN** no `FILES` argument is provided
- **WHEN** `specfact code review run` is called
- **THEN** changed files are determined from `git diff HEAD --name-only` and the run proceeds
