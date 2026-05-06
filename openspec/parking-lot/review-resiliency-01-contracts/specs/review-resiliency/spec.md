## ADDED Requirements

### Requirement: Resiliency Finding Model

The system SHALL define a resiliency finding model with fixed categories and deterministic rule-id format.

#### Scenario: Finding carries canonical category enum

- **GIVEN** a resiliency runner emits a finding for a missing timeout
- **WHEN** the finding is serialised
- **THEN** the category is one of the 9 enum values
- **AND** the rule id matches pattern `^RES-[A-Z_]+-\d{3}$`.

#### Scenario: Unknown category is rejected

- **GIVEN** a runner emits a finding with category `"flakiness"` (not in enum)
- **WHEN** the scorer consumes the finding
- **THEN** validation raises and the report run fails with exit code 2.

### Requirement: Resiliency Scorer Contract

The system SHALL deterministically map findings to severity and aggregate them per category for the shared review-report envelope.

#### Scenario: Severity is fixed per rule-id

- **GIVEN** rule `RES-TIMEOUT-001` defaults to severity `high`
- **WHEN** any finding with that rule-id is scored
- **THEN** the severity is `high`
- **AND** profile-level overrides can only downgrade to advisory, not upgrade above the registered default without explicit policy.

#### Scenario: Scorer emits a single resiliency block in the shared envelope

- **GIVEN** a run produces findings across multiple categories
- **WHEN** the scorer serialises its output
- **THEN** the shared review-report envelope contains a top-level `resiliency` section with per-category counts and a verdict
- **AND** the existing `code_quality` section is not modified.

### Requirement: Resiliency CLI Command

The system SHALL provide `specfact review resiliency` with JSON/markdown reports and enforcement-mode exit codes.

#### Scenario: Hard mode fails run on blocker

- **GIVEN** the active profile enforcement mode is `hard` and a blocker finding exists
- **WHEN** `specfact review resiliency` runs
- **THEN** exit code is 1
- **AND** the report includes the blocker finding with remediation guidance.

#### Scenario: Advisory mode never fails

- **GIVEN** the active profile enforcement mode is `advisory`
- **WHEN** any number of findings (including blocker) are produced
- **THEN** exit code is 0
- **AND** the report is emitted identically to hard mode (only exit code differs).

#### Scenario: JSON report schema matches review-report-model

- **GIVEN** `--report json`
- **WHEN** the command completes
- **THEN** stdout is valid JSON conforming to the shared review-report envelope
- **AND** the top-level `schema_version` is present.

### Requirement: Resiliency Report Envelope Integration

The system SHALL emit resiliency findings as a top-level `resiliency` section inside the shared `ReviewReport` envelope, without mutating other sections.

#### Scenario: Envelope carries both code_quality and resiliency sections

- **GIVEN** a run produces both clean-code and resiliency findings
- **WHEN** the shared envelope is built
- **THEN** both `code_quality` and `resiliency` sections are present
- **AND** neither section's schema is mutated by the other's presence.
