## ADDED Requirements

### Requirement: Provider-Specific Rendering

The system SHALL render backlog item bodies into provider-specific formats when updating remote items.

#### Scenario: GitHub preserves Markdown

- **GIVEN** a BacklogItem with Markdown body
- **WHEN** the GitHub adapter updates the issue body
- **THEN** the Markdown is sent as-is.

#### Scenario: ADO renders Markdown safely

- **GIVEN** a BacklogItem with Markdown body
- **WHEN** the ADO adapter updates the work item description
- **THEN** the adapter sets the field format to Markdown where supported
- **AND** uses `/multilineFieldsFormat/System.Description` with value `Markdown`
- **AND** converts Markdown to HTML when Markdown format is not accepted.

#### Scenario: Round-trip format metadata

- **GIVEN** a provider-specific render step is applied
- **WHEN** the update succeeds
- **THEN** the adapter records the original Markdown and render format in `provider_fields`
- **AND** round-trip sync preserves the original Markdown source.
