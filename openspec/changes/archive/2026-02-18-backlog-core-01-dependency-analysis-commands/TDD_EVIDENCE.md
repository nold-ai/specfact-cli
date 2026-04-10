# TDD Evidence

## Scope

Critical-path analysis on large dependency graphs (`1000+` items) must avoid recursion failure and complete quickly.

## Pre-Implementation Failing Run

- Timestamp: 2026-02-13T00:30:xx+01:00
- Command:
  - `hatch test -- tests/unit/backlog/test_analyzers.py::test_critical_path_handles_large_graph_under_one_second -v`
- Result: **FAIL**
- Failure summary:
  - `RecursionError: maximum recursion depth exceeded` from `DependencyAnalyzer.critical_path()` via `_longest_path_from` on a 1200-node chain.

## Implementation

- Added failing test first:
  - `tests/unit/backlog/test_analyzers.py::test_critical_path_handles_large_graph_under_one_second`
- Updated production code:
  - `modules/backlog-core/src/backlog_core/analyzers/dependency.py`
  - Added recursion headroom sizing for deep graphs.
  - Added memoization for `_longest_path_from` to reduce repeated traversal.

## Post-Implementation Passing Run

- Timestamp: 2026-02-13T00:33:xx+01:00
- Commands:
  - `hatch test -- tests/unit/backlog/test_analyzers.py::test_critical_path_handles_large_graph_under_one_second -v`
  - `hatch test -- tests/unit/backlog/test_analyzers.py -v`
- Result: **PASS**
- Verification summary:
  - Large-graph critical path test passes.
  - Full analyzer unit suite passes (`6 passed`).

## Scope (Phase 2.4)

Add remaining backlog command suite entries: `diff`, `promote`, and `generate-release-notes`.

## Pre-Implementation Failing Run (Phase 2.4)

- Timestamp: 2026-02-13T00:58:01+01:00
- Command:
  - `hatch run pytest tests/integration/backlog/test_additional_commands_e2e.py -q`
- Result: **FAIL**
- Failure summary:
  - `diff` command was not registered on `backlog_app` (`exit code 2` on `runner.invoke(..., ["diff", ...])`), so additional backlog commands were missing.

## Implementation (Phase 2.4)

- Added failing integration test first:
  - `tests/integration/backlog/test_additional_commands_e2e.py`
- Updated production code:
  - `modules/backlog-core/src/backlog_core/commands/diff.py`
  - `modules/backlog-core/src/backlog_core/commands/promote.py`
  - `modules/backlog-core/src/backlog_core/commands/release_notes.py`
  - `modules/backlog-core/src/backlog_core/commands/shared.py`
  - `modules/backlog-core/src/backlog_core/commands/__init__.py`
  - `modules/backlog-core/src/backlog_core/main.py`

## Post-Implementation Passing Run (Phase 2.4)

- Timestamp: 2026-02-13T01:00:51+01:00
- Commands:
  - `hatch run pytest tests/integration/backlog/test_additional_commands_e2e.py -q`
  - `hatch run smart-test-folder`
- Result: **PASS**
- Verification summary:
  - Additional backlog command integration test passes (`1 passed`).
  - Smart folder test suite passes (`158 tests`), executed outside sandbox due Hatch coverage file permission constraints.

## Scope (Phase 2.2.15)

Make backlog-core help ordering impact-oriented so command groups are listed before leaf commands.

## Pre-Implementation Failing Run (Phase 2.2.15)

- Timestamp: 2026-02-13T01:21:xx+01:00
- Command:
  - `hatch run pytest modules/backlog-core/tests/unit/test_command_order.py -q`
- Result: **FAIL**
- Failure summary:
  - `backlog --help` listed `delta` after leaf commands (`delta_idx > sync_idx`), violating groups-first discoverability.

## Implementation (Phase 2.2.15)

- Added failing test first:
  - `modules/backlog-core/tests/unit/test_command_order.py`
- Updated production code:
  - `modules/backlog-core/src/backlog_core/main.py`
  - Added `_BacklogCoreCommandGroup` with stable priority-based ordering and attached it to `backlog_app`.

## Post-Implementation Passing Run (Phase 2.2.15)

- Timestamp: 2026-02-13T01:22:xx+01:00
- Commands:
  - `hatch run pytest modules/backlog-core/tests/unit/test_command_order.py -q`
  - `hatch run specfact backlog -h`
- Result: **PASS**
- Verification summary:
  - Module-local `backlog --help` now lists `delta` before leaf commands.
  - Unified CLI help keeps `ceremony` and `delta` at the top with impact-sorted leaf commands following.

## Validation Refresh (Phase 2.5)

