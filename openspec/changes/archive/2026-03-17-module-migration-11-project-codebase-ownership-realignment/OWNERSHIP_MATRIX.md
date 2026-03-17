# Project vs Codebase Ownership Matrix

## Current Runtime Surface

### Core CLI group mounting

| Surface | Current owner | Evidence | Notes |
|---|---|---|---|
| `specfact project ...` | `specfact-project` bundle | `src/specfact_cli/groups/project_group.py` | Mounts `project`, `plan`, `import`, `sync`, `migrate` |
| `specfact code ...` | `specfact-codebase` bundle | `src/specfact_cli/groups/codebase_group.py` | Mounts only `analyze`, `drift`, `validate`, `repro` |

### Brownfield import path

| Concern | Current owner | Evidence | Problem |
|---|---|---|---|
| Public grouped path | `project` | `docs/reference/commands.md`, `README.md`, `module-migration-10` active spec | Code-first workflow is exposed as project-owned |
| Actual command implementation | `specfact_project.import_cmd` | `packages/specfact-project/src/specfact_project/import_cmd/commands.py` | Canonical implementation lives under project bundle |
| `code` aggregate bundle app | `specfact-codebase.code` | `packages/specfact-codebase/src/specfact_codebase/code/commands.py` | No `import` subtree exists today |

## Contradictory Archived Ownership Records

| Subsystem / path | Archived source | Recorded owner |
|---|---|---|
| `import_cmd` | `module-migration-01`, `module-grouping` spec, `bundle-extraction` spec | `specfact-project` |
| `analyzers` | `IMPORT_DEPENDENCY_ANALYSIS.md`, `MIGRATION_REMOVAL_PLAN.md` | `specfact-codebase` |
| `comparators` | `IMPORT_DEPENDENCY_ANALYSIS.md`, `MIGRATION_REMOVAL_PLAN.md` | `specfact-codebase` |
| brownfield-oriented `parsers` | `IMPORT_DEPENDENCY_ANALYSIS.md`, `MIGRATION_REMOVAL_PLAN.md` | `specfact-codebase` |
| migrated local package placement | `module-migration-05-modules-repo-quality/tasks.md` section 19.2 | copied into `specfact_project` |

## Current Helper / Subsystem Placement

### In `specfact-project`

- `import_cmd`
- `agents`
- `analyzers`
- `comparators`
- `parsers`
- `sync_runtime`
- project-bundle artifact lifecycle commands (`project`, `plan`, `sync`, `migrate`)

### In `specfact-codebase`

- `code` aggregate app
- `analyze`
- `drift`
- `validate`
- `repro`
- `validators.sidecar`
- `validators.repro_checker`
- `sync.drift_detector`

## Pending Active Changes That Must Align

| Change | Why alignment is required |
|---|---|
| `module-migration-10-bundle-command-surface-alignment` | Currently treats `specfact project import from-code` as the documented grouped contract |
| `init-ide-prompt-source-selection` | Prompt source ownership must not re-assert obsolete import paths |
| docs/prompt updates under current release branch | README, prompt validation, suggestions, and docs all reference the import path users are told to run |

## Target Rule From This Change

- `code` owns commands whose primary input is source code or runtime code evidence
- `project` owns SpecFact project bundle/workspace artifact lifecycle
- `specfact code import` is canonical in the target state
- temporary aliases such as `project import from-code` are acceptable only as compatibility behavior during transition
