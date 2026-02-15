## MODIFIED Requirements

### Requirement: Policy Engine
Policy evaluation outputs SHALL be serializable into governance evidence records.

#### Scenario: Policy rule results include evidence-ready fields
- **GIVEN** policy validation completes
- **WHEN** evidence serialization runs
- **THEN** each rule result includes rule ID, severity, mode, and outcome
- **AND** output can be consumed by CI gates without additional transformation.
