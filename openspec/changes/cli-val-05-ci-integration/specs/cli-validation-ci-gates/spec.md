## ADDED Requirements

### Requirement: Snapshot Validation Gate

The CI pipeline SHALL fail on snapshot mismatches to prevent unintentional output changes.

#### Scenario: PR fails when snapshots do not match

- **GIVEN** a PR modifies CLI command output (help text, error messages, structured output)
- **WHEN** the CI pipeline runs snapshot tests without `--snapshot-update` flag
- **THEN** the pipeline fails with a clear error listing mismatched snapshots
- **AND** the PR cannot merge until snapshots are updated or code is fixed.

#### Scenario: Snapshot update workflow available for intentional changes

- **GIVEN** a developer intentionally changes CLI output
- **WHEN** the developer triggers the snapshot update workflow
- **THEN** snapshots are regenerated and committed
- **AND** the updated snapshot files appear in the PR diff for review.

### Requirement: Black-Box Acceptance Gate

The CI pipeline SHALL run acceptance tests against the installed binary as a hard gate on PRs to main.

#### Scenario: Black-box tests run against installed wheel

- **GIVEN** the CI pipeline builds a wheel from the PR branch
- **WHEN** the black-box acceptance job installs the wheel and runs subprocess-path scenarios
- **THEN** all pattern and anti-pattern scenarios pass
- **AND** the installed binary is verified to work as expected.

#### Scenario: Black-box failure blocks merge to main

- **GIVEN** a black-box acceptance test fails
- **WHEN** the PR targets main
- **THEN** the merge is blocked
- **AND** the failure is reported with scenario name and expected vs actual output.

### Requirement: Tiered Gating Policy

The CI pipeline SHALL distinguish hard gates (block merge) from advisory gates (warn only).

#### Scenario: Hard gates block merge

- **GIVEN** a snapshot mismatch, black-box acceptance failure, or anti-pattern safety violation
- **WHEN** the CI pipeline evaluates gates
- **THEN** the PR is blocked from merging
- **AND** the failure reason is visible in PR checks.

#### Scenario: Advisory gates warn without blocking

- **GIVEN** a Hypothesis-discovered edge case or coverage threshold miss
- **WHEN** the CI pipeline evaluates gates
- **THEN** a warning annotation is added to the PR
- **AND** the PR is not blocked from merging.

### Requirement: Contract-Test Tier Extension

The contract-first test system SHALL include CLI behavior contracts as a recognized tier.

#### Scenario: CLI validation runs as part of contract-test

- **GIVEN** the developer runs `hatch run contract-test`
- **WHEN** CLI behavior contract files exist in `tests/cli-contracts/`
- **THEN** CLI scenario validation is included in the test run
- **AND** results appear alongside existing contract/exploration/scenario tiers.
