## ADDED Requirements

### Requirement: Azure DevOps Backlog Adapter

The system SHALL provide an Azure DevOps backlog adapter that implements the BridgeAdapter interface and BacklogAdapterMixin patterns to synchronize OpenSpec change proposals with ADO work items.

#### Scenario: Register ADO adapter

- **WHEN** the adapter registry is initialized
- **THEN** the ADO adapter is registered with key "ado"
- **AND** AdapterType.ADO is used for bridge configuration
- **AND** `specfact sync bridge --adapter ado` selects the adapter

#### Scenario: Generate bridge config for ADO

- **WHEN** `AdoAdapter.generate_bridge_config()` is called
- **THEN** it returns a `BridgeConfig` with `adapter = AdapterType.ADO`
- **AND** it includes artifact mappings for `change_proposal` and `change_status`
- **AND** ADO credentials are supplied via environment variables or CLI options, not stored in BridgeConfig

#### Scenario: Export change proposal to ADO work item

- **WHEN** `export_artifact("change_proposal", proposal, bridge_config)` is executed
- **THEN** an ADO work item is created or updated idempotently
- **AND** the work item title and description are derived from the proposal (Why/What Changes/Impact)
- **AND** the ADO work item state is set using the OpenSpec status mapping
- **AND** ADO metadata (work item id, URL, state, org, project) is stored in `source_tracking`

#### Scenario: Import ADO work item as change proposal

- **WHEN** `import_artifact("ado_work_item", work_item_data, project_bundle, bridge_config)` is executed
- **THEN** proposal fields are extracted from ADO work item fields (title, description, state)
- **AND** ADO state is mapped to an OpenSpec status using tool-agnostic mapping
- **AND** malformed or missing fields raise `ValueError` and no proposal is created
- **AND** backlog items are imported only when explicitly selected (no automatic bulk import)

#### Scenario: Synchronize status between OpenSpec and ADO

- **WHEN** an OpenSpec proposal status changes
- **THEN** the corresponding ADO work item state is updated
- **WHEN** an ADO work item state changes
- **THEN** the OpenSpec proposal status is updated using conflict resolution strategy

### Requirement: Azure DevOps Status Mapping and Configuration

The system SHALL support configurable mapping between OpenSpec statuses and ADO work item states, with defaults aligned to backlog adapter patterns.

#### Scenario: Default status mapping

- **WHEN** OpenSpec status is "proposed"
- **THEN** ADO state maps to "New"
- **WHEN** OpenSpec status is "in-progress"
- **THEN** ADO state maps to "Active"
- **WHEN** OpenSpec status is "applied"
- **THEN** ADO state maps to "Closed"
- **WHEN** OpenSpec status is "deprecated"
- **THEN** ADO state maps to "Removed"
- **WHEN** OpenSpec status is "discarded"
- **THEN** ADO state maps to "Rejected"

#### Scenario: Override status mapping

- **WHEN** a custom mapping is provided via configuration
- **THEN** the adapter uses the configured mapping instead of defaults

#### Scenario: Cross-repo support

- **WHEN** `bridge_config.external_base_path` is set
- **THEN** ADO adapter uses the external path for OpenSpec reads and writes

### Requirement: Azure DevOps Work Item Type Defaults

The system SHALL derive the default ADO work item type from the process template (Scrum/Kanban/Agile) and allow explicit overrides.

#### Scenario: Derive work item type from Scrum template

- **WHEN** the ADO process template is Scrum
- **THEN** the default work item type is "Product Backlog Item"

#### Scenario: Derive work item type from Agile template

- **WHEN** the ADO process template is Agile
- **THEN** the default work item type is "User Story"

#### Scenario: Derive work item type from Kanban workflow

- **WHEN** the ADO process template is Kanban
- **THEN** the default work item type is "User Story"

#### Scenario: Override work item type

- **WHEN** an explicit work item type is provided via configuration
- **THEN** the adapter uses the configured work item type
