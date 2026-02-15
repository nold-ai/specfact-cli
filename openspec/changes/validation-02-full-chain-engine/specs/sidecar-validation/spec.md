## MODIFIED Requirements

### Requirement: Sidecar Validation
The sidecar validation capability SHALL support full-chain payload checks in addition to spec-code checks.

#### Scenario: Sidecar consumes full-chain input set
- **GIVEN** requirement and architecture artifact paths are provided
- **WHEN** sidecar validation runs
- **THEN** sidecar validates layered chain references
- **AND** results are merged into full-chain evidence output.

#### Scenario: Existing spec-code validation remains supported
- **GIVEN** sidecar is invoked without requirements/architecture inputs
- **WHEN** validation executes
- **THEN** existing spec-code validation behavior continues unchanged.
