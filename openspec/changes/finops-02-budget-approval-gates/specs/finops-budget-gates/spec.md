## ADDED Requirements

### Requirement: Budget Policy Schema

The system SHALL define a budget policy schema for per-flow, per-project, and periodic cost controls.

#### Scenario: Policy defines per-flow caps

- **WHEN** a budget policy is loaded
- **THEN** it can specify token and cost caps for individual flows
- **AND** invalid approval-tier values fail validation.

#### Scenario: Policy defines project budget windows

- **WHEN** a project budget is configured
- **THEN** the policy can declare weekly or monthly budget windows
- **AND** the gate can evaluate projected usage against the correct window.

### Requirement: Budget Approval Gate

The system SHALL pause or block projected-overbudget runs according to the active policy.

#### Scenario: Projected overspend requires approval

- **GIVEN** projected cost exceeds the active policy threshold and approval tier is not `auto`
- **WHEN** the gate evaluates the run
- **THEN** execution pauses with a structured wait-state result
- **AND** a resume token is returned for later continuation.

#### Scenario: Advisory gate warns without blocking

- **GIVEN** the policy is advisory-only
- **WHEN** projected overspend is detected
- **THEN** the warning is recorded in FinOps evidence
- **AND** execution may continue without pause.

### Requirement: Burndown Report CLI

The system SHALL provide a FinOps burndown report command summarizing spend, outcomes, and gate events.

#### Scenario: Weekly report summarizes budget posture

- **WHEN** `specfact finops report --period weekly` runs
- **THEN** the report includes cost totals, outcome counts, and gate/approval event counts for the selected window
- **AND** JSON output remains available for downstream automation.
