# Tasks: Add backlog dependency analysis and command suites

## 1. Phase 1: Backlog Dependency Analysis (v0.26.0)

### 1.1 Core Data Model: Provider-Agnostic Dependency Graph

- [ ] 1.1.1 Create `src/specfact_cli/backlog/graph/` directory structure
- [ ] 1.1.2 Implement `ItemType` enum (EPIC, FEATURE, STORY, TASK, BUG, SUB_TASK, CUSTOM) in `models.py`
- [ ] 1.1.3 Implement `DependencyType` enum (PARENT_CHILD, BLOCKS, RELATES_TO, DUPLICATES, CLONED_FROM, IMPLEMENTS, CUSTOM) in `models.py`
- [ ] 1.1.4 Implement `BacklogItem` dataclass with fields: id, key, title, type, status, description, priority, parent_id, raw_data, inferred_type, confidence, effective_type() method (use Pydantic BaseModel for serialization support)
- [ ] 1.1.5 Implement `Dependency` dataclass with fields: source_id, target_id, type, metadata, confidence (use Pydantic BaseModel for serialization support)
- [ ] 1.1.6 Implement `BacklogGraph` dataclass with fields: items (Dict[str, BacklogItem]), dependencies (list[Dependency]), provider, project_key, fetched_at, transitive_closure, cycles_detected, orphans (use Pydantic BaseModel for serialization support, implement `from_json()` and `to_json()` class methods)
- [ ] 1.1.7 Add unit tests for `BacklogItem`, `Dependency`, `BacklogGraph` models in `tests/unit/backlog/test_graph_models.py`
- [ ] 1.1.8 Run tests: `hatch run smart-test-unit`
- [ ] 1.1.9 Run linting: `hatch run format`
- [ ] 1.1.10 Run type checking: `hatch run type-check`

### 1.2 Provider-to-Graph Builder: Template-Driven Mapping

- [ ] 1.2.1 Create `src/specfact_cli/backlog/mappers/` directory structure
- [ ] 1.2.2 Create template YAML files in `src/specfact_cli/resources/backlog-templates/`: `ado_scrum.yaml`, `github_projects.yaml`, `jira_kanban.yaml` with type_mapping, dependency_rules, status_mapping sections (templates stored in resources directory for consistency with other resources)
- [ ] 1.2.3 Implement `BacklogGraphBuilder` class with `__init__()`, `_load_template()`, `add_items()`, `_infer_type()`, `_map_status()`, `add_dependencies()`, `_infer_dependency_type()`, `build()` methods (add `@beartype` and `@icontract` decorators to public methods)
- [ ] 1.2.4 Implement template loading logic (loads built-in templates from `src/specfact_cli/resources/backlog-templates/` directory, supports custom config overrides from `ProjectBundle.metadata.backlog_config` or `.specfact/spec.yaml`)
- [ ] 1.2.5 Implement type inference from raw provider items using template rules with confidence scoring
- [ ] 1.2.6 Implement status mapping from provider status to normalized status using template rules
- [ ] 1.2.7 Implement dependency extraction from provider relationships using template rules
- [ ] 1.2.8 Implement `_compute_transitive_closure()` method for graph analysis
- [ ] 1.2.9 Implement `_detect_cycles()` method using DFS algorithm
- [ ] 1.2.10 Implement `_find_orphans()` method for items with no parents
- [ ] 1.2.11 Add unit tests for `BacklogGraphBuilder` in `tests/unit/backlog/test_builders.py`
- [ ] 1.2.12 Add test fixtures: `tests/unit/backlog/fixtures/ado_sample_graph.json`, `github_sample_graph.json`, `cycles_fixture.json`
- [ ] 1.2.13 Run tests: `hatch run smart-test-unit`
- [ ] 1.2.14 Run linting: `hatch run format`
- [ ] 1.2.15 Run type checking: `hatch run type-check`

### 1.3 Graph Analyzers: Dependency Inference & Validation

