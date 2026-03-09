# backlog-map-fields Specification

## Purpose
TBD - created by archiving change backlog-core-05-user-modules-bootstrap. Update Purpose after archive.
## Requirements
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

#### Scenario: ADO mapping persists required custom fields per work item type

- **GIVEN** ADO provider mapping setup is requested for a selected work item type
- **AND** ADO field metadata contains custom fields marked required for that work item type
- **WHEN** `specfact backlog map-fields` persists ADO field mappings
- **THEN** `.specfact/backlog-config.yaml` stores required custom field metadata for the mapped work item type
- **AND** the metadata is available to `specfact backlog add` validation before create.

#### Scenario: ADO mapping persists allowed values for constrained list fields

- **GIVEN** a mapped ADO field has constrained picklist values
- **WHEN** `specfact backlog map-fields` persists ADO mapping metadata
- **THEN** the mapping stores eligible values for that field
- **AND** add-time flows can validate user input against those values in interactive and non-interactive modes.

#### Scenario: Interactive mapping reports selected-type metadata fetch progress

- **GIVEN** the user selected an ADO work item type during `specfact backlog map-fields`
- **WHEN** the command fetches required-field metadata and follow-up allowed-value or picklist details for that selected type
- **THEN** the CLI prints status output before the next prompt gap
- **AND** when multiple metadata items are resolved the status output includes incremental `N/M` progress for the pending items.

#### Scenario: Built-in required hierarchy identifiers do not block successful mapping

- **GIVEN** the selected ADO work item type marks built-in hierarchy identifiers such as `System.IterationId` or `System.AreaId` as required
- **AND** those identifiers are system-managed and not valid interactive mapping targets
- **WHEN** `specfact backlog map-fields` validates required-field metadata before saving mappings
- **THEN** the command does not require explicit user mappings for those built-in identifiers
- **AND** mapping still succeeds when every actually mappable required field is resolved.

#### Scenario: Non-interactive map-fields auto-maps or fails with interactive guidance

- **GIVEN** the user runs `specfact backlog map-fields` in non-interactive mode
- **WHEN** provider metadata can resolve canonical and required custom fields deterministically
- **THEN** mapping and metadata are persisted without prompts
- **AND** the command exits successfully.

#### Scenario: Non-interactive map-fields fails when auto-mapping is incomplete

- **GIVEN** the user runs non-interactive `specfact backlog map-fields`
- **AND** one or more required fields cannot be mapped automatically
- **WHEN** validation runs before persistence
- **THEN** the command exits non-zero
- **AND** the error explicitly lists unresolved fields and instructs the user to run interactive `specfact backlog map-fields`.
