# Migration Removal Plan: specfact-cli Core Decoupling

## Context

- **Migration-05** completed: All MIGRATE-tier code was copied to specfact-cli-modules. Bundles (specfact-project, specfact-backlog, specfact-codebase, specfact-spec, specfact-govern) have local copies. `check-bundle-imports` gate passes; bundles only use CORE/SHARED imports.
- **Migration-06 scope**: Remove residual MIGRATE-tier code from specfact-cli so core owns only runtime/lifecycle/bootstrap. Package-specific artifacts must live in specfact-cli-modules.

## Current State

specfact-cli still contains MIGRATE-tier subsystems that bundles no longer import:

| Subsystem | Target bundle | Core usage blocker |
|-----------|---------------|-------------------|
| `agents` | specfact-project | `modes.router` uses `get_agent` for Copilot routing |
| `analyzers` | specfact-codebase | `sync.repository_sync` uses `CodeAnalyzer`; `importers` uses `ConstitutionEvidenceExtractor` |
| `backlog` | specfact-backlog | `adapters` (github, ado) use backlog mappers/converters for issue conversion |
| `comparators` | specfact-codebase | `sync.repository_sync` uses `PlanComparator` |
| `enrichers` | specfact-project/spec | Used by generators, importers |
| `generators` | specfact-project/spec | `utils.structure` uses `PlanGenerator` for `update_plan_summary`; `importers`, `migrations` |
| `importers` | specfact-project | `adapters.speckit` uses `SpecKitConverter`, `SpecKitScanner` |
| `merge` | specfact-project | Used by generators/enrichers |
| `migrations` | specfact-spec | Used by `generators`, `analyzers`, `agents` |
| `parsers` | specfact-codebase | Used by `validators.agile_validation` |
| `sync` | specfact-project | `templates.bridge_templates` uses `BridgeProbe`; only tests use bridge_templates |
| `templates.registry` | specfact-backlog | Used by `backlog` |
| `validators.sidecar`, `repro_checker` | specfact-codebase | Used by validate/repro commands (bundle) |
| `utils.*` (MIGRATE subset) | specfact-project | Various; `structure` uses `PlanGenerator` |

## Removal Phases

### Phase 1: Zero-core-usage removal (immediate)

Components with **no** imports from core (cli, init, module_registry, upgrade, registry, bootstrap, adapters, models, runtime, telemetry, allowed utils):

- **`templates.bridge_templates`**: Only used by tests. `BridgeProbe` is in sync (MIGRATE). → Migrate tests to specfact-cli-modules; remove `bridge_templates.py`.
- **`sync`** (after bridge_templates): Only used by bridge_templates and tests. specfact-project has `sync_runtime`. → Remove after bridge_templates; migrate sync tests.

### Phase 2: Interface extraction (core keeps interface, impl moves)

- **`utils.structure.update_plan_summary`**: Uses `PlanGenerator`. Extract to interface or delegate to bundle via `module_io_shim`. Minimal stub in core that raises "use bundle" or delegates.
- **`modes.router`**: Uses `agents.registry`. Replace with bundle-loaded agent resolution (router asks registry for agent by command; agent comes from loaded bundle).

### Phase 3: Adapter decoupling (larger refactor)

- **`adapters` (github, ado)**: Use `backlog` mappers/converters. Options: (a) Inline conversion in adapters, (b) Move conversion to specfact-backlog and expose via protocol, (c) Keep minimal backlog interface in core.
- **`adapters.speckit`**: Uses `importers`. Move speckit-specific import logic to specfact-project or create adapter-internal implementation.

### Phase 4: Full MIGRATE removal

After Phases 1–3, remove: `agents`, `analyzers`, `backlog`, `comparators`, `enrichers`, `generators`, `importers`, `merge`, `migrations`, `parsers`, `sync`, `validators.sidecar`, `validators.repro_checker`, `templates.registry`, MIGRATE `utils.*`. Migrate associated tests to specfact-cli-modules.

## Execution Order (Phase 1)

1. Add `test_core_migrate_tier_allowlist` — fail if new MIGRATE-tier paths are added to core.
2. Remove `templates.bridge_templates` (and its test) — move test to specfact-cli-modules or delete if covered there.
3. Remove `sync` package — specfact-project has `sync_runtime`. Update `sync/__init__.py` to raise `ImportError` with migration message, or delete and fix any remaining imports.
4. Fix `utils.structure` — replace `PlanGenerator` usage with minimal implementation or interface.
5. Run quality gates.

## References

- `openspec/changes/archive/2026-03-03-module-migration-02-bundle-extraction/IMPORT_DEPENDENCY_ANALYSIS.md`
- `openspec/changes/archive/2026-03-04-module-migration-05-modules-repo-quality/tasks.md` (section 19)
- specfact-cli-modules `ALLOWED_IMPORTS.md`, `scripts/check-bundle-imports.py`