- [ ] 1.3.1 Implement `DependencyAnalyzer` class with `__init__()` method (add `@beartype` and `@icontract` decorators)
- [ ] 1.3.2 Implement `compute_transitive_closure()` method using DFS traversal (add `@beartype` and `@icontract` decorators)
- [ ] 1.3.3 Implement `_traverse_dfs()` helper method for recursive graph traversal (private method, optional decorators)
- [ ] 1.3.4 Implement `detect_cycles()` method using DFS with recursion stack tracking (add `@beartype` and `@icontract` decorators)
- [ ] 1.3.5 Implement `critical_path()` method for finding longest dependency chain (add `@beartype` and `@icontract` decorators)
- [ ] 1.3.6 Implement `_longest_path_from()` helper method for path calculation (private method, optional decorators)
- [ ] 1.3.7 Implement `impact_analysis()` method for downstream impact calculation (direct_dependents, transitive_dependents, blockers, estimated_impact_count) (add `@beartype` and `@icontract` decorators)
- [ ] 1.3.8 Implement `coverage_analysis()` method for backlog health metrics (total_items, properly_typed, properly_typed_pct, with_dependencies, orphan_count, cycle_count) (add `@beartype` and `@icontract` decorators)
- [ ] 1.3.9 Add unit tests for `DependencyAnalyzer` in `tests/unit/backlog/test_analyzers.py`
- [ ] 1.3.10 Test cycle detection with known cycles fixture
- [ ] 1.3.11 Test critical path calculation with various graph structures
- [ ] 1.3.12 Test impact analysis with different dependency types
- [ ] 1.3.13 Run tests: `hatch run smart-test-unit`
- [ ] 1.3.14 Run linting: `hatch run format`
- [ ] 1.3.15 Run type checking: `hatch run type-check`

### 1.4 Extend BacklogAdapterMixin with Bulk Fetching Methods

- [ ] 1.4.1 Extend `BacklogAdapterMixin` in `src/specfact_cli/adapters/backlog_base.py` with abstract method `fetch_all_issues(project_id: str, filters: dict | None = None) -> list[dict[str, Any]]` with `@abstractmethod`, `@beartype`, and `@icontract` decorators
- [ ] 1.4.2 Extend `BacklogAdapterMixin` with abstract method `fetch_relationships(project_id: str) -> list[dict[str, Any]]` with `@abstractmethod`, `@beartype`, and `@icontract` decorators
- [ ] 1.4.3 Implement `fetch_all_issues()` in `GitHubAdapter` (use GitHub API to fetch all issues from repository, handle pagination, return list of issue dicts) with `@beartype` and `@icontract` decorators
- [ ] 1.4.4 Implement `fetch_relationships()` in `GitHubAdapter` (use GitHub API to fetch issue links, dependencies, return list of relationship dicts with source/target/item_ref fields) with `@beartype` and `@icontract` decorators
- [ ] 1.4.5 Implement `fetch_all_issues()` in `AdoAdapter` (use ADO API to fetch all work items from project, handle pagination, return list of work item dicts) with `@beartype` and `@icontract` decorators
- [ ] 1.4.6 Implement `fetch_relationships()` in `AdoAdapter` (use ADO API to fetch work item relations, return list of relationship dicts) with `@beartype` and `@icontract` decorators
- [ ] 1.4.7 Add unit tests for bulk fetching methods in `tests/unit/adapters/test_backlog_base.py` and `test_github.py`, `test_ado.py`
- [ ] 1.4.8 Run tests: `hatch run smart-test-unit`
- [ ] 1.4.9 Run linting: `hatch run format`
- [ ] 1.4.10 Run type checking: `hatch run type-check`

### 1.5 CLI Command: `specfact backlog analyze-deps`

- [ ] 1.5.1 Create `src/specfact_cli/backlog/commands/` directory structure
- [ ] 1.5.2 Implement `dependency.py` with `analyze_deps()` command using typer (add `@beartype` decorator)
- [ ] 1.5.3 Add command options: `--project-id`, `--adapter`, `--template`, `--custom-config`, `--output`, `--json-export`
- [ ] 1.5.4 Implement adapter fetching logic using `AdapterRegistry.get_adapter()` from bridge adapter architecture (bulk fetching methods already implemented in task 1.4)
- [ ] 1.5.5 Call adapter's `fetch_all_issues(project_id)` method to get all backlog items
- [ ] 1.5.6 Call adapter's `fetch_relationships(project_id)` method to get all relationships
- [ ] 1.5.7 Implement graph building using `BacklogGraphBuilder` with template selection (passes fetched items and relationships to builder)
- [ ] 1.5.8 Implement analysis execution using `DependencyAnalyzer` (coverage, cycles, critical path)
- [ ] 1.5.9 Implement markdown report generation (`generate_dependency_report()`) using `rich.table.Table` for tabular data and `rich.panel.Panel` for section headers (follow existing console patterns from `specfact_cli.utils.console`)
- [ ] 1.5.10 Implement JSON export (`export_graph_json()`) for `BacklogGraph` serialization (Pydantic model JSON serialization)
- [ ] 1.5.11 Implement `trace_impact()` command for specific item impact analysis using existing console helpers (`print_info`, `print_success`, `print_warning` from `specfact_cli.utils.console`)
- [ ] 1.5.12 Create `backlog_app = typer.Typer(name="backlog", help="Backlog dependency analysis and sync")` in `src/specfact_cli/backlog/commands/__init__.py`
- [ ] 1.5.13 Register `analyze_deps` and `trace_impact` commands to `backlog_app`
- [ ] 1.5.14 Register `backlog_app` in `src/specfact_cli/cli.py` after `sync` command group (location: after line with `app.add_typer(sync.app, name="sync", ...)` with comment `# 11.7. Backlog Management`)
- [ ] 1.5.15 Add integration tests in `tests/integration/backlog/test_ado_e2e.py` and `test_github_e2e.py`
- [ ] 1.5.16 Run tests: `hatch run smart-test-folder`
- [ ] 1.5.17 Run linting: `hatch run format`
- [ ] 1.5.18 Run type checking: `hatch run type-check`

