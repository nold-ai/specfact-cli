## ADDED Requirements

### Requirement: Policy Packs And Modes
The system SHALL install policy packs and evaluate them under active enforcement mode.

#### Scenario: Policy pack install and listing
- **GIVEN** `specfact policy install <pack-ref>`
- **WHEN** installation succeeds
- **THEN** pack metadata is persisted in active configuration
- **AND** `specfact policy list --show-mode` displays pack and mode.

#### Scenario: New policy starts in shadow/advisory period
- **GIVEN** newly installed pack with gradual rollout enabled
- **WHEN** validation is run during rollout window
- **THEN** failures are advisory
- **AND** mode promotion behavior is traceable in config/evidence.

#### Scenario: Clean-code pack installs as a first-class built-in pack
- **GIVEN** `specfact policy install specfact/clean-code-principles`
- **WHEN** installation succeeds
- **THEN** the pack exposes rule IDs for naming, kiss, yagni, dry, solid, and code-review checks
- **AND** no separate clean-code-specific configuration system is required outside `.specfact/policy.yaml`
