## ADDED Requirements

### Requirement: BacklogAdapter Interface

The system SHALL provide a standard `BacklogAdapter` interface that all backlog sources (GitHub, ADO, JIRA, GitLab, etc.) must implement.

#### Scenario: Adapter implements standard contract

- **WHEN** a new backlog adapter is created
- **THEN** it inherits from `BacklogAdapter` and implements `name()`, `supports_format()`, `fetch_backlog_items()`, and `update_backlog_item()`

#### Scenario: Fetch items with filters

- **WHEN** `fetch_backlog_items(filters: BacklogFilters)` is called
- **THEN** the adapter returns a list of `BacklogItem` objects matching the filters

#### Scenario: Update item with selective fields

- **WHEN** `update_backlog_item(item: BacklogItem, update_fields: Optional[List[str]])` is called
- **THEN** the adapter updates only the specified fields (or all fields if update_fields is None) and returns the updated item

#### Scenario: Round-trip validation

- **WHEN** `validate_round_trip(original: BacklogItem, updated: BacklogItem)` is called
- **THEN** the system verifies that id, title, body_markdown, and state are preserved

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