### 1.6 Configuration: User-Defined Mappers

- [ ] 1.6.1 Create backlog configuration schema for `ProjectBundle.metadata.backlog_config` field (not separate `.specfact/backlog-config.yaml` file) with `dependencies` section (template, type_mapping, dependency_rules, status_mapping) and `providers` section
- [ ] 1.6.2 Implement YAML schema validation (`config_schema.py`) using Pydantic (for `.specfact/spec.yaml` backlog_config section)
- [ ] 1.6.3 Implement config loading in `BacklogGraphBuilder` to support custom config overrides (from `ProjectBundle.metadata.backlog_config` or `.specfact/spec.yaml`)
- [ ] 1.6.4 Add tests for custom config loading and override behavior
- [ ] 1.6.5 Run tests: `hatch run smart-test-unit`
- [ ] 1.6.6 Run linting: `hatch run format`

### 1.7 Testing & Validation

- [ ] 1.7.1 Ensure all unit tests pass: `hatch run smart-test-unit`
- [ ] 1.7.2 Ensure all integration tests pass: `hatch run smart-test-folder`
- [ ] 1.7.3 Verify test coverage ≥80%: `hatch run smart-test-status`
- [ ] 1.7.4 Run contract tests: `hatch run contract-test`
- [ ] 1.7.5 Run full test suite: `hatch run smart-test-full`
- [ ] 1.7.6 Validate acceptance criteria:
  - [ ] Parse ADO/GitHub issues into unified model (100% fidelity)
  - [ ] Detect 100% of cycles in test graphs
  - [ ] Type inference confidence ≥ 0.8 for standard provider flows
  - [ ] Critical path computed in < 1 sec for graphs with 1000+ items
  - [ ] User-defined templates override builtin rules correctly
  - [ ] Bulk fetching methods work correctly for GitHub and ADO adapters

## 2. Phase 2: Backlog & Delta Command Suites (v0.27.0)

### 2.1 Backlog Sync Command

- [ ] 2.1.1 Implement `sync.py` with `sync()` command using typer
- [ ] 2.1.2 Add command options: `--project-id`, `--adapter`, `--baseline-file` (default: `.specfact/backlog-baseline.json`), `--output-format`
- [ ] 2.1.3 Implement graph fetching using adapter's `fetch_all_issues()` and `fetch_relationships()` methods
- [ ] 2.1.4 Implement graph building using `BacklogGraphBuilder` with adapter data
- [ ] 2.1.5 Implement baseline loading from JSON file (`BacklogGraph.from_json()`) - baseline stored as JSON for performance (faster parsing for large graphs), format: serialized `BacklogGraph` model
- [ ] 2.1.6 Implement delta computation (`compute_delta()` function comparing baseline_graph vs current_graph)
- [ ] 2.1.7 Implement plan bundle conversion (`BacklogGraphToPlanBundle` class with `convert()` method) - converts `BacklogGraph` to plan bundle format, stores in `ProjectBundle.backlog_graph` field (optional, v1.2)
- [ ] 2.1.8 Implement output format handling (plan bundle YAML or JSON export) - if plan format, save to `.specfact/plans/backlog-<timestamp>.yaml` with `backlog_graph` field
- [ ] 2.1.9 Implement console output using `rich.table.Table` for delta summary and `specfact_cli.utils.console` helpers for consistent formatting
- [ ] 2.1.10 Add `sync` command to backlog CLI group
- [ ] 2.1.11 Add integration tests for sync command
- [ ] 2.1.12 Run tests: `hatch run smart-test-folder`
- [ ] 2.1.13 Run linting: `hatch run format`
- [ ] 2.1.14 Run type checking: `hatch run type-check`

