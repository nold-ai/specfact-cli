## ADDED Requirements

### Requirement: Requirements Module
The system SHALL provide requirements CLI commands for extract, author, validate, and list.

#### Scenario: Extract command creates requirement artifacts
- **GIVEN** `specfact requirements extract --from-backlog <adapter> --output .specfact/requirements/`
- **WHEN** extraction succeeds
- **THEN** one or more `*.req.yaml` files are produced
- **AND** each file includes schema version and source backlog reference.

#### Scenario: Author command applies profile-aware template fields
- **GIVEN** `specfact requirements author --template story`
- **WHEN** active profile is `solo`
- **THEN** authoring prompts require only solo-required fields
- **AND** optional advanced fields remain non-blocking.

#### Scenario: Validate and list expose completeness and trace coverage
- **GIVEN** requirement artifacts with trace references
- **WHEN** `specfact requirements validate` and `specfact requirements list --show-coverage` run
- **THEN** completeness and coverage are reported per requirement
- **AND** output is machine-readable when requested.
