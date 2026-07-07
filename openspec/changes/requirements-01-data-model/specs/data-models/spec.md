## MODIFIED Requirements

### Requirement: Requirements Input Extension Namespace

The system SHALL support requirement input payloads through the existing ProjectBundle schema extension mechanism.

#### Scenario: Project bundle accepts requirements namespace

- **GIVEN** a project bundle with `requirements.inputs` extension entries
- **WHEN** model validation runs
- **THEN** the requirements namespace is accepted through the existing extensions field
- **AND** existing non-requirements fields remain backward compatible.

#### Scenario: Schema version is required for requirements artifacts

- **GIVEN** a requirement document without `schema_version`
- **WHEN** it is loaded
- **THEN** requirement input validation fails
- **AND** output indicates the missing version field.