### 2.2 Delta Detection & Analysis

- [ ] 2.2.1 Create `delta_app = typer.Typer(name="delta", help="Backlog delta analysis and impact tracking")` in `src/specfact_cli/backlog/commands/delta.py` (delta is backlog-specific, so it's a separate command group but clearly backlog-related)
- [ ] 2.2.2 Implement `status()` command using typer with options: `--project-id`, `--adapter`, `--since`
- [ ] 2.2.3 Implement baseline loading from `.specfact/backlog-baseline.json` (JSON format for performance) or user-specified file
- [ ] 2.2.4 Implement delta computation with timestamp filtering (`compute_delta()` with `since` parameter)
- [ ] 2.2.5 Implement delta reporting using `rich.table.Table` for tabular output (added, updated, deleted items, status transitions, new dependencies) and `specfact_cli.utils.console` helpers
- [ ] 2.2.6 Implement `impact()` command for downstream impact analysis with console output using existing patterns
- [ ] 2.2.7 Implement `cost-estimate()` command for effort estimation with console output
- [ ] 2.2.8 Implement `rollback-analysis()` command for revert impact analysis with console output
- [ ] 2.2.9 Register all delta commands (`status`, `impact`, `cost-estimate`, `rollback-analysis`) to `delta_app`
- [ ] 2.2.10 Register `delta_app` in `src/specfact_cli/cli.py` after `backlog` command group (location: after `backlog_app` registration with comment `# 11.8. Delta Analysis`)
- [ ] 2.2.11 Add integration tests for delta commands
- [ ] 2.2.12 Run tests: `hatch run smart-test-folder`
- [ ] 2.2.13 Run linting: `hatch run format`
- [ ] 2.2.14 Run type checking: `hatch run type-check`

### 2.3 Release Readiness Verification

- [ ] 2.3.1 Implement `verify.py` with `verify_readiness()` command using typer
- [ ] 2.3.2 Add command options: `--project-id`, `--adapter`, `--target-items`
- [ ] 2.3.3 Implement graph fetching using adapter's `fetch_all_issues()` and `fetch_relationships()` methods
- [ ] 2.3.4 Implement graph building and analysis using `DependencyAnalyzer`
- [ ] 2.3.5 Implement blocker detection (checks `impact_analysis()["blockers"]` for each target item)
- [ ] 2.3.6 Implement circular dependency check (uses `detect_cycles()`)
- [ ] 2.3.7 Implement child completion check (verifies all child items are completed before parent)
- [ ] 2.3.8 Implement status transition validation
- [ ] 2.3.9 Implement exit code logic (0: ready, 1: blockers found)
- [ ] 2.3.10 Implement console output using `rich.panel.Panel` for results and `specfact_cli.utils.console` helpers for error/warning messages
- [ ] 2.3.11 Add `verify-readiness` command to backlog CLI group
- [ ] 2.3.12 Add integration tests for verify-readiness command
- [ ] 2.3.13 Run tests: `hatch run smart-test-folder`
- [ ] 2.3.14 Run linting: `hatch run format`
- [ ] 2.3.15 Run type checking: `hatch run type-check`

### 2.4 Additional Backlog Commands

- [ ] 2.4.1 Implement `diff()` command for showing changes since last sync
- [ ] 2.4.2 Implement `promote()` command for moving items through workflow stages
- [ ] 2.4.3 Implement `generate-release-notes()` command for auto-generating release notes from graph
- [ ] 2.4.4 Add all commands to backlog CLI group
- [ ] 2.4.5 Add integration tests for all commands
- [ ] 2.4.6 Run tests: `hatch run smart-test-folder`
- [ ] 2.4.7 Run linting: `hatch run format`

### 2.5 Testing & Validation

- [ ] 2.5.1 Ensure all unit tests pass: `hatch run smart-test-unit`
- [ ] 2.5.2 Ensure all integration tests pass: `hatch run smart-test-folder`
- [ ] 2.5.3 Verify test coverage ≥80%: `hatch run smart-test-status`
- [ ] 2.5.4 Run contract tests: `hatch run contract-test`
- [ ] 2.5.5 Run full test suite: `hatch run smart-test-full`

## 3. Phase 3: Project Command Enhancement (v0.28.0)

### 3.1 Project Backlog Integration

- [ ] 3.1.1 Extend `ProjectMetadata` model in `src/specfact_cli/models/project.py` to add optional `backlog_config: dict[str, Any] | None` field (not separate config file)
- [ ] 3.1.2 Implement `link_backlog()` command in `project_cmd.py` with options: `--project-name`, `--adapter`, `--project-id`
- [ ] 3.1.3 Implement backlog config storage in `ProjectBundle.metadata.backlog_config` with structure: `{"adapter": "github", "project_id": "owner/repo"}` (stored in bundle metadata, not separate file)
- [ ] 3.1.4 Implement backlog config loading from `ProjectBundle.metadata.backlog_config` (use existing bundle loading utilities)
- [ ] 3.1.5 Implement backlog config saving to `ProjectBundle.metadata.backlog_config` (use existing bundle saving utilities with atomic writes)
- [ ] 3.1.6 Implement console output using `specfact_cli.utils.console` helpers (`print_success`, `print_info`) for consistent formatting
- [ ] 3.1.7 Add unit tests for backlog linking functionality
- [ ] 3.1.8 Run tests: `hatch run smart-test-unit`
- [ ] 3.1.9 Run linting: `hatch run format`
- [ ] 3.1.10 Run type checking: `hatch run type-check`

### 3.2 Project Health Check

- [ ] 3.2.1 Implement `health_check()` command in `project_cmd.py` with options: `--project-name`, `--verbose`
- [ ] 3.2.2 Integrate spec-code alignment check (uses existing `run_enforce()` function)
- [ ] 3.2.3 Integrate backlog health check (uses `DependencyAnalyzer.coverage_analysis()`) - requires fetching graph using adapter's `fetch_all_issues()` and `fetch_relationships()`
- [ ] 3.2.4 Integrate dependency graph health metrics (cycles, orphans, coverage)
- [ ] 3.2.5 Integrate release readiness check (uses `verify_readiness()` from Phase 2)
- [ ] 3.2.6 Implement comprehensive report generation using `rich.table.Table` for metrics and `rich.panel.Panel` for sections, with action items using `specfact_cli.utils.console` helpers
- [ ] 3.2.7 Add integration tests for health-check command
- [ ] 3.2.8 Run tests: `hatch run smart-test-folder`
- [ ] 3.2.9 Run linting: `hatch run format`
- [ ] 3.2.10 Run type checking: `hatch run type-check`

### 3.3 Integrated DevOps Workflow Command

- [ ] 3.3.1 Implement `devops_flow()` command in `project_cmd.py` with options: `--project-name`, `--stage`, `--action`
- [ ] 3.3.2 Implement PLAN stage: `generate-roadmap` action (uses adapter's `fetch_all_issues()` and `fetch_relationships()` to build graph, then `DependencyAnalyzer.critical_path()` and `generate_roadmap()`)
- [ ] 3.3.3 Implement DEVELOP stage: `sync` action (syncs spec plan + backlog state, shows conflicts)
- [ ] 3.3.4 Implement REVIEW stage: `validate-pr` action (enforces spec contracts in PR, links to backlog items)
- [ ] 3.3.5 Implement RELEASE stage: `verify` action (checks blockers, runs verify-readiness, generates release notes)
- [ ] 3.3.6 Implement MONITOR stage: `health-check` action (continuous health metrics, alerts on drift)
- [ ] 3.3.7 Implement helper functions: `generate_roadmap()`, `merge_plans()`, `find_conflicts()`, `extract_backlog_references()`, `extract_release_target()`
- [ ] 3.3.8 Implement console output using `rich.table.Table`, `rich.panel.Panel`, and `specfact_cli.utils.console` helpers for all stage outputs
- [ ] 3.3.9 Add integration tests for devops-flow command
- [ ] 3.3.10 Run tests: `hatch run smart-test-folder`
- [ ] 3.3.11 Run linting: `hatch run format`
- [ ] 3.3.12 Run type checking: `hatch run type-check`

### 3.4 Additional Project Commands

- [ ] 3.4.1 Implement `snapshot()` command for saving current state as baseline (saves `BacklogGraph` to `.specfact/backlog-baseline.json` in JSON format)
- [ ] 3.4.2 Implement `regenerate()` command for re-deriving plan from code + backlog (fetches graph using adapter's `fetch_all_issues()` and `fetch_relationships()`)
- [ ] 3.4.3 Implement `export-roadmap()` command for generating timeline from dependency graph (uses `DependencyAnalyzer.critical_path()` and console output with `rich.table.Table`)
- [ ] 3.4.4 Add all commands to project CLI group
- [ ] 3.4.5 Add integration tests for all commands
- [ ] 3.4.6 Run tests: `hatch run smart-test-folder`
- [ ] 3.4.7 Run linting: `hatch run format`

### 3.5 OpenSpec DSL Extensions

- [ ] 3.5.1 Extend `.specfact/spec.yaml` schema to add `backlog_config` section with provider linking, type mapping, dependency rules, auto-sync configuration (note: this is separate from `ProjectBundle.metadata.backlog_config` - spec.yaml is for project-level defaults, metadata is for bundle-specific config)
- [ ] 3.5.2 Extend `.specfact/spec.yaml` schema to add `devops_stages` section with plan, develop, review, release, monitor stage definitions
- [ ] 3.5.3 Extend `ProjectBundle` model in `src/specfact_cli/models/project.py` to add optional `backlog_graph: BacklogGraph | None` field (v1.2 bundle format)
- [ ] 3.5.4 Implement `BacklogGraph` serialization to YAML/JSON (Pydantic model serialization)
- [ ] 3.5.5 Update schema validation in `src/specfact_cli/validators/schema.py` for spec.yaml extensions
- [ ] 3.5.6 Add tests for schema validation with new sections
- [ ] 3.5.7 Add tests for `BacklogGraph` serialization/deserialization
- [ ] 3.5.8 Run tests: `hatch run smart-test-unit`
- [ ] 3.5.9 Run linting: `hatch run format`

### 3.6 Testing & Validation

- [ ] 3.6.1 Ensure all unit tests pass: `hatch run smart-test-unit`
- [ ] 3.6.2 Ensure all integration tests pass: `hatch run smart-test-folder`
- [ ] 3.6.3 Verify test coverage ≥80%: `hatch run smart-test-status`
- [ ] 3.6.4 Run contract tests: `hatch run contract-test`
- [ ] 3.6.5 Run full test suite: `hatch run smart-test-full`
- [ ] 3.6.6 Validate E2E flow: Test complete DevOps workflow from plan → develop → review → release → monitor

## 4. Git Workflow

- [ ] 4.1 Create git branch `feature/backlog-01-backlog-01-add-backlog-dependency-analysis-and-commands` from `dev` branch
  - [ ] 4.1.1 Ensure we're on dev and up to date: `git checkout dev && git pull origin dev`
  - [ ] 4.1.2 Create branch: `git checkout -b feature/backlog-01-backlog-01-add-backlog-dependency-analysis-and-commands`
  - [ ] 4.1.3 Verify branch was created: `git branch --show-current`

## 5. Documentation

- [ ] 5.1 Update `CHANGELOG.md` with new features (Phase 1, 2, 3)
- [ ] 5.2 Update `README.md` with new backlog and delta commands
- [ ] 5.3 Update `AGENTS.md` with new command patterns
- [ ] 5.4 Create user guide for backlog dependency analysis
- [ ] 5.5 Create user guide for delta commands
- [ ] 5.6 Create user guide for DevOps workflow integration
- [ ] 5.7 Update API documentation for new models and classes

## 6. Pull Request

- [ ] 6.1 Prepare changes for commit
  - [ ] 6.1.1 Ensure all changes are committed: `git add .`
  - [ ] 6.1.2 Commit with conventional message: `git commit -m "feat: add backlog dependency analysis and command suites"`
  - [ ] 6.1.3 Push to remote: `git push origin feature/backlog-01-backlog-01-add-backlog-dependency-analysis-and-commands`
- [ ] 6.2 Create Pull Request from `feature/backlog-01-backlog-01-add-backlog-dependency-analysis-and-commands` to `dev` branch
  - [ ] 6.2.1 Create PR using GitHub CLI: `gh pr create --base dev --head feature/backlog-01-backlog-01-add-backlog-dependency-analysis-and-commands --title "feat: add backlog dependency analysis and command suites" --body "Implements OpenSpec change proposal: backlog-01-add-backlog-dependency-analysis-and-commands"`
  - [ ] 6.2.2 Verify PR was created and is visible on GitHub