- Timestamp: 2026-02-13
- Commands:
  - `hatch run contract-test`
  - `hatch run type-check`
  - User full-suite run (`hatch run smart-test-full`)
- Result: **PASS**
- Verification summary:
  - Contract test run passed.
  - Type-check completed with warnings only (`0 errors`).
  - Full suite reported: `2613 tests`, `61.0% coverage` (coverage threshold treated as optional per approved constraint override).
  - Backlog-focused unit validation passed: `hatch run pytest tests/unit/backlog modules/backlog-core/tests/unit -q` (`158 passed`).

## Scope (Phase 3.1)

Add `project link-backlog` and persist backlog provider configuration through module-scoped project metadata extensions.

## Pre-Implementation Failing Run (Phase 3.1)

- Timestamp: 2026-02-13T01:30:xx+01:00
- Command:
  - `hatch run pytest tests/unit/commands/test_project_cmd.py -k link_backlog -q`
- Result: **FAIL**
- Failure summary:
  - `project link-backlog` command did not exist (`SystemExit(2)`).
  - No metadata extension API was available to persist `backlog_core.backlog_config`.

## Implementation (Phase 3.1)

- Added failing tests first:
  - `tests/unit/commands/test_project_cmd.py` (`TestProjectLinkBacklog`)
- Updated production code:
  - `src/specfact_cli/models/project.py`
    - Added generic metadata extension container and accessors:
      - `ProjectMetadata.extensions`
      - `ProjectMetadata.set_extension(...)`
      - `ProjectMetadata.get_extension(...)`
  - `src/specfact_cli/modules/project/src/commands.py`
    - Added `project link-backlog` command with adapter/project-id/template options.
    - Saves config at `project_metadata.extensions["backlog_core"]["backlog_config"]`.
  - `modules/backlog-core/src/backlog_core/graph/builder.py`
    - Reads backlog config from metadata extension path (`extensions.backlog_core.backlog_config`).
  - `tests/unit/backlog/test_builders.py`
    - Added regression test for extension-path config loading.

## Post-Implementation Passing Run (Phase 3.1)

- Timestamp: 2026-02-13T01:31-01:32+01:00
- Commands:
  - `hatch run pytest tests/unit/commands/test_project_cmd.py -k link_backlog -q`
  - `hatch run pytest tests/unit/backlog/test_builders.py -k extensions -q`
  - `hatch run pytest tests/unit/commands/test_project_cmd.py -q`
  - `hatch run format`
  - `hatch run type-check`
- Result: **PASS**
- Verification summary:
  - `project link-backlog` persists `adapter`, `project_id`, and optional `template`.
  - Project command unit suite passes (`23 passed`).
  - Builder resolves metadata extension config path correctly.
  - Type-check completed with warnings only (`0 errors`).

## Scope (Phase 3.2 partial)

Add `project health-check` with backlog graph coverage/cycle/orphan metrics sourced from linked backlog configuration.

## Pre-Implementation Failing Run (Phase 3.2 partial)

- Timestamp: 2026-02-13T01:34:xx+01:00
- Command:
  - `hatch run pytest tests/unit/commands/test_project_cmd.py -k health_check -q`
- Result: **FAIL**
- Failure summary:
  - `project health-check` command did not exist.
  - No test seam (`_collect_backlog_health_metrics`) existed for deterministic health metric validation.

## Implementation (Phase 3.2 partial)

- Added failing tests first:
  - `tests/unit/commands/test_project_cmd.py` (`TestProjectHealthCheck`)
- Updated production code:
  - `src/specfact_cli/modules/project/src/commands.py`
    - Added `_collect_backlog_health_metrics(...)` helper.
    - Added `project health-check` command.
    - Reads linked config from `ProjectMetadata` extension `backlog_core.backlog_config`.
    - Reports typed coverage, dependency coverage, orphan count, and cycle count.

## Post-Implementation Passing Run (Phase 3.2 partial)

- Timestamp: 2026-02-13T01:34-01:35+01:00
- Commands:
  - `hatch run pytest tests/unit/commands/test_project_cmd.py -k health_check -q`
  - `hatch run pytest tests/unit/commands/test_project_cmd.py -q`
  - `hatch run pytest tests/integration/commands/test_project_health_check_command.py -q`
  - `hatch run specfact project health-check --help`
  - `hatch run format`
  - `hatch run type-check`
- Result: **PASS**
- Verification summary:
  - Health check fails fast with actionable `link-backlog` guidance when missing config.
  - Health check reads linked metadata extension and renders backlog graph health table.
  - Project command unit suite passes (`27 passed`).
  - Health-check integration command suite passes (`2 passed`).

