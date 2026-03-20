## MODIFIED Requirements

### Requirement: Azure DevOps Backlog Sync Support

The system SHALL support Azure DevOps work items as a backlog adapter in the DevOps sync workflow.

#### Scenario: Selective ADO import preserves native payload for proposal import

- **GIVEN** a user runs `specfact project sync bridge --adapter ado --mode bidirectional --backlog-ids 123456`
- **WHEN** bridge sync fetches that single ADO work item for import as an OpenSpec change proposal
- **THEN** the adapter returns the provider-native work item payload with a populated `fields` object
- **AND** the payload may include convenience keys such as `title`, `state`, or `description` without removing the native `fields` structure
- **AND** proposal import does not fail for a valid work item with `ADO work item must have fields`

#### Scenario: Selective ADO import derives a human-readable change ID when metadata is absent

- **GIVEN** an imported ADO work item has no existing OpenSpec change ID embedded in its description or comments
- **AND** the work item title is `Selective import keeps ADO payload`
- **WHEN** the adapter generates the OpenSpec change proposal during import
- **THEN** the resulting change ID is derived from the title as kebab-case
- **AND** the work item numeric ID remains in source tracking metadata instead of becoming the entire change name

#### Scenario: Duplicate title slug appends deterministic source suffix

- **GIVEN** a title-derived slug already exists in `openspec/changes/`
- **AND** another imported ADO work item with ID `123456` resolves to the same title slug
- **WHEN** the second proposal is created
- **THEN** the final change ID keeps the readable title slug and appends a deterministic suffix such as `-123456`
- **AND** the system does not fall back to using only the raw numeric work item ID as the change name
