## MODIFIED Requirements

### Requirement: Budget Approval Gate

The budget approval gate SHALL support enterprise routing and attribution metadata without changing local gate state semantics.

#### Scenario: Enterprise approval metadata is captured

- **GIVEN** a paused run is routed to an enterprise approver
- **WHEN** the gate records the wait-state
- **THEN** the gate evidence includes enterprise routing metadata and chargeback identifiers
- **AND** the original projected-overage details remain attached.

#### Scenario: Approval decision preserves chargeback attribution

- **GIVEN** a routed enterprise approval is granted or denied
- **WHEN** the gate updates the session trail
- **THEN** the decision carries the same team or cost-center attribution used for chargeback reporting
- **AND** downstream audits can correlate the decision with the original paused run.
