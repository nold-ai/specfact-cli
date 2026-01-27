## ADDED Requirements

### Requirement: Azure DevOps Backlog Sync Support

The system SHALL support Azure DevOps work items as a backlog adapter in the DevOps sync workflow.

#### Scenario: Export-only sync to ADO

- **WHEN** the user runs `specfact sync bridge --adapter ado --mode export-only`
- **THEN** change proposals are exported to ADO work items
- **AND** no ADO import operations are attempted

#### Scenario: Bidirectional sync with ADO

- **WHEN** the user runs `specfact sync bridge --adapter ado --mode bidirectional`
- **THEN** change proposals are exported to ADO work items
- **AND** ADO work items are imported as OpenSpec change proposals
- **AND** status synchronization is applied in both directions

### Requirement: Azure DevOps Sync Configuration

The system SHALL use explicit Azure DevOps configuration options for DevOps sync and derive sensible defaults when optional values are not provided.

#### Scenario: Configure ADO sync via explicit options

- **WHEN** the user provides `--ado-org`, `--ado-project`, `--ado-base-url`, `--ado-token`, and `--ado-work-item-type`
- **THEN** the adapter uses these values for all ADO API interactions
- **AND** secrets are not persisted in BridgeConfig

#### Scenario: Derive work item type from process template

- **WHEN** `--ado-work-item-type` is not provided
- **THEN** the adapter derives the default work item type from the process template
- **AND** Scrum defaults to "Product Backlog Item"
- **AND** Agile defaults to "User Story"
- **AND** Kanban defaults to "User Story"

### Requirement: Selective Backlog Import into Project Bundles

The system SHALL support importing selected backlog items into a project bundle without automatically importing all backlog items.

#### Scenario: Import specific backlog items by ID

- **WHEN** the user provides explicit backlog item IDs or URLs for import
- **THEN** only those items are imported into the target project bundle
- **AND** no other backlog items are imported

#### Scenario: Interactive backlog item selection

- **WHEN** the user runs sync in interactive mode without explicit IDs
- **THEN** the CLI prompts for backlog item selection
- **AND** only the selected items are imported into the target project bundle

#### Scenario: Non-interactive backlog item selection for AI copilot flows

- **WHEN** the user provides a non-interactive selection input (IDs list or input file)
- **THEN** the CLI imports only the specified backlog items
- **AND** the selection can be executed without prompts

#### Scenario: No selection provided

- **WHEN** no backlog item selection is provided
- **THEN** no backlog items are imported by default
