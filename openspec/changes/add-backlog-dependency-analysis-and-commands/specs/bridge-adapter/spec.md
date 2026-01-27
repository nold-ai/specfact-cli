# bridge-adapter Specification

## Purpose

The bridge adapter architecture provides a universal abstraction layer for integrating SpecFact with external tools and formats, including specification tools (Spec-Kit, OpenSpec), backlog management tools (GitHub Issues, Azure DevOps, Jira, Linear), and validation systems. The architecture uses a plugin-based adapter registry pattern that enables extensibility for future tool integrations while maintaining clean separation of concerns.

## Requirements

## ADDED Requirements

### Requirement: Backlog Adapter Bulk Fetching Methods

The system SHALL extend `BacklogAdapterMixin` with abstract methods for bulk fetching backlog items and relationships to support dependency graph analysis.

#### Scenario: Implement bulk fetching in adapters

- **GIVEN** `BacklogAdapterMixin` is extended with abstract methods for bulk fetching
- **WHEN** a backlog adapter (GitHub, ADO) implements `BacklogAdapterMixin`
- **THEN** adapter must implement `fetch_all_issues(project_id: str, filters: dict | None = None) -> list[dict[str, Any]]` abstract method
- **AND** adapter must implement `fetch_relationships(project_id: str) -> list[dict[str, Any]]` abstract method
- **AND** `GitHubAdapter` implements `fetch_all_issues()` using GitHub API to fetch all issues from repository
- **AND** `GitHubAdapter` implements `fetch_relationships()` using GitHub API to fetch issue links and dependencies
- **AND** `AdoAdapter` implements `fetch_all_issues()` using ADO API to fetch all work items from project
- **AND** `AdoAdapter` implements `fetch_relationships()` using ADO API to fetch work item relations

### Requirement: Backlog Adapter Integration with Dependency Graph

The system SHALL support using backlog adapters (GitHub, ADO, Jira) to fetch raw backlog items and relationships for dependency graph analysis.

#### Scenario: Fetch backlog items for graph building

- **GIVEN** a backlog adapter (GitHub, ADO) is configured
- **WHEN** `BacklogGraphBuilder` needs to build a dependency graph
- **THEN** adapter's `fetch_all_issues(project_id: str, filters: dict | None = None) -> list[dict[str, Any]]` method is called to get all raw items
- **AND** adapter's `fetch_relationships(project_id: str) -> list[dict[str, Any]]` method is called to get all raw relationships
- **AND** raw data is passed to `BacklogGraphBuilder.add_items()` and `BacklogGraphBuilder.add_dependencies()`
- **AND** adapter-specific data is preserved in `BacklogItem.raw_data` field

#### Scenario: BacklogAdapterMixin extends with bulk fetching methods

- **GIVEN** `BacklogAdapterMixin` is extended with abstract methods for bulk fetching
- **WHEN** a backlog adapter (GitHub, ADO) implements `BacklogAdapterMixin`
- **THEN** adapter must implement `fetch_all_issues(project_id: str, filters: dict | None = None) -> list[dict[str, Any]]` abstract method
- **AND** adapter must implement `fetch_relationships(project_id: str) -> list[dict[str, Any]]` abstract method
- **AND** `GitHubAdapter` implements `fetch_all_issues()` using GitHub API to fetch all issues from repository
- **AND** `GitHubAdapter` implements `fetch_relationships()` using GitHub API to fetch issue links and dependencies
- **AND** `AdoAdapter` implements `fetch_all_issues()` using ADO API to fetch all work items from project
- **AND** `AdoAdapter` implements `fetch_relationships()` using ADO API to fetch work item relations

#### Scenario: Use adapter registry for graph building

- **GIVEN** backlog dependency analysis commands need to fetch data
- **WHEN** `specfact backlog analyze-deps --adapter github --project-id owner/repo` is executed
- **THEN** `AdapterRegistry.get_adapter("github")` is used to retrieve GitHub adapter
- **AND** adapter's `fetch_all_issues(project_id)` and `fetch_relationships(project_id)` methods are called
- **AND** no hard-coded adapter checks are used in graph building logic
- **AND** adapter methods return lists of dicts with raw provider data

#### Scenario: Support cross-adapter graph analysis

- **GIVEN** backlog items exist in multiple providers (GitHub and ADO)
- **WHEN** dependency analysis is performed across providers
- **THEN** each provider's adapter is used to fetch items
- **AND** items from different providers are unified into single `BacklogGraph`
- **AND** provider information is preserved in `BacklogItem.raw_data` and `BacklogGraph.provider`

### Requirement: Template-Driven Mapping for Adapters

The system SHALL support provider-specific templates for mapping adapter data to unified dependency graph model.

#### Scenario: Use ADO template for ADO adapter

- **GIVEN** ADO adapter is used with `--template ado_scrum`
- **WHEN** `BacklogGraphBuilder` processes ADO work items
- **THEN** ADO-specific template rules are applied (WorkItemType → ItemType mapping, relation types → DependencyType mapping)
- **AND** ADO state values are mapped to normalized status values
- **AND** ADO-specific fields are preserved in `raw_data`

#### Scenario: Use GitHub template for GitHub adapter

- **GIVEN** GitHub adapter is used with `--template github_projects`
- **WHEN** `BacklogGraphBuilder` processes GitHub issues
- **THEN** GitHub-specific template rules are applied (labels → ItemType mapping, linked issues → DependencyType mapping)
- **AND** GitHub state values are mapped to normalized status values
- **AND** GitHub-specific fields are preserved in `raw_data`

#### Scenario: Custom template overrides adapter defaults

- **GIVEN** a user provides custom YAML config with type mapping overrides
- **WHEN** `BacklogGraphBuilder` is initialized with custom config
- **THEN** custom rules override template rules
- **AND** adapter-specific data is still accessible via `raw_data`
- **AND** unified graph model is used regardless of adapter
