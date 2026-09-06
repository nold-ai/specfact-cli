# test-suite-stabilization Specification Delta

## ADDED Requirements

### Requirement: Primary test suite ignores the outer pull-request base

The pull-request orchestrator SHALL prevent its primary test process from
receiving an effective `GITHUB_BASE_REF` value.

#### Scenario: Primary test suite ignores the outer pull-request base

- **GIVEN** a pull-request job with a GitHub-provided base reference
- **WHEN** the Python 3.12 test suite executes
- **THEN** its test process receives no effective `GITHUB_BASE_REF` value
- **AND** tests that create synthetic Git repositories resolve only their own
  fixture history.

### Requirement: Compatibility suite ignores the outer pull-request base

The pull-request orchestrator SHALL prevent its Python 3.11 compatibility test
process from receiving an effective `GITHUB_BASE_REF` value.

#### Scenario: Compatibility suite ignores the outer pull-request base

- **GIVEN** a pull-request job with a GitHub-provided base reference
- **WHEN** the Python 3.11 compatibility suite executes
- **THEN** its pytest process receives no effective `GITHUB_BASE_REF` value.

### Requirement: Non-test workflow routing remains unchanged

The pull-request orchestrator SHALL preserve GitHub's authentic base-reference
value for non-test workflow behavior.

#### Scenario: Non-test workflow routing remains unchanged

- **GIVEN** release, signature, change-selection, and other non-test workflow
  steps
- **WHEN** they evaluate the pull-request base
- **THEN** they retain the authentic GitHub-provided `GITHUB_BASE_REF` value.
