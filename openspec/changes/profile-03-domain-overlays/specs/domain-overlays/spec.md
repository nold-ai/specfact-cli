## ADDED Requirements

### Requirement: Domain Overlays
The system SHALL allow domain-specific overlays to extend profile requirements and policy constraints.

#### Scenario: Domain overlay adds required requirement fields
- **GIVEN** an enterprise profile with `payments` overlay
- **WHEN** requirements schema is resolved
- **THEN** overlay-required fields include `regulatory_reference` and `risk_owner`
- **AND** requirement validation fails when those fields are missing.

#### Scenario: Domain overlay adds architectural constraints
- **GIVEN** overlay defines mandatory shared payment gateway usage
- **WHEN** architecture validation runs
- **THEN** solutions missing that integration are flagged
- **AND** severity follows active policy mode.
