## ADDED Requirements

### Requirement: Provider auth and field discovery checks

The system SHALL verify auth context and discover provider fields/metadata before accepting mappings.

#### Scenario: GitHub mapping fails when repository issue types are unavailable

- **GIVEN** GitHub provider mapping setup is requested
- **AND** repository issue types cannot be discovered (API failure, missing scope, or empty response)
- **WHEN** `specfact backlog map-fields` runs
- **THEN** the command exits non-zero with actionable guidance
- **AND** it does not report successful GitHub type mapping persistence.

#### Scenario: GitHub mapping persists repository issue-type IDs for add flow

- **GIVEN** repository issue types are discovered from GitHub metadata
- **WHEN** `specfact backlog map-fields` persists GitHub settings
- **THEN** `.specfact/backlog-config.yaml` includes `backlog_config.providers.github.settings.github_issue_types.type_ids`
- **AND** subsequent `specfact backlog add` can consume those IDs for issue-type updates.

#### Scenario: GitHub ProjectV2 mapping is optional

- **GIVEN** GitHub repository issue types are successfully discovered
- **AND** the user leaves GitHub ProjectV2 input empty
- **WHEN** `specfact backlog map-fields` runs
- **THEN** the command succeeds and persists repository issue-type IDs
- **AND** ProjectV2 field mapping is skipped without a hard failure.

#### Scenario: Blank ProjectV2 input clears stale ProjectV2 mapping

- **GIVEN** existing `backlog-config` contains stale `provider_fields.github_project_v2` values
- **AND** GitHub repository issue types are successfully discovered
- **WHEN** `specfact backlog map-fields` runs with blank ProjectV2 input
- **THEN** stale `provider_fields.github_project_v2` configuration is cleared
- **AND** subsequent `specfact backlog add` does not attempt ProjectV2 type-field updates from stale IDs.
