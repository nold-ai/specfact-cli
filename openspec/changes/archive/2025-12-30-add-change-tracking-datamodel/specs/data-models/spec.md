# Data Models Capability

## ADDED Requirements

### Requirement: Change Tracking Models

The system SHALL provide tool-agnostic change tracking models to support delta spec tracking (ADDED/MODIFIED/REMOVED) and change proposals.

#### Scenario: Create Change Proposal Model

- **GIVEN** a change proposal needs to be tracked
- **WHEN** a `ChangeProposal` model is instantiated
- **THEN** the model includes fields for:
  - Change identifier (name)
  - Title and description (what)
  - Rationale (why)
  - Timeline and dependencies (when)
  - Owner and stakeholders (who)
  - Status (proposed, in-progress, applied, archived)
  - Timestamps (created_at, applied_at, archived_at)
  - Tool-specific metadata via `source_tracking`

#### Scenario: Create Feature Delta Model

- **GIVEN** a feature change needs to be tracked
- **WHEN** a `FeatureDelta` model is instantiated
- **THEN** the model includes fields for:
  - Feature key
  - Change type (ADDED, MODIFIED, REMOVED)
  - Original feature (for MODIFIED/REMOVED)
  - Proposed feature (for ADDED/MODIFIED)
  - Change rationale
  - Validation status and results
  - Tool-specific metadata via `source_tracking`

#### Scenario: Create Change Tracking Container

- **GIVEN** multiple change proposals need to be managed
- **WHEN** a `ChangeTracking` model is instantiated
- **THEN** the model includes:
  - Dictionary of change proposals (name → ChangeProposal)
  - Dictionary of feature deltas per change (change_name → [FeatureDelta])
  - No tool-specific fields (all tool metadata in `source_tracking`)

#### Scenario: Create Change Archive Model

- **GIVEN** a completed change needs to be archived
- **WHEN** a `ChangeArchive` model is instantiated
- **THEN** the model includes fields for:
  - Change name
  - Applied timestamp and user
  - PR number and commit hash (if applicable)
  - Feature deltas that were applied
  - Validation results
  - Tool-specific metadata via `source_tracking`

### Requirement: BundleManifest Extension

The system SHALL extend `BundleManifest` with optional change tracking fields for schema v1.1.

#### Scenario: Add Change Tracking to BundleManifest

- **GIVEN** a bundle manifest needs change tracking support
- **WHEN** schema version is v1.1
- **THEN** `BundleManifest` includes optional fields:
  - `change_tracking: ChangeTracking | None` (default None)
  - `change_archive: list[ChangeArchive]` (default empty list)
  - Fields are backward compatible (v1.0 bundles load correctly)

#### Scenario: Backward Compatibility

- **GIVEN** an existing v1.0 bundle
- **WHEN** the bundle is loaded
- **THEN** `change_tracking` and `change_archive` are None/empty
- **AND** no errors occur
- **AND** all existing functionality continues to work

### Requirement: ProjectBundle Extension

The system SHALL extend `ProjectBundle` with optional change tracking and helper methods.

#### Scenario: Add Change Tracking to ProjectBundle

- **GIVEN** a project bundle needs change tracking support
- **WHEN** schema version is v1.1
- **THEN** `ProjectBundle` includes:
  - Optional `change_tracking: ChangeTracking | None` field
  - `get_active_changes()` helper method (returns list of non-archived proposals)
  - `get_feature_deltas(change_name: str)` helper method (returns deltas for specific change)

#### Scenario: Query Active Changes

- **GIVEN** a project bundle with change tracking
- **WHEN** `get_active_changes()` is called
- **THEN** returns list of `ChangeProposal` objects with status "proposed" or "in-progress"
- **AND** excludes archived changes

#### Scenario: Query Feature Deltas

- **GIVEN** a project bundle with change tracking
- **WHEN** `get_feature_deltas(change_name)` is called
- **THEN** returns list of `FeatureDelta` objects for the specified change
- **AND** returns empty list if change not found
- **AND** returns empty list if `change_tracking` is None
- **AND** handles invalid `change_name` gracefully (returns empty list)

#### Scenario: Helper Method - get_active_changes() Detailed Behavior

- **GIVEN** a project bundle with change tracking containing multiple proposals
- **WHEN** `get_active_changes()` is called
- **THEN** returns list of `ChangeProposal` objects
- **AND** includes only proposals with status "proposed" or "in-progress"
- **AND** excludes proposals with status "applied" or "archived"
- **AND** returns empty list if no active changes exist
- **AND** returns empty list if `change_tracking` is None
- **AND** preserves original order of proposals

#### Scenario: Helper Method - get_feature_deltas() Detailed Behavior

- **GIVEN** a project bundle with change tracking containing feature deltas
- **WHEN** `get_feature_deltas(change_name)` is called with valid change name
- **THEN** returns list of `FeatureDelta` objects for the specified change
- **AND** preserves order of deltas
- **WHEN** `get_feature_deltas(change_name)` is called with invalid change name
- **THEN** returns empty list
- **WHEN** `get_feature_deltas(change_name)` is called when `change_tracking` is None
- **THEN** returns empty list

### Requirement: Schema Version Support

The system SHALL support schema version v1.1 with backward compatibility for v1.0.

#### Scenario: Load v1.1 Bundle

- **GIVEN** a bundle with schema version v1.1
- **WHEN** the bundle is loaded
- **THEN** change tracking fields are loaded if present
- **AND** bundle loads successfully

#### Scenario: Load v1.0 Bundle

- **GIVEN** a bundle with schema version v1.0
- **WHEN** the bundle is loaded
- **THEN** change tracking fields are None/empty
- **AND** bundle loads successfully
- **AND** no errors occur

#### Scenario: Schema Migration

- **GIVEN** a v1.0 bundle
- **WHEN** migration to v1.1 is requested
- **THEN** schema version is updated to "1.1"
- **AND** change tracking structure is initialized (empty)
- **AND** all existing data is preserved

### Requirement: Tool-Agnostic Design

The system SHALL ensure change tracking models are tool-agnostic and accessed via bridge adapters.

#### Scenario: Tool Metadata Storage

- **GIVEN** a change proposal from OpenSpec
- **WHEN** the proposal is stored
- **THEN** OpenSpec-specific paths stored in `source_tracking.source_metadata`
- **AND** no OpenSpec-specific fields in `ChangeProposal` model
- **AND** model remains tool-agnostic

#### Scenario: Adapter-Based Access

- **GIVEN** change tracking needs to be loaded
- **WHEN** loading from OpenSpec
- **THEN** `OpenSpecAdapter.load_change_tracking()` is called
- **AND** adapter decides storage location (not hard-coded in core)
- **AND** adapter handles OpenSpec-specific paths
- **AND** adapter checks `bridge_config.external_base_path` for cross-repo support
- **AND** adapter resolves paths relative to external base when provided

#### Scenario: Cross-Repository Support

- **GIVEN** OpenSpec artifacts in `specfact-cli-internal` repository
- **AND** code being analyzed in `specfact-cli` repository
- **WHEN** change tracking is loaded via adapter
- **THEN** adapter uses `bridge_config.external_base_path` to locate OpenSpec artifacts
- **AND** all paths resolved relative to external base
- **AND** change tracking loads successfully from cross-repository location
- **AND** works transparently (same interface as same-repo scenario)

#### Scenario: Future Tool Support

- **GIVEN** a future tool (e.g., Linear) supports change tracking
- **WHEN** change tracking models are used
- **THEN** same models work for Linear
- **AND** Linear-specific metadata stored in `source_tracking`
- **AND** no model changes required
