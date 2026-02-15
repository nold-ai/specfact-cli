## MODIFIED Requirements

### Requirement: Governance Evidence Output
Governance evidence SHALL include exception lifecycle status for active and expired exceptions.

#### Scenario: Exception lifecycle is visible in evidence
- **GIVEN** evidence generation runs with configured exceptions
- **WHEN** artifact is emitted
- **THEN** evidence lists applied, pending-expiry, and expired exception states
- **AND** each entry includes policy, scope, and expiry date.
