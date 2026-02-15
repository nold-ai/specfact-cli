## MODIFIED Requirements

### Requirement: Profile Config Layering
The system SHALL incorporate central config sources into profile layering without breaking existing local-only workflows.

#### Scenario: Local-only repositories remain valid
- **GIVEN** no central source is configured
- **WHEN** profile layering resolves config
- **THEN** resolution still works with profile, repo, and local layers
- **AND** no network dependency is required.

#### Scenario: Source attribution includes central baseline
- **GIVEN** central baseline is configured
- **WHEN** resolved config is inspected
- **THEN** keys sourced from baseline are marked as central
- **AND** overridden keys show both baseline and overriding source.
