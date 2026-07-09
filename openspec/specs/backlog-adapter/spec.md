# backlog-adapter Specification

## Purpose

TBD - created by archiving change add-generic-backlog-abstraction. Update Purpose after archive.

## Requirements

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

### Requirement: Adapter Extensibility

The system SHALL enable new backlog adapters to be added with minimal code (<500 LOC) without modifying existing adapters or core logic.

#### Scenario: Add new adapter (JIRA example)

- **WHEN** a developer wants to add JIRA support
- **THEN** they create a new class inheriting from `BacklogAdapter`, implement required methods, and register it (~300 LOC)

#### Scenario: New adapter works with existing features

- **WHEN** a new adapter is added
- **THEN** template detection (Plan A) and bundle mapping (Plan C) work automatically with the new adapter

### Requirement: Backward Compatibility

The system SHALL maintain backward compatibility when refactoring existing adapters to use the new interface.

#### Scenario: GitHub adapter refactoring

- **WHEN** GitHub adapter is refactored to inherit from `BacklogAdapter`
- **THEN** all existing functionality remains unchanged, and existing tests continue to pass

#### Scenario: ADO adapter refactoring

- **WHEN** ADO adapter is refactored to inherit from `BacklogAdapter`
- **THEN** all existing functionality remains unchanged, and existing tests continue to pass

#### Scenario: Lossless round-trip after refactoring

- **WHEN** existing adapters are refactored
- **THEN** round-trip tests confirm zero data loss (GitHub issue → BacklogItem → GitHub issue)

### Requirement: Backlog module provides bridge converters for supported services

The system SHALL provide backlog bridge converters for Azure DevOps, Jira, Linear, and GitHub using the shared bridge registry contract.

#### Scenario: Backlog module declares service bridges in manifest

- **WHEN** backlog module package metadata is discovered
- **THEN** manifest `service_bridges` SHALL declare converter entries for `ado`, `jira`, `linear`, and `github`
- **AND** each entry SHALL reference a converter class path under backlog adapters.

#### Scenario: Backlog converters satisfy schema converter contract

- **WHEN** bridge converters are loaded
- **THEN** each converter SHALL implement `to_bundle` and `from_bundle` operations
- **AND** conversion behavior SHALL preserve required backlog fields for round-trip workflows.

### Requirement: Backlog bridge mappings support custom enterprise overrides

The system SHALL allow custom bridge field mappings for backlog converter workflows.

#### Scenario: Custom mapping file overrides default mapping

- **WHEN** a custom mapping YAML exists for a configured service bridge
- **THEN** backlog converter behavior SHALL apply custom mapping before default mapping
- **AND** fallback to defaults when custom mappings are absent or incomplete.

#### Scenario: Invalid custom mapping falls back safely

- **WHEN** custom mapping configuration is malformed
- **THEN** converter execution SHALL continue with default mapping behavior
- **AND** SHALL emit warning/debug context for troubleshooting.

### Requirement: Source-Attributed Backlog Requirement Snippets

The system SHALL define source-attributed backlog requirement snippets that
requirements runtime adapters can normalize without provider-specific parsing in
core command handlers.

#### Scenario: Adapter returns source fields for requirement context import

- **GIVEN** a backlog item selected for requirement context import
- **WHEN** the requirements adapter receives source fields
- **THEN** the adapter can return title, description, acceptance-criteria text, and item identity
- **AND** normalization proceeds without provider-specific parsing in core helpers.

#### Scenario: Missing acceptance criteria is surfaced explicitly

- **GIVEN** a backlog item with no acceptance criteria
- **WHEN** requirements context normalization runs
- **THEN** the item is reported as incomplete input
- **AND** diagnostics include the backlog item identifier.
