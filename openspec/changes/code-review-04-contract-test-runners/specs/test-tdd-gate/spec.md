## ADDED Requirements

### Requirement: TDD Gate Enforcing Test File Existence and Coverage Threshold
The system SHALL block the review if any changed `src/` file has no corresponding test file, or if tests fail, or if coverage is below 80%.

#### Scenario: Changed src file with no test file produces BLOCK
- **GIVEN** a changed file `src/specfact_code_review/run/scorer.py` with no corresponding test file
- **WHEN** the TDD gate runs
- **THEN** a `ReviewFinding` with `rule="TEST_FILE_MISSING"`, `severity="error"`, `category="testing"` is returned
- **AND** the overall verdict is forced to BLOCK

#### Scenario: Passing tests with coverage >= 80% produces no finding
- **GIVEN** a changed file with a corresponding test file and 85% coverage
- **WHEN** the TDD gate runs
- **THEN** no testing finding is returned

#### Scenario: Test failure produces BLOCK finding
- **GIVEN** a changed file with failing tests
- **WHEN** the TDD gate runs
- **THEN** a `ReviewFinding` with `severity="error"` and `category="testing"` is returned

#### Scenario: Coverage below 80% produces warning
- **GIVEN** passing tests with 65% coverage
- **WHEN** the TDD gate runs
- **THEN** a `ReviewFinding` with `severity="warning"` and `category="testing"` is returned

#### Scenario: --no-tests flag skips TDD gate
- **GIVEN** `--no-tests` is passed to `specfact code review run`
- **WHEN** the runner executes
- **THEN** no TDD gate check is performed and no testing findings are returned
