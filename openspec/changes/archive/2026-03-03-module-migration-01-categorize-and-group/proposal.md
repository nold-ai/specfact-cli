# Change: Module Grouping and Category Command Groups

## Why

SpecFact CLI currently exposes 21 flat top-level commands, overwhelming new users with no clear entry point and no indication of which modules are relevant to their workflow. Every install loads every module, even when users need only backlog management or codebase quality tooling. Community and enterprise modules have no canonical grouping to compete alongside official modules.

The marketplace infrastructure (marketplace-01 archived, marketplace-02 in progress) now provides the foundation — signed packages, lifecycle management, dependency resolution — to move forward with the UX reorganization. This change introduces the categorization layer that groups the 21 modules into 5 workflow-domain bundles under category group commands, adds the metadata fields to `module-package.yaml` that drive the grouping, and replaces the overwhelming flat help with a curated first-run selection experience.

This mirrors the VS Code model: ship a lean core, present workflow-domain groups, and let users install exactly the bundle that matches how they work.

## What Changes

- **MODIFY**: Add `category`, `bundle`, `bundle_group_command`, and `bundle_sub_command` fields to all 21 `module-package.yaml` files
- **NEW**: Create `src/specfact_cli/groups/` layer with 5 category umbrella `typer.Typer()` apps:
  - `groups/project_group.py` — aggregates project, plan, import_cmd, sync, migrate
  - `groups/backlog_group.py` — aggregates backlog, policy_engine
  - `groups/codebase_group.py` — aggregates analyze, drift, validate, repro
  - `groups/spec_group.py` — aggregates contract, spec, sdd, generate
  - `groups/govern_group.py` — aggregates enforce, patch_mode
- **MODIFY**: Update `src/specfact_cli/registry/bootstrap.py` to mount category groups with backward-compat shims for all existing flat commands
- **NEW**: Add `category_grouping_enabled` config flag (default `true`) allowing opt-out during migration window
- **MODIFY**: Update `specfact init` with first-run interactive module selection UI, `--profile` and `--install` parameters
- **NEW**: 4 workflow profile presets: solo-developer, backlog-team, api-first-team, enterprise-full-stack

## Capabilities

### New Capabilities

- `module-grouping`: `category`, `bundle`, `bundle_group_command`, and `bundle_sub_command` metadata fields in `module-package.yaml`; registry reads these to group modules into category bundles
- `category-command-groups`: 5 category umbrella commands (`specfact project`, `specfact backlog`, `specfact code`, `specfact spec`, `specfact govern`) that aggregate module sub-apps; controlled by `category_grouping_enabled` config flag
- `first-run-selection`: Interactive `specfact init` bundle selection with profile presets (solo-developer, backlog-team, api-first-team, enterprise-full-stack); CI/CD non-interactive path via `--profile` and `--install` flags

### Modified Capabilities

- `command-registry`: Bootstrap updated to mount category groups instead of individual module apps; backward-compat shims delegate old top-level commands to category equivalents with deprecation warning in interactive mode
- `lazy-loading`: Registry lazy loading extended to resolve category groups first, then resolve sub-commands within the group

## Impact

- **Affected code**:
  - `src/specfact_cli/modules/*/module-package.yaml` (all 21, add category metadata)
  - `src/specfact_cli/groups/` (new directory: 5 group files + `__init__.py`)
  - `src/specfact_cli/registry/bootstrap.py` (mount category groups, compat shims)
  - `src/specfact_cli/registry/registry.py` (group-aware lazy loading)
  - `src/specfact_cli/modules/init/src/commands.py` (first-run selection UI, `--profile`, `--install`)
  - `src/specfact_cli/cli.py` (register category groups)
- **Affected specs**: New specs for `module-grouping`, `category-command-groups`, `first-run-selection`; delta specs on `command-registry` and `lazy-loading`
- **Affected documentation**:
  - `docs/guides/getting-started.md` (update install + first-run flow with new bundle selection UX)
  - `docs/reference/module-categories.md` (new: canonical category assignments, bundle contents, profile presets)
  - `docs/reference/commands.md` (update command topology: before/after diagram)
  - `docs/_layouts/default.html` (navigation: add "Module Categories" reference page)
  - `README.md` (update command listing to reflect category groups)
- **Backward compatibility**: Fully backward compatible during migration window. All 21 existing top-level commands remain functional via deprecation shims that warn in interactive mode and run silently in CI/CD mode. Shims are removed after one major version cycle.
- **Rollback plan**: Set `category_grouping_enabled: false` in `~/.specfact/config.yaml` to revert to flat module mounting. All category group code is isolated in `groups/` and `bootstrap.py` — reverting the bootstrap change restores original flat behavior without touching module code.
- **Blocked by**: `marketplace-02-advanced-marketplace-features` (dependency-resolution capability required for bundle-level dep graph: `specfact-spec` → `specfact-project`, `specfact-govern` → `specfact-project`)

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #315
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/315>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open
- **Sanitized**: false
