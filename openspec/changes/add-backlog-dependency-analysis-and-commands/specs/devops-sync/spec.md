# devops-sync Specification

## Purpose

TBD - created by archiving change add-devops-backlog-tracking. Update Purpose after archive.

## Requirements

## ADDED Requirements

### Requirement: Backlog Dependency Graph Analysis

The system SHALL support analyzing logical dependencies in backlog items (epic → feature → story → task hierarchies) using a provider-agnostic dependency graph model.

#### Scenario: Build dependency graph from backlog items

- **GIVEN** backlog items from a provider (GitHub, ADO, Jira)
- **WHEN** `BacklogGraphBuilder` processes the items with a template (ado_scrum, github_projects, jira_kanban)
- **THEN** items are converted to unified `BacklogItem` model with inferred types (epic, feature, story, task)
- **AND** dependencies are extracted as `Dependency` edges (parent_child, blocks, relates_to, implements)
- **AND** a `BacklogGraph` is built with items, dependencies, and analysis metadata
- **AND** graph includes transitive closure, cycles_detected, and orphans

#### Scenario: Analyze dependencies with custom template

- **GIVEN** a user provides custom YAML config to override template rules
- **WHEN** `BacklogGraphBuilder` is initialized with custom config
- **THEN** custom type mapping rules override built-in template rules
- **AND** custom dependency rules override built-in template rules
- **AND** custom status mapping rules override built-in template rules

#### Scenario: Detect circular dependencies

- **GIVEN** a backlog graph with circular dependencies (e.g., Task A blocks Task B, Task B blocks Task A)
- **WHEN** `DependencyAnalyzer.detect_cycles()` is called
- **THEN** all circular dependency chains are detected and returned
- **AND** cycles are stored in `graph.cycles_detected` as lists of item IDs

#### Scenario: Compute critical path

- **GIVEN** a backlog graph with dependency chains
- **WHEN** `DependencyAnalyzer.critical_path()` is called
- **THEN** the longest dependency chain is identified
- **AND** critical path is returned as a list of item IDs
- **AND** computation completes in < 1 second for graphs with 1000+ items

#### Scenario: Analyze impact of item changes

- **GIVEN** a backlog graph and a specific item ID
- **WHEN** `DependencyAnalyzer.impact_analysis(item_id)` is called
- **THEN** returns direct_dependents (items directly depending on this one)
- **AND** returns transitive_dependents (all items downstream)
- **AND** returns blockers (items blocking this one from completion)
- **AND** returns estimated_impact_count (total items affected)

### Requirement: Backlog Sync Command

The system SHALL provide a CLI command for synchronizing backlog state into SpecFact plan bundles with baseline comparison.

#### Scenario: Sync backlog to plan bundle

- **GIVEN** a backlog provider (GitHub, ADO) is configured
- **WHEN** user runs `specfact backlog sync --project-id owner/repo --adapter github --output-format plan`
- **THEN** adapter's `fetch_all_issues(project_id)` method is called to fetch all backlog items
- **AND** adapter's `fetch_relationships(project_id)` method is called to fetch all relationships
- **AND** dependency graph is built using `BacklogGraphBuilder` with fetched data
- **AND** graph is converted to plan bundle format
- **AND** plan bundle is saved to `.specfact/plans/backlog-<timestamp>.yaml` with `backlog_graph` field (optional, v1.2 format)
- **AND** plan bundle includes dependency graph data in `ProjectBundle.backlog_graph` field

#### Scenario: Sync with baseline comparison

- **GIVEN** a baseline file from previous sync exists (`.specfact/backlog-baseline.json` in JSON format)
- **WHEN** user runs `specfact backlog sync --project-id owner/repo --baseline-file .specfact/backlog-baseline.json`
- **THEN** baseline graph is loaded from JSON file using `BacklogGraph.from_json()` (JSON format for performance with large graphs)
- **AND** current graph is built using adapter's `fetch_all_issues()` and `fetch_relationships()` methods
- **AND** delta is computed comparing baseline vs current graph
- **AND** delta shows added, updated, deleted items
- **AND** delta shows new dependencies and status transitions

