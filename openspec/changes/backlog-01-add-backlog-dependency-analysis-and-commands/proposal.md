# Change: Add backlog dependency analysis and command suites

## Why



After implementing backlog adapters for ADO and GitHub with directional sync (v0.25.1), we need to extend the backlog capabilities beyond simple sync to enable dependency analysis, delta tracking, and integrated DevOps workflows. Without dependency graph analysis, teams cannot understand logical relationships between backlog items (epic → feature → story → task hierarchies) or detect blockers and circular dependencies. Without dedicated backlog/delta command suites, users must use low-level bridge sync commands instead of intuitive backlog-focused workflows. Without project command integration, backlog features remain disconnected from the broader SpecFact project management workflow. Adding these capabilities establishes SpecFact CLI as the comprehensive DevOps tool for agile workflows, enabling teams to analyze dependencies, track changes, verify release readiness, and orchestrate complete DevOps flows from a single tool.

## What Changes



- **NEW**: Implement provider-agnostic dependency graph model (`BacklogGraph`, `GraphBacklogItem`, `Dependency`) that abstracts epic → feature → story → task hierarchies without locking to ADO/GitHub/Jira models, with full support for Kanban (work item types and states), Scrum (sprint-based hierarchies), and SAFe (Epic → Feature → Story → Task with Value Points and WSJF).
- **NOTE**: `GraphBacklogItem` extends the base `BacklogItem` model from `add-template-driven-backlog-refinement` with graph-specific fields (parent_id, dependencies, graph metadata). This avoids model name conflicts and reuses the unified domain model.
- **NEW**: Add template-driven mapping system (`BacklogGraphBuilder`) that converts provider items (ADO/GitHub) into unified graph using pre-built templates (ado_scrum, ado_safe, github_projects, jira_kanban) with user-defined overrides, supporting work item type hierarchies (Epic/Feature/Story/Task) and framework-specific relationships (SAFe parent-child, Scrum sprint assignments, Kanban state transitions).
- **NEW**: Implement graph analyzers (`DependencyAnalyzer`) for transitive closure, cycle detection, critical path analysis, and impact analysis (downstream dependencies).
- **NEW**: Add CLI command `specfact backlog analyze-deps` for dependency analysis with template selection, custom config overrides, and report generation (markdown or JSON export).
- **NEW**: Add CLI command `specfact backlog sync` for full backlog synchronization into SpecFact plan bundles with baseline comparison and delta computation.
- **NEW**: Add CLI command `specfact backlog diff` for showing changes since last sync (added, updated, deleted items, status transitions, new dependencies).
- **NEW**: Add CLI command `specfact backlog promote` for moving items through workflow stages with dependency validation.
- **NEW**: Add CLI command `specfact backlog verify-readiness` for checking blockers, circular dependencies, and child completion before release.
- **NEW**: Add CLI command `specfact backlog generate-release-notes` for auto-generating release notes from dependency graph.
- **NEW**: Add CLI command `specfact delta status` for showing backlog changes since last baseline (new items, modified items, deleted items, status transitions, new dependencies).
- **NEW**: Add CLI command `specfact delta impact` for showing downstream impact of recent changes using dependency graph traversal.
- **NEW**: Add CLI command `specfact delta cost-estimate` for estimating effort of delta changes.
- **NEW**: Add CLI command `specfact delta rollback-analysis` for analyzing what breaks if changes are reverted.
- **EXTEND**: Add `specfact project snapshot` command for saving current state as baseline for delta comparison.
- **EXTEND**: Add `specfact project regenerate` command for re-deriving plan from code + backlog with conflict detection.
- **EXTEND**: Add `specfact project link-backlog` command for associating project with backlog provider (ADO/GitHub/Jira) with configuration storage in `ProjectBundle.metadata.backlog_config` (not separate config file).
- **EXTEND**: Add `specfact project export-roadmap` command for generating timeline from dependency graph with critical path estimation.
- **EXTEND**: Add `specfact project health-check` command for comprehensive project quality metrics (spec-code alignment, backlog maturity, dependency graph health, release readiness).
- **EXTEND**: Add `specfact project devops-flow` command for integrated agile DevOps workflow orchestration (plan → develop → review → release → monitor stages) with context-specific actions.
- **EXTEND**: Add backlog configuration section to `.specfact/spec.yaml` for provider linking, type mapping, dependency rules, and auto-sync configuration.
- **EXTEND**: Add DevOps flow stages configuration to `.specfact/spec.yaml` for defining workflow stages and actions.
- **EXTEND**: Extend `BacklogAdapterMixin` (or `BacklogAdapter` interface from `add-generic-backlog-abstraction`) with abstract methods `fetch_all_issues()` and `fetch_relationships()` for bulk backlog data fetching (required for dependency graph building).
- **NOTE**: The `search_issues()` and `list_work_items()` methods from `add-template-driven-backlog-refinement` are wrapper methods that call `fetch_all_issues()` with filtering. Both changes coordinate on adapter method naming.
- **EXTEND**: Add optional `backlog_graph: BacklogGraph | None` field to `ProjectBundle` model (v1.2) for storing dependency graph data in plan bundles, with separate JSON baseline files (`.specfact/backlog-baseline.json`) for delta comparison.
- **EXTEND** (plan E4): Add outputs that teams can use directly: "dependency contract" per edge (what/when/acceptance), ROAM list seed (feeds SAFe safe-pi-planning-essentials), "critical path narrative" for humans (short, evidence-based). Add `--export json|md` for analyzers. **Acceptance**: `specfact backlog analyze-deps` can export a "dependency review packet" (Markdown).

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #116
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/116>
- **Last Synced Status**: proposed
- **Sanitized**: true