## MODIFIED Requirements

### Requirement: Init Module State

The system SHALL initialize module state according to the active profile selected during `specfact init`.

#### Scenario: Profile activates expected module set

- **GIVEN** `specfact init --profile startup`
- **WHEN** init writes module state
- **THEN** enabled modules include sync and ceremony capabilities for startup
- **AND** modules outside the startup profile default set remain disabled unless explicitly enabled.

#### Scenario: Backward compatible default behavior

- **GIVEN** `specfact init` is executed without `--profile`
- **WHEN** module state is generated
- **THEN** behavior matches current default compatibility profile
- **AND** no hard-fail governance mode is enabled implicitly.
