## MODIFIED Requirements

### Requirement: FinOps Session Evidence Schema

The FinOps session evidence schema SHALL record budget-gate, wait-state, and approval events alongside cost and outcome data.

#### Scenario: Wait-state event is captured

- **GIVEN** a run is paused by the budget gate
- **WHEN** FinOps evidence is written
- **THEN** the record includes the gate decision, projected overage details, and a resume-token reference
- **AND** the original session outcome remains auditable.

#### Scenario: Approval event updates the session trail

- **GIVEN** a paused run is later approved
- **WHEN** the session trail is updated
- **THEN** the approval tier and approval timestamp are recorded
- **AND** downstream reporting can correlate the approval with the original paused run.
