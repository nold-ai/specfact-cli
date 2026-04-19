## ADDED Requirements

### Requirement: Enterprise Contribution Flag

The system SHALL support an explicit `contribute-to-org` flag controlling whether local learnings or rules participate in enterprise aggregation.

#### Scenario: Local learning remains local by default

- **GIVEN** a learning or rule has no contribution flag
- **WHEN** enterprise aggregation prepares payloads
- **THEN** the artifact is excluded from org aggregation
- **AND** local distillation behavior remains unchanged.

#### Scenario: Opted-in learning is eligible for aggregation

- **GIVEN** a learning or rule sets `contribute-to-org: true`
- **WHEN** aggregation payloads are built
- **THEN** the artifact is included using structured metadata only
- **AND** required references to evidence or audit events are preserved.

### Requirement: Drift Metrics Contract

The system SHALL define drift metrics for override rate, stale distillation cycles, cross-team pattern reuse, and unresolved churn.

#### Scenario: Override rate metric is derivable

- **WHEN** enterprise drift analytics are computed
- **THEN** override rate can be derived from enterprise audit events over a selected window
- **AND** the metric is published with the same window metadata used for the calculation.

#### Scenario: Analytics summary links back to source references

- **WHEN** a drift analytics summary is emitted
- **THEN** it includes references to the underlying audit events or evidence ids
- **AND** the summary can be reconstructed without hidden state.