## Validation Refresh (Phase 3.5 partial)

- Timestamp: 2026-02-13T01:36:xx+01:00
- Commands:
  - `hatch run pytest modules/backlog-core/tests/unit/test_schema_extensions.py -q`
  - `hatch run format`
- Result: **PASS**
- Verification summary:
  - Added schema extension regression tests covering:
    - module package extension declarations
    - project metadata extension persistence across bundle save/load
    - `BacklogGraph` JSON serialization round-trip
  - New tests passed (`3 passed`).

## Validation Refresh (Phase 3.2 completion)

- Timestamp: 2026-02-13T01:52-01:53+01:00
- Commands:
  - `hatch run pytest tests/unit/commands/test_project_cmd.py -k health_check -q`
  - `hatch run pytest tests/integration/commands/test_project_health_check_command.py -q`
  - `hatch run pytest tests/unit/commands/test_project_cmd.py -q`
  - `hatch run smart-test-folder`
  - `hatch run format`
  - `hatch run type-check`
- Result: **PASS**
- Verification summary:
  - `health-check` now includes spec-code alignment and release-readiness sections.
  - Unit and integration tests for health-check pass.
  - Smart-test-folder completed successfully for modified folders (no additional unit-test targets discovered by selector).

## Scope (Phase 3.3/3.4 remaining)

Implement remaining `project devops-flow` stage actions and add `project snapshot`, `project regenerate`, `project export-roadmap`.

## Pre-Implementation Failing Run (Phase 3.3/3.4 remaining)

- Timestamp: 2026-02-13T01:56+01:00
- Command:
  - `hatch run pytest tests/unit/commands/test_project_cmd.py -k "devops_flow_plan_generate_roadmap or devops_flow_release_verify_calls_readiness or snapshot_writes_baseline or export_roadmap_runs_critical_path or regenerate_runs_sync_and_conflict_scan" -q`
- Result: **FAIL**
- Failure summary:
  - `devops-flow` only supported monitor/health-check and rejected plan/release actions.
  - Missing helper seams in project module (`generate_roadmap`, `merge_plans`, `find_conflicts`).
  - Missing commands: `project snapshot`, `project regenerate`, `project export-roadmap`.

## Scope (Phase 3.4 regenerate UX)

Reduce `project regenerate` conflict noise by default and add explicit strict/verbose controls.

## Pre-Implementation Failing Run (Phase 3.4 regenerate UX)

- Timestamp: 2026-02-13T02:18:04+01:00
- Command:
  - `hatch run pytest tests/unit/commands/test_project_cmd.py -k "regenerate_conflicts_are_summary_only_by_default or regenerate_strict_fails_and_verbose_lists_conflicts" -q`
- Result: **FAIL**
- Failure summary:
  - Default `project regenerate` exited with code `1` when conflicts existed; expected summary-only warning with zero exit unless strict mode is requested.
  - CLI did not accept `--strict` (`No such option: --strict`), so strict/verbose conflict behavior was unavailable.

## Implementation (Phase 3.4 regenerate UX)

- Added strict/verbose controls to `project regenerate`:
  - `--strict`: fail command when mismatches are detected.
  - `--verbose`: print detailed mismatch lines.
- Updated default mismatch behavior:
  - Print a single summary warning (`Detected N plan/backlog mismatches`).
  - Exit successfully unless `--strict` is set.

Updated production code:

- `src/specfact_cli/modules/project/src/commands.py`

## Post-Implementation Passing Run (Phase 3.4 regenerate UX)

- Timestamp: 2026-02-13T02:19:00+01:00
- Commands:
  - `hatch run pytest tests/unit/commands/test_project_cmd.py -k "regenerate_runs_sync_and_conflict_scan or regenerate_conflicts_are_summary_only_by_default or regenerate_strict_fails_and_verbose_lists_conflicts" -q`
  - `hatch run format`
  - `hatch run type-check`
- Result: **PASS**
- Verification summary:
  - `regenerate` defaults to summary-only warning output and zero exit when mismatches exist.
  - `--strict --verbose` prints detailed mismatch rows and exits non-zero.
  - Formatting and type-check completed successfully (type-check warnings-only baseline unchanged).

## Scope (Phase 3.7 provider dependency enrichment)

Enrich GitHub/ADO provider outputs so dependency graph analysis gets relationship edges and improved item typing from adapter-normalized data.

## Pre-Implementation Failing Run (Phase 3.7 provider dependency enrichment)

- Timestamp: 2026-02-13T02:22:52+01:00
- Command:
  - `hatch run pytest modules/backlog-core/tests/unit/test_provider_enrichment.py -q`
