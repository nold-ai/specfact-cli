## MODIFIED Requirements

### Requirement: Profile and Project Configuration Resolve in a Deterministic Order

Configuration resolution SHALL remain deterministic while allowing optional enterprise layers to precede local project and profile values.

#### Scenario: Team-advisory rule precedes local defaults

- **GIVEN** enterprise configuration provides a team-advisory value and no org-mandatory override exists
- **WHEN** resolution runs
- **THEN** the team-advisory value is applied before project and profile defaults
- **AND** explicit CLI overrides may still replace it when `override_allowed` is true.

#### Scenario: Resolution inspection shows the winning layer

- **GIVEN** a resolved configuration value
- **WHEN** the user inspects its source
- **THEN** the winning layer and enterprise provenance metadata are shown when applicable
- **AND** local-only values remain labeled consistently with existing behavior.
