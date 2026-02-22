# Backlog Map Fields (Multi-Provider Mapping Setup)

## ADDED Requirements

### Requirement: Backlog-scoped config scaffolding command

The system SHALL provide a backlog-scoped scaffolding command `specfact backlog init-config` that creates `.specfact/backlog-config.yaml` with safe defaults.

**Rationale**: Backlog mapping config should live under backlog command ownership and not require manual file creation.

#### Scenario: Initialize backlog config defaults

**Given**: User runs `specfact backlog init-config` in a repository

**When**: `.specfact/backlog-config.yaml` does not exist

**Then**: The command creates `.specfact/backlog-config.yaml` with minimal provider settings defaults

**And**: GitHub defaults do not include empty ProjectV2 id/option placeholders; ProjectV2 mapping is written only when configured

**And**: The command prints next steps for `specfact backlog map-fields`

#### Scenario: Initialize backlog config without overwrite

**Given**: `.specfact/backlog-config.yaml` already exists

**When**: User runs `specfact backlog init-config` without force option

**Then**: The command does not overwrite existing config and reports how to proceed safely

### Requirement: Multi-provider map-fields setup workflow

The system SHALL provide a provider-aware `specfact backlog map-fields` workflow that supports configuring mapping metadata for one or more backlog adapters in a single guided run.

**Rationale**: Users currently need different setup paths per provider and manual config edits for some providers. A unified setup flow prevents missing mappings and hidden fallback behavior.

#### Scenario: Select providers and run setup sequentially

**Given**: User runs `specfact backlog map-fields`

**When**: User selects one or more providers to configure (for example `ado` and `github`)

**Then**: The command executes setup for each selected provider in sequence

**And**: The command prints per-provider success/failure status with actionable next steps

### Requirement: Provider auth and field discovery checks

The system SHALL verify auth context and discover provider fields/metadata before accepting mappings.

#### Scenario: ADO mapping setup with API discovery

**Given**: ADO provider is selected

**When**: The command validates auth and loads ADO work item fields from API

**Then**: The user maps required canonical fields to available ADO fields

**And**: The command validates mapped field ids before saving

#### Scenario: GitHub ProjectV2 Type mapping setup with API discovery

**Given**: GitHub provider is selected

**When**: The command validates auth and loads ProjectV2 metadata (project, Type field, options)

**Then**: The user maps canonical issue types (`epic`, `feature`, `story`, `task`, `bug`) to ProjectV2 Type options

**And**: The command validates selected option IDs before saving

#### Scenario: GitHub issue types are sourced from repository metadata

**Given**: GitHub provider is selected

**When**: The command loads repository issue types via GitHub GraphQL (`repository.issueTypes`)

**Then**: Canonical type mapping is derived from repository issue type names/ids (for example `epic`, `feature`, `story`, `task`, `bug`)

**And**: This source is preferred over ProjectV2 `Status` options for issue-type identity

#### Scenario: ProjectV2 type-option mapping is optional when Type field is absent

**Given**: GitHub ProjectV2 has no Type-like single-select field (for example only `Status`)

**When**: The user runs `specfact backlog map-fields` for GitHub

**Then**: The command persists repository issue-type mappings and warns that ProjectV2 Type option mapping is skipped

**And**: The command does not fail solely because ProjectV2 Type options are unavailable

### Requirement: Canonical config persistence and verification

The system SHALL persist provider mapping outputs into canonical backlog config and verify integrity post-write.

#### Scenario: Persist provider mappings into .specfact/backlog-config.yaml

**Given**: User completes mapping flow for one or more providers

**When**: The command writes configuration

**Then**: Mappings are stored under `backlog_config.providers.<provider>.settings` in `.specfact/backlog-config.yaml`

**And**: Existing unrelated config keys are preserved

#### Scenario: Post-write verification and summary

**Given**: Mapping write completes

**When**: Verification runs

**Then**: The command confirms required keys are present and prints a concise summary of configured providers

**And**: If verification fails, the command reports the failing keys and exits non-zero