### Requirement: Backlog Delta Commands

The system SHALL provide CLI commands for analyzing backlog changes and their impact.

#### Scenario: Show backlog delta status

- **GIVEN** a backlog with changes since last sync
- **WHEN** user runs `specfact delta status --project-id owner/repo --adapter github`
- **THEN** shows new items (added)
- **AND** shows modified items (field changes)
- **AND** shows deleted items
- **AND** shows status transitions
- **AND** shows new dependencies

#### Scenario: Analyze delta impact

- **GIVEN** backlog changes have been detected
- **WHEN** user runs `specfact delta impact --project-id owner/repo --adapter github`
- **THEN** uses dependency graph to trace from changed items
- **AND** shows directly changed items count
- **AND** shows downstream affected items count
- **AND** shows total blast radius (changed + affected)

#### Scenario: Estimate delta cost

- **GIVEN** backlog changes have been detected
- **WHEN** user runs `specfact delta cost-estimate --project-id owner/repo --adapter github`
- **THEN** estimates effort of delta changes based on item types and dependencies
- **AND** provides effort breakdown by item type

#### Scenario: Analyze rollback impact

- **GIVEN** backlog changes have been detected
- **WHEN** user runs `specfact delta rollback-analysis --project-id owner/repo --adapter github`
- **THEN** analyzes what breaks if changes are reverted
- **AND** identifies dependent items that would be affected
- **AND** shows potential conflicts or blockers

### Requirement: Release Readiness Verification

The system SHALL provide a CLI command for verifying backlog items are ready for release.

#### Scenario: Verify release readiness

- **GIVEN** backlog items targeted for release
- **WHEN** user runs `specfact backlog verify-readiness --project-id owner/repo --adapter github --target-items "FEATURE-1,FEATURE-2"`
- **THEN** checks all blockers are resolved (no blocking items with open status)
- **AND** checks no circular dependencies exist
- **AND** checks all child items are completed (if parent specified)
- **AND** checks status transitions are valid
- **AND** exits with code 0 if ready, 1 if blockers found

#### Scenario: Verify readiness for all closed items

- **GIVEN** backlog items with status "closed" or "resolved"
- **WHEN** user runs `specfact backlog verify-readiness --project-id owner/repo --adapter github` (no target-items)
- **THEN** checks all closed/resolved items for blockers
- **AND** checks all closed/resolved items for incomplete children
- **AND** reports any issues found

### Requirement: Project Backlog Integration

The system SHALL support linking projects to backlog providers and integrating backlog features into project workflows.

#### Scenario: Link project to backlog provider

- **GIVEN** a SpecFact project exists with `ProjectBundle`
- **WHEN** user runs `specfact project link-backlog --project-name my-project --adapter github --project-id owner/repo`
- **THEN** backlog configuration is stored in `ProjectBundle.metadata.backlog_config` field (not separate config file):

  ```python
  bundle.metadata.backlog_config = {
      "adapter": "github",
      "project_id": "owner/repo"
  }
  ```

- **AND** bundle is saved with updated metadata (atomic write)
- **AND** backlog commands auto-use this project's backlog configuration by reading from `bundle.metadata.backlog_config`

#### Scenario: Project health check with backlog metrics

- **GIVEN** a project is linked to a backlog provider (config in `ProjectBundle.metadata.backlog_config`)
- **WHEN** user runs `specfact project health-check --project-name my-project`
- **THEN** adapter's `fetch_all_issues()` and `fetch_relationships()` methods are called to build graph
- **AND** shows spec-code alignment (from existing enforce command)
- **AND** shows backlog maturity metrics (from `DependencyAnalyzer.coverage_analysis()`)
- **AND** shows dependency graph health (cycles, orphans, coverage)
- **AND** shows release readiness status
- **AND** provides action items for improvement
- **AND** output uses `rich.table.Table` for metrics and `rich.panel.Panel` for sections (consistent with existing console patterns)

