# Change: Backlog Core — Dependency Analysis and Command Suites

## Why


After implementing backlog adapters for ADO and GitHub with directional sync (v0.25.1), we need to extend the backlog capabilities beyond simple sync to enable dependency analysis, delta tracking, and integrated DevOps workflows. Without dependency graph analysis, teams cannot understand logical relationships between backlog items (epic → feature → story → task hierarchies) or detect blockers and circular dependencies. Without dedicated backlog/delta command suites, users must use low-level bridge sync commands instead of intuitive backlog-focused workflows.

This change establishes the **`backlog-core` module** — the foundational backlog module that all framework-specific modules (backlog-scrum, backlog-kanban, backlog-safe) depend on. It provides the provider-agnostic graph model, dependency analysis, and core backlog commands.

## Module Package Structure

This change is implemented as a standalone module in the module registry:

```
modules/backlog-core/
  module-package.yaml          # module metadata, commands, schema_extensions, publisher
  src/backlog_core/
    __init__.py
    main.py                    # typer.Typer app — backlog command group with delta subcommands
    graph/
      models.py                # BacklogGraph, GraphBacklogItem, Dependency (Pydantic)
      builder.py               # BacklogGraphBuilder (template-driven mapping)
    analyzers/
      dependency.py            # DependencyAnalyzer (@icontract + @beartype)
    commands/
      analyze_deps.py          # specfact backlog analyze-deps
      sync.py                  # specfact backlog sync
      diff.py                  # specfact backlog diff
      promote.py               # specfact backlog promote
      verify.py                # specfact backlog verify-readiness
      release_notes.py         # specfact backlog generate-release-notes
      delta.py                 # specfact backlog delta status/impact/cost-estimate/rollback-analysis
    adapters/
      backlog_protocol.py      # BacklogGraphProtocol (arch-05 bridge registry)
    resources/
      backlog-templates/
        ado_scrum.yaml
        ado_safe.yaml
        github_projects.yaml
        jira_kanban.yaml
```

**`module-package.yaml` declares:**
- `name: backlog-core`
- `version: 0.1.0`
- `commands: [backlog]` (module extends the shared backlog command group with additional commands and `delta` subgroup)
- `dependencies: []` (no module deps; uses bridge registry for adapters)
- `schema_extensions:` — see arch-07 section below
- `publisher:` — see arch-06 section below

Commands are auto-discovered by the registry and lazy-loaded; no registration in `cli.py` required.

## Module Package Structure

This change is implemented as a standalone module in the module registry:

```
modules/backlog-core/
  module-package.yaml          # module metadata, commands, schema_extensions, publisher
  src/backlog_core/
    __init__.py
    main.py                    # typer.Typer app — backlog command group with delta subcommands
    graph/
      models.py                # BacklogGraph, GraphBacklogItem, Dependency (Pydantic)
      builder.py               # BacklogGraphBuilder (template-driven mapping)
    analyzers/
      dependency.py            # DependencyAnalyzer (@icontract + @beartype)
    commands/
      analyze_deps.py          # specfact backlog analyze-deps
      sync.py                  # specfact backlog sync
      diff.py                  # specfact backlog diff
      promote.py               # specfact backlog promote
      verify.py                # specfact backlog verify-readiness
      release_notes.py         # specfact backlog generate-release-notes
      delta.py                 # specfact backlog delta status/impact/cost-estimate/rollback-analysis
    adapters/
      backlog_protocol.py      # BacklogGraphProtocol (arch-05 bridge registry)
    resources/
      backlog-templates/
        ado_scrum.yaml
        ado_safe.yaml
        github_projects.yaml
        jira_kanban.yaml
```

**`module-package.yaml` declares:**
- `name: backlog-core`
- `version: 0.1.0`
- `commands: [backlog]` (module extends the shared backlog command group with additional commands and `delta` subgroup)
- `dependencies: []` (no module deps; uses bridge registry for adapters)
- `schema_extensions:` — see arch-07 section below
- `publisher:` — see arch-06 section below

Commands are auto-discovered by the registry and lazy-loaded; no registration in `cli.py` required.

## What Changes


