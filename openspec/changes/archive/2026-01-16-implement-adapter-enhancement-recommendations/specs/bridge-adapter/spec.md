## ADDED Requirements

### Requirement: Backlog Adapter Extensibility Pattern

The bridge adapter architecture SHALL provide reusable patterns and abstractions that enable easy implementation of future backlog adapters (Azure DevOps/ADO, Jira, Linear, etc.) following the same patterns as the GitHub adapter implementation.

#### Scenario: Future backlog adapters follow established patterns

- **WHEN** a new backlog adapter is implemented (ADO, Jira, Linear, etc.)
- **THEN** it follows the same import/export patterns as GitHub adapter
- **AND** it uses the same tool-agnostic status mapping interface
- **AND** it uses the same tool-agnostic metadata extraction interface
- **AND** it stores tool-specific metadata in `source_tracking` only
- **AND** it respects `bridge_config.external_base_path` for cross-repo support

### Requirement: Backlog Adapter Import Capability

The bridge adapter architecture SHALL support importing backlog items (issues, work items, tickets) from backlog management tools as OpenSpec change proposals. GitHub is the first implementation; the pattern must be extensible for future backlog adapters (Azure DevOps/ADO, Jira, Linear, etc.).

#### Scenario: Import backlog item as change proposal (GitHub first)

- **WHEN** a backlog item is imported via `import_artifact("github_issue", issue_data, project_bundle, bridge_config)` (GitHub)
- **OR** via `import_artifact("ado_work_item", ...)` (future: Azure DevOps)
- **OR** via `import_artifact("jira_issue", ...)` (future: Jira)
- **OR** via `import_artifact("linear_issue", ...)` (future: Linear)
- **THEN** the backlog item body is parsed to extract change proposal data (title, description, rationale)
- **AND** backlog item status/labels are mapped to OpenSpec change status (tool-agnostic mapping)
- **AND** backlog item metadata (ID, URL, status, assignees) is stored in `source_tracking` (tool-agnostic pattern)

#### Scenario: Handle missing or malformed backlog item data

- **WHEN** backlog item data is missing required fields or malformed (any backlog adapter)
- **THEN** the import method raises `ValueError` with descriptive error message
- **AND** no change proposal is created

#### Scenario: Map backlog status to OpenSpec status (tool-agnostic pattern)

- **WHEN** backlog item has status "enhancement" or "new" or "todo" (GitHub label, ADO state, Jira status, Linear state)
- **THEN** OpenSpec change status is set to "proposed"
- **WHEN** backlog item has status "in-progress" or "active" or "in development"
- **THEN** OpenSpec change status is set to "in-progress"
- **WHEN** backlog item has status "done" or "closed" or "completed"
- **THEN** OpenSpec change status is set to "applied"
- **NOTE**: Status mapping must be tool-agnostic and configurable for future backlog adapters

### Requirement: Bidirectional Status Synchronization

Backlog adapters SHALL support bidirectional synchronization of change status between OpenSpec and backlog management tools. GitHub is the first implementation; the pattern must be extensible for future backlog adapters (ADO, Jira, Linear, etc.).

#### Scenario: Sync OpenSpec status to backlog status (tool-agnostic)

- **WHEN** OpenSpec change proposal status changes to "in-progress"
- **THEN** corresponding backlog item status is updated (GitHub labels, ADO state, Jira status, Linear state)
- **AND** previous status is removed/updated
- **NOTE**: Status sync pattern must be tool-agnostic and reusable for future backlog adapters

#### Scenario: Sync backlog status to OpenSpec status (tool-agnostic)

- **WHEN** backlog item status changes (e.g., GitHub "enhancement" → "in-progress", ADO "New" → "Active", Jira "To Do" → "In Progress", Linear "Backlog" → "In Progress")
- **THEN** corresponding OpenSpec change proposal status is updated
- **AND** change tracking is saved back to OpenSpec

#### Scenario: Handle status conflicts (tool-agnostic)

- **WHEN** OpenSpec status and backlog item status differ (any backlog adapter)
- **THEN** conflict resolution strategy is applied (prefer OpenSpec status or user-defined strategy)
- **AND** both systems are synchronized

### Requirement: Validation Integration with Change Proposals

The SpecFact validation command SHALL integrate with OpenSpec change proposals to validate against proposed specifications.

#### Scenario: Load active change proposals during validation

- **WHEN** `specfact validate` command is executed in a repository with OpenSpec
- **THEN** active change proposals (status: "proposed" or "in-progress") are loaded
- **AND** associated spec deltas are extracted from change proposals

#### Scenario: Merge specs for validation

- **WHEN** active change proposals contain spec deltas
- **THEN** current Spec-Kit specs are merged with proposed OpenSpec changes
- **AND** ADDED requirements are included in validation set
- **AND** MODIFIED requirements replace existing requirements
- **AND** REMOVED requirements are excluded from validation set

#### Scenario: Update validation status in change proposals

- **WHEN** validation completes for a change proposal
- **THEN** `validation_status` in `FeatureDelta` is updated ("passed" or "failed")
- **AND** `validation_results` are stored with detailed validation output
- **AND** updated change tracking is saved back to OpenSpec

#### Scenario: Report validation results to backlog (tool-agnostic)

- **WHEN** validation completes and a backlog adapter is configured (GitHub, future: ADO, Jira, Linear)
- **THEN** validation results are reported to corresponding backlog item
- **AND** backlog item comments/notes are updated with validation status
- **AND** backlog item status/labels are updated based on validation status
- **NOTE**: Reporting pattern must be tool-agnostic and reusable for future backlog adapters

## MODIFIED Requirements

### Requirement: Backlog Adapter Export and Import Capability

Backlog adapters SHALL support exporting OpenSpec change proposals to backlog management tools, **AND** importing backlog items as OpenSpec change proposals. GitHub is the first implementation; the pattern must be extensible for future backlog adapters (ADO, Jira, Linear, etc.).

#### Scenario: Export change proposal to backlog (tool-agnostic)

- **WHEN** a change proposal is exported via `export_artifact("change_proposal", proposal, bridge_config)`
- **THEN** a backlog item is created (GitHub issue, ADO work item, Jira issue, Linear issue)
- **AND** backlog item title and description are set from proposal
- **AND** backlog item status is set based on OpenSpec change status (tool-agnostic mapping)
- **AND** backlog item metadata is stored in `source_tracking` (tool-agnostic pattern)

#### Scenario: Export and import maintain bidirectional sync

- **WHEN** a change proposal is exported to GitHub and then imported back
- **THEN** the imported proposal matches the original proposal
- **AND** bidirectional sync is maintained
