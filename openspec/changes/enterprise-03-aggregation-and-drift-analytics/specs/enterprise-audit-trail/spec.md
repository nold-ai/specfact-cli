## MODIFIED Requirements

### Requirement: Signed Audit Event Schema

Signed audit events SHALL expose the references required for enterprise drift analytics.

#### Scenario: Audit event supports analytics correlation

- **GIVEN** an audited rule promotion, override, or approval event
- **WHEN** the event is written
- **THEN** the event MUST include stable correlation identifiers required for enterprise drift analytics (references only; no full evidence bodies)
- **AND** those identifiers MUST NOT duplicate whole evidence payloads.
