## MODIFIED Requirements

### Requirement: BacklogAdapter Interface

The system SHALL provide a standard `BacklogAdapter` interface that all backlog sources (GitHub, ADO, JIRA, GitLab, etc.) must implement.

#### Scenario: Selective proposal import preserves provider-native payload

- **GIVEN** an adapter supports selective backlog import by explicit item reference
- **WHEN** bridge sync fetches one item through `fetch_backlog_item()` and passes the result into proposal import
- **THEN** the fetched artifact preserves the provider-native fields required by `extract_change_proposal_data()` or `import_artifact()`
- **AND** adapter-specific convenience fields may be added without discarding the native structure
- **AND** contract tests cover the `fetch_backlog_item()` to `import_artifact()` round trip for supported adapters

#### Scenario: Imported proposal IDs normalize title-first across adapters

- **GIVEN** an imported backlog artifact has no embedded OpenSpec change ID metadata
- **AND** the source artifact has a usable human-readable title
- **WHEN** the adapter or shared backlog import path constructs the proposal change ID
- **THEN** the change ID is derived from a normalized title slug
- **AND** a numeric provider ID is used only as source tracking metadata or as a deterministic suffix when needed for uniqueness
- **AND** the system does not default to a numeric-only change name while a usable title is available
