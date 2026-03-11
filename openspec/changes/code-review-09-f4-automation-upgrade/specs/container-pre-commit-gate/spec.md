## ADDED Requirements

### Requirement: Stage 6 Pre-Commit Gate in coding-workflow.js
The system SHALL run `specfact code review run --score-only` as a pre-commit gate in stage 6. Exit code 1 prevents the git commit and fires `REVIEW_BLOCKED` callback.

#### Scenario: PASS verdict allows commit to proceed
- **GIVEN** changed files have exit code 0 from the review gate
- **WHEN** stage 6 pre-commit gate runs
- **THEN** the gate passes and the git commit in stage 6 proceeds

#### Scenario: BLOCK verdict prevents git commit
- **GIVEN** changed files have exit code 1 from the review gate
- **WHEN** stage 6 pre-commit gate runs
- **THEN** no `git commit` command is executed
- **AND** `REVIEW_BLOCKED` callback is fired with score details and the container exits non-zero

#### Scenario: WARN verdict allows commit
- **GIVEN** changed files have exit code 0 (WARN maps to 0) from the review gate
- **WHEN** stage 6 runs
- **THEN** the gate passes and the git commit proceeds

#### Scenario: specfact unavailable causes graceful degradation
- **GIVEN** `specfact` binary is not in PATH
- **WHEN** stage 6 attempts the pre-commit gate
- **THEN** a warning is logged and the commit proceeds (fail-open for tool availability)

#### Scenario: HOUSE_RULES present in stage 5 stdin
- **GIVEN** house_rules skill content is read at container startup
- **WHEN** stage 5 sends stdin JSON to the coding CLI
- **THEN** the JSON contains `context.house_rules` with the skill content
