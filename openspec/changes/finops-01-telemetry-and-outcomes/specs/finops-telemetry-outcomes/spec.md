## ADDED Requirements

### Requirement: FinOps Session Evidence Schema

The system SHALL define a canonical FinOps session evidence schema carrying flow, model, token, cost, and outcome metadata.

#### Scenario: Session evidence carries required FinOps fields

- **WHEN** a FinOps session evidence record is emitted
- **THEN** it includes `flow`, `model`, `tokens_in`, `tokens_out`, `cost_usd`, and `outcome`
- **AND** optional project or team identifiers do not replace the required core fields.

#### Scenario: Invalid token or cost values are rejected

- **GIVEN** a session record with negative token counts or negative `cost_usd`
- **WHEN** the schema validates the record
- **THEN** validation fails before the evidence is written.

### Requirement: Shared Outcome Enum

The system SHALL provide a shared outcome enum reusable across telemetry, governance, and knowledge evidence.

#### Scenario: Outcome enum is stable across producers

- **WHEN** a review, authoring, or implementation flow records a completed session
- **THEN** the outcome is one of `rework-required`, `spec-approved`, `code-merged-clean`, `test-passed-first-run`, or `rule-updated`
- **AND** downstream consumers do not need producer-specific outcome mappings.

### Requirement: Efficiency Ratio Contract

The system SHALL publish an efficiency ratio contract based on score, tokens, and cost.

#### Scenario: Efficiency ratio is deterministic

- **GIVEN** a session record with fixed score, token counts, and cost
- **WHEN** efficiency ratio is calculated
- **THEN** repeated calculations produce the same numeric result
- **AND** zero-token or zero-cost edge cases are handled without division errors.