- **NEW**: Implement provider-agnostic dependency graph model (`BacklogGraph`, `GraphBacklogItem`, `Dependency`) in `modules/backlog-core/src/backlog_core/graph/models.py` that abstracts epic → feature → story → task hierarchies without locking to ADO/GitHub/Jira models, with full support for Kanban (work item types and states), Scrum (sprint-based hierarchies), and SAFe (Epic → Feature → Story → Task with Value Points and WSJF).
- **NEW**: Add template-driven mapping system (`BacklogGraphBuilder`) in `modules/backlog-core/src/backlog_core/graph/builder.py` that converts provider items (ADO/GitHub) into unified graph using pre-built templates (`ado_scrum`, `ado_safe`, `github_projects`, `jira_kanban`) stored in `modules/backlog-core/src/backlog_core/resources/backlog-templates/`.
- **NEW**: Implement graph analyzers (`DependencyAnalyzer`) in `modules/backlog-core/src/backlog_core/analyzers/dependency.py` for transitive closure, cycle detection, critical path analysis, and impact analysis.
- **NEW**: Add CLI commands under `specfact backlog`: `analyze-deps`, `sync`, `diff`, `promote`, `verify-readiness`, `generate-release-notes` — all declared in `module-package.yaml`, lazy-loaded by registry.
- **NEW**: Add CLI commands under `specfact backlog delta`: `status`, `impact`, `cost-estimate`, `rollback-analysis` — mounted as a backlog subgroup by the module extension mechanism.
- **EXTEND** (arch-05 bridge registry): Define `BacklogGraphProtocol` in `modules/backlog-core/src/backlog_core/adapters/backlog_protocol.py` — a protocol class that adapter implementations (GitHubAdapter, AdoAdapter) satisfy via the bridge registry. The protocol declares: `fetch_all_issues(project_id, filters)`, `fetch_relationships(project_id)`. Adapters register protocol implementations via the bridge registry; no modification to `BacklogAdapterMixin` base class required.
- **EXTEND**: Add provider dependency enrichment path in this change: improve GitHub relationship extraction (`fetch_relationships`) and typing signals (`fetch_all_issues` payload normalization), and validate ADO relationship parity, so health metrics and release-readiness use meaningful dependency edges on real backlogs.
- **EXTEND** (arch-07 schema extensions): The `module-package.yaml` `schema_extensions` section declares:
  - `backlog_core.backlog_graph` on `ProjectBundle` (type: `BacklogGraph | None`) — stores dependency graph data in plan bundles
  - `backlog_core.backlog_config` on `ProjectMetadata` (type: `dict[str, Any] | None`) — stores provider/template config per project
  - Modules access extensions via `bundle.get_extension("backlog_core", "backlog_graph")` / `bundle.set_extension("backlog_core", "backlog_graph", graph)` — no direct `ProjectBundle` attribute modification.
- **EXTEND**: Add backlog configuration section to `.specfact/spec.yaml` for provider linking, type mapping, dependency rules, and auto-sync configuration.
- **EXTEND** (plan E4): Add outputs that teams can use directly: "dependency contract" per edge (what/when/acceptance), ROAM list seed (feeds backlog-safe-01-pi-planning), "critical path narrative" for humans. Add `--export json|md` for analyzers.
- **EXTEND** (arch-01 init-module-state): Align `specfact init` module discovery with command registration so workspace-level modules are included in central module management. Use the same discovery roots for init as for the registry (`discover_all_package_metadata()` / `get_modules_roots()`), so `specfact init --list-modules`, `--enable-module`, and `--disable-module` see and manage workspace-level modules (e.g. `modules/backlog-core/`) consistently with runtime command discovery.

## Arch-06 Marketplace Readiness
The `module-package.yaml` includes publisher and integrity metadata:

```yaml
publisher:
  name: nold-ai
  url: https://github.com/nold-ai/specfact-cli-modules
integrity:
  checksum_algorithm: sha256
  # checksum populated at publish time by sign-modules.yml CI workflow
```

This enables integrity verification when installed via `specfact module install backlog-core`.

## Capabilities
- **backlog-core**: Provider-agnostic `BacklogGraph` model; `DependencyAnalyzer` (transitive closure, cycle detection, critical path, impact); `BacklogGraphBuilder` with template-driven mapping; `BacklogGraphProtocol` for bridge adapter extensions; CLI: `backlog analyze-deps`, `backlog sync`, `backlog diff`, `backlog promote`, `backlog verify-readiness`, `backlog generate-release-notes`; `backlog delta status`, `backlog delta impact`, `backlog delta cost-estimate`, `backlog delta rollback-analysis`.
- **init-module-discovery-alignment**: `specfact init` uses the same module discovery roots as command registration (built-in + workspace-level + `SPECFACT_MODULES_ROOTS`), so `--list-modules`, `--enable-module`, and `--disable-module` operate on all discovered modules including external/workspace-level ones.

## Impact
- **Affected specs**: backlog-core (existing), init-module-state (extended via init-module-discovery-alignment).
- **Affected code**: `modules/backlog-core/` (existing), `src/specfact_cli/modules/init/src/commands.py` (discovery alignment), `src/specfact_cli/registry/module_packages.py` (no API change; init will use existing `discover_all_package_metadata()`).
- **Integration points**: Init command and module state persistence; registry discovery (unchanged).

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #116
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/116>
- **Working Branch**: `feature/backlog-core-01-dependency-analysis-commands`
- **Last Synced Status**: in-progress
- **Sanitized**: false
