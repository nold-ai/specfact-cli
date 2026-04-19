## ADDED Requirements

### Requirement: Enterprise Resolution Layers

The system SHALL support enterprise policy resolution layers for org-mandatory and team-advisory rules above the existing local chain.

#### Scenario: Org-mandatory rule takes precedence

- **GIVEN** enterprise configuration is present and an org-mandatory rule exists for a setting
- **WHEN** resolution runs
- **THEN** the org-mandatory value wins over team, project, profile, and built-in values
- **AND** local overrides are rejected unless a signed exception path allows them.

#### Scenario: Missing enterprise configuration preserves local behavior

- **GIVEN** no enterprise configuration or cache is present
- **WHEN** policy resolution runs
- **THEN** local CLI, project, profile, and built-in resolution continues unchanged
- **AND** no enterprise error is emitted.

### Requirement: Pushed Rule Metadata

The system SHALL validate signed metadata for pushed enterprise rules.

#### Scenario: Pushed rule carries provenance metadata

- **WHEN** an enterprise rule is loaded
- **THEN** it records `mandatory`, `override_allowed`, `effective_from`, `pushed_by`, and `signed_by`
- **AND** missing required metadata fails validation.
