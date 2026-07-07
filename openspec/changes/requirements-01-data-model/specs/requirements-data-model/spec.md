## ADDED Requirements

### Requirement: Requirements Evidence Input Model

The system SHALL define normalized requirement input records that preserve upstream source references for validation evidence.

#### Scenario: Requirement input captures source-backed intent and constraints

- **GIVEN** a requirement input record carried in `requirements.inputs`
- **WHEN** validation evidence reads the record
- **THEN** it includes a stable requirement identifier, schema version, title, and at least one upstream source reference
- **AND** it MAY include business rules, constraints, and profile completeness findings.

#### Scenario: Evidence links are represented explicitly

- **GIVEN** requirement evidence metadata
- **WHEN** artifacts are parsed
- **THEN** architecture, spec, code, test, and validation references are stored as explicit evidence links
- **AND** evidence links are serializable to JSON output.

#### Scenario: Profile completeness is advisory evidence

- **GIVEN** a requirement input with profile completeness findings
- **WHEN** validation evidence is produced
- **THEN** each finding records the profile, severity, field path, and message
- **AND** missing optional profile fields do not make the requirement input unusable.