#### Scenario: Integrated DevOps workflow

- **GIVEN** a project is linked to a backlog provider (config in `ProjectBundle.metadata.backlog_config`)
- **WHEN** user runs `specfact project devops-flow --project-name my-project --stage plan --action generate-roadmap`
- **THEN** adapter's `fetch_all_issues()` and `fetch_relationships()` methods are called to build graph
- **AND** uses backlog dependency graph to create release timeline
- **AND** identifies critical path from dependency graph using `DependencyAnalyzer.critical_path()`
- **AND** estimates timeline duration based on critical path
- **AND** generates roadmap markdown file with console output using `rich.table.Table` and `rich.panel.Panel`

#### Scenario: DevOps workflow - develop stage

- **GIVEN** a project is linked to a backlog provider
- **WHEN** user runs `specfact project devops-flow --project-name my-project --stage develop --action sync`
- **THEN** syncs spec plan + backlog state
- **AND** detects conflicts between spec and backlog
- **AND** reports conflicts if found
- **AND** shows sync status

#### Scenario: DevOps workflow - review stage

- **GIVEN** a project is linked to a backlog provider
- **WHEN** user runs `specfact project devops-flow --project-name my-project --stage review --action validate-pr`
- **THEN** extracts backlog item references from PR description
- **AND** verifies items are implemented in spec plan
- **AND** runs enforce command to validate contracts
- **AND** reports validation results

#### Scenario: DevOps workflow - release stage

- **GIVEN** a project is linked to a backlog provider
- **WHEN** user runs `specfact project devops-flow --project-name my-project --stage release --action verify`
- **THEN** runs full health check
- **AND** gets items targeted for release
- **AND** checks readiness using `verify-readiness` command
- **AND** generates release notes if ready
- **AND** exits with code 0 if ready, 1 if blockers found

#### Scenario: DevOps workflow - monitor stage

- **GIVEN** a project is linked to a backlog provider
- **WHEN** user runs `specfact project devops-flow --project-name my-project --stage monitor --action health-check`
- **THEN** runs continuous health metrics check
- **AND** alerts on drift (spec-code misalignment, backlog issues)
- **AND** reports current project status

### Requirement: Backlog Configuration in Spec YAML

The system SHALL support backlog configuration in `.specfact/spec.yaml` for provider linking, type mapping, and auto-sync.

#### Scenario: Configure backlog in spec YAML

- **GIVEN** a `.specfact/spec.yaml` file (project-level defaults, separate from bundle-specific `ProjectBundle.metadata.backlog_config`)
- **WHEN** backlog_config section is added:

  ```yaml
  backlog_config:
    version: "1.0"
    provider:
      adapter: "github"
      project: "owner/repo"
    type_mapping:
      template: "github_projects"
      overrides:
        - labels: ["epic", "meta"]
          type: epic
    dependency_rules:
      template: "github_projects"
    auto_sync:
      enabled: true
      interval: "hourly"
      baseline_file: ".specfact/backlog-baseline.json"
  ```

- **THEN** backlog commands use this configuration as defaults (can be overridden by bundle-specific config)
- **AND** auto-sync runs according to interval setting
- **AND** type mapping overrides are applied
- **AND** baseline file path is specified (JSON format for performance)

### Requirement: DevOps Stages Configuration

The system SHALL support DevOps flow stages configuration in `.specfact/spec.yaml`.

#### Scenario: Configure DevOps stages in spec YAML

- **GIVEN** a `.specfact/spec.yaml` file
- **WHEN** devops_stages section is added:

  ```yaml
  devops_stages:
    plan:
      - generate-roadmap
      - verify-dependencies
    develop:
      - sync-spec-backlog
      - detect-drift
    review:
      - validate-pr-items
      - enforce-contracts
    release:
      - verify-readiness
      - generate-release-notes
    monitor:
      - health-check
      - alert-on-drift
  ```

- **THEN** `devops-flow` command uses these stage definitions
- **AND** available actions for each stage are defined by configuration
