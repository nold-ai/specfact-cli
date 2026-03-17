## ADDED Requirements

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
