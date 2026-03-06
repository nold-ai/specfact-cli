## ADDED Requirements

### Requirement: Marketplace Backlog Commands Must Interoperate With Core Backlog Adapters

The system SHALL allow the published `nold-ai/specfact-backlog` marketplace bundle to operate against the built-in core backlog adapters without runtime interface mismatches.

#### Scenario: Refine command accepts the core ADO adapter

- **GIVEN** `backlog-core` and `nold-ai/specfact-backlog` are both installed in a normal user environment
- **AND** the user invokes `specfact backlog refine ado` with valid ADO adapter configuration
- **WHEN** the backlog bundle resolves the adapter from the shared registry
- **THEN** it accepts the returned core adapter instance as a valid backlog adapter
- **AND** it proceeds to fetch backlog items instead of failing with `Adapter ado does not implement BacklogAdapter interface`.

#### Scenario: Expected backlog command overlap stays quiet in normal startup

- **GIVEN** the built-in `backlog-core` module and the published `nold-ai/specfact-backlog` bundle both contribute to the public `backlog` command surface by design
- **WHEN** a user runs a normal `specfact backlog ...` command without `--debug`
- **THEN** expected overlap handling does not emit duplicate-subcommand warnings
- **AND** only unexpected or actionable ownership conflicts remain visible.

### Requirement: Map-Fields Must Show Progress After Work Item Type Selection

The system SHALL keep the interactive `backlog map-fields` flow responsive and observable while it resolves required-field and picklist metadata for the selected work item type.

#### Scenario: Interactive mapping reports metadata fetch progress

- **GIVEN** the user selected an ADO work item type during `specfact backlog map-fields`
- **WHEN** the command fetches work-item-type field metadata and follow-up allowed-value or picklist data
- **THEN** the CLI emits progress or status text before the next prompt gap
- **AND** the command does not appear to stop silently after the work item type selection.

#### Scenario: Selected work item type metadata is persisted for later create-time validation

- **GIVEN** `specfact backlog map-fields` completes successfully for a selected ADO work item type
- **WHEN** the command writes provider configuration
- **THEN** it persists the selected work item type, required fields for that type, and any allowed-value metadata needed for downstream validation
- **AND** later backlog creation flows can consume that metadata without re-running `map-fields`.

### Requirement: Backlog Add Must Enforce Saved Provider Metadata

The system SHALL use saved custom-field mapping metadata from `backlog map-fields` when creating backlog items through the built-in `backlog add` flow.

#### Scenario: Backlog add exposes custom field input for mapped provider fields

- **GIVEN** provider settings include saved required or optional custom field mappings for the selected backlog adapter and work item type
- **WHEN** the user runs `specfact backlog add`
- **THEN** the command accepts repeatable `--custom-field <canonical-or-provider-key>=<value>` options
- **AND** it forwards the resolved provider-specific custom field values to the adapter create payload.

#### Scenario: Backlog add rejects missing required custom fields with guidance

- **GIVEN** provider settings mark one or more custom fields as required for the selected work item type
- **WHEN** the user omits one of those required custom fields during `specfact backlog add`
- **THEN** the command fails before the adapter create call
- **AND** the error identifies the missing field and tells the user how to supply it.

#### Scenario: Backlog add rejects invalid picklist values with allowed options

- **GIVEN** provider settings include allowed values for a mapped custom field on the selected work item type
- **WHEN** the user supplies a value outside the allowed set during `specfact backlog add`
- **THEN** the command fails before the adapter create call
- **AND** the error lists the accepted values for that field.
