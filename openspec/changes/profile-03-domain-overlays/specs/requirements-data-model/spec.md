## MODIFIED Requirements

### Requirement: Requirements Data Model
The system SHALL support schema-driven required fields introduced by domain overlays.

#### Scenario: Overlay-required fields enforced at model validation
- **GIVEN** overlay declares additional required fields
- **WHEN** a requirement document is parsed
- **THEN** missing overlay-required fields cause validation errors
- **AND** error output identifies the overlay and missing fields.

#### Scenario: Base schema compatibility preserved
- **GIVEN** no domain overlay is active
- **WHEN** requirement documents are validated
- **THEN** base requirements schema behavior remains unchanged.