- Result: **FAIL**
- Failure summary:
  - `GitHubAdapter.fetch_all_issues()` did not enrich normalized `type` in payload (`KeyError: 'type'`).
  - `GitHubAdapter.fetch_relationships()` returned no edges for `blocks`/`blocked by`/`related` body references.
  - `AdoAdapter.fetch_relationships()` returned no edges for hierarchy/dependency/relation links.
  - End-to-end coverage check remained untyped and without dependencies (`properly_typed == 0`, `with_dependencies == 0`).

## Implementation (Phase 3.7 provider dependency enrichment)

- Updated `GitHubAdapter.fetch_all_issues()` to enrich normalized graph `type` values from label/type/title signals.
- Implemented `GitHubAdapter.fetch_relationships()` extraction from issue metadata/body references with deterministic edge mapping:
  - `blocks #X` -> `source=current, target=X, type=blocks`
  - `blocked by #X` / `depends on #X` -> `source=X, target=current, type=blocks`
  - parent/child and related/reference phrases -> normalized `parent` / `relates` edge types.
- Implemented `AdoAdapter.fetch_relationships()` extraction from relation links (`provider_fields.relations`) with parity mapping:
  - hierarchy forward/reverse -> `parent`
  - dependency/predecessor forward/reverse -> `blocks`
  - related -> `relates`
- Added regression tests:
  - Unit: `modules/backlog-core/tests/unit/test_provider_enrichment.py`
  - Integration fixtures: `tests/integration/backlog/test_provider_enrichment_e2e.py`

## Post-Implementation Passing Run (Phase 3.7 provider dependency enrichment)

- Timestamp: 2026-02-13T02:25:50+01:00
- Commands:
  - `hatch run pytest modules/backlog-core/tests/unit/test_provider_enrichment.py -q`
  - `hatch run pytest tests/integration/backlog/test_provider_enrichment_e2e.py -q`
  - `hatch run pytest modules/backlog-core/tests/unit/test_backlog_protocol.py tests/unit/backlog/test_builders.py -q`
  - `hatch run format`
  - `hatch run type-check`
  - `hatch run smart-test-folder`
- Result: **PASS**
- Verification summary:
  - Provider enrichment tests pass for GitHub and ADO extraction/normalization.
  - Integration fixture flows pass for both providers through `backlog analyze-deps` graph export.
  - Formatting and type-check pass (warnings-only baseline unchanged).
  - `smart-test-folder` completed successfully when run outside sandbox due Hatch coverage config write requirements.

## Validation Refresh (Phase 3.6.6 E2E flow)

- Timestamp: 2026-02-13T02:28:39+01:00
- Command:
  - `hatch run pytest tests/integration/commands/test_project_devops_workflow_commands.py -q`
- Result: **PASS**
- Verification summary:
  - Added integration coverage for full stage sequence `plan -> develop -> review -> release -> monitor`.
  - `test_project_devops_flow_complete_stage_sequence` validates all stage/action paths execute end-to-end with deterministic stubs.
  - Integration command file now passes fully (`4 passed`).

## Scope (0.5 Init module discovery alignment)

Align `specfact init` with command registration so workspace-level modules appear in `--list-modules`, `--enable-module`, and `--disable-module`.

### Pre-Implementation Failing Run (0.5)

- Timestamp: 2026-02-18
- Command:
  - `hatch run pytest tests/unit/specfact_cli/registry/test_init_module_lifecycle_ux.py::test_init_enable_workspace_level_module_succeeds -v`
- Result: **FAIL** (before code change)
- Failure summary: Init used `discover_package_metadata(get_modules_root())` for validation, so enabling a module only present in `SPECFACT_MODULES_ROOTS` was blocked ("module not found"); exit_code == 1.

### Implementation (0.5)

- Tests added: `test_init_list_modules_includes_workspace_level_modules`, `test_init_enable_workspace_level_module_succeeds` in `tests/unit/specfact_cli/registry/test_init_module_lifecycle_ux.py`.
- Production change: `src/specfact_cli/modules/init/src/commands.py` — replaced `discover_package_metadata(get_modules_root())` with `discover_all_package_metadata()` for building `packages` and `discovered_list`.
- Updated mocks in existing init tests from `discover_package_metadata` to `discover_all_package_metadata` (no-arg lambda).

### Post-Implementation Passing Run (0.5)

- Timestamp: 2026-02-18
- Command:
  - `hatch run pytest tests/unit/specfact_cli/registry/test_init_module_lifecycle_ux.py -v`
- Result: **PASS** (11 passed)
- Verification summary: All init lifecycle UX tests pass; workspace-level module list and enable flows succeed.
