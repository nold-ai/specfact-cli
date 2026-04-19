## MODIFIED Requirements

### Requirement: Signed Audit Event Schema

Signed audit events SHALL expose the references required for enterprise drift analytics.

#### Scenario: Audit event supports analytics correlation

- **GIVEN** an audited rule promotion, override, or approval event
- **WHEN** the event is written
- **THEN** it may include stable correlation identifiers needed by drift analytics
- **AND** those identifiers do not duplicate whole evidence payloads.
