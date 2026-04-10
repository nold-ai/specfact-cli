# Change: module-migration-04 - Remove Flat Shims — Category-Only CLI (0.40.x)

## Why

Module-migration-01 introduced category group commands (`code`, `backlog`, `project`, `spec`, `govern`) and backward-compatibility shims so existing flat commands (e.g. `specfact validate`, `specfact analyze`) still worked while emitting a deprecation notice. The proposal stated: "Shims are removed after one major version cycle."

The 0.40.x series completes that migration: the top-level CLI surface should show only core commands (`init`, `auth`, `module`, `upgrade`) and the five category groups. Scripts and muscle memory that still invoke flat commands must switch to the category form (e.g. `specfact code validate`). This reduces noise in `specfact --help`, clarifies the canonical command topology, and avoids maintaining two code paths.

## What Changes

- **REMOVE**: `FLAT_TO_GROUP` constant and `_make_shim_loader()` function from `module_packages.py` — the shim machinery that generates deprecated flat-command delegates.
- **MODIFY**: `_register_category_groups_and_shims()` in `module_packages.py` — remove the `FLAT_TO_GROUP` shim registration loop; retain only the category group registration logic. Rename to `_register_category_groups()` to reflect the reduced responsibility.
- **REMOVE**: Any shim-specific tests that assert flat-command deprecation warnings or shim delegation (e.g. tests that assert `specfact validate --help` exits 0 via a shim or that a `DeprecationWarning` is emitted for flat commands).
- **KEEP**: Core commands (`init`, `auth`, `module`, `upgrade`) and the five category groups with their sub-commands unchanged. `category_grouping_enabled` remains supported; when `false`, behavior mounts module commands directly (no groups, no shims).
- **MODIFY**: Docs and CHANGELOG to state the breaking change and migration path (flat → category group).
- **Scope boundary — bootstrap.py is NOT modified by this change**: This change removes the shim *machinery* from `module_packages.py`. The dead shim *registration call sites* in `bootstrap.py` (which called `_make_shim_loader()` or equivalent) are cleaned up by `module-migration-03-core-slimming` (Wave 4), which follows this change. The call sites become unreachable/dead after this change but are not deleted here to keep the diff focused and to avoid coupling two unrelated deletion passes in one PR.

## Capabilities

### Modified Capabilities

- `category-command-groups`: Sole top-level surface for non-core module commands. No flat shims; users must use `specfact code analyze`, `specfact backlog ceremony`, etc.
- `command-registry`: `module_packages.py` no longer contains the shim registration loop or shim factory. Only category group typers are registered (and, when grouping disabled, direct module commands).

### Removed Capabilities

- Flat-command shim machinery (`FLAT_TO_GROUP`, `_make_shim_loader()`) — the infrastructure that generated deprecation-warning delegates for the 17 flat command names.

## Impact

- **Affected code**:
  - `src/specfact_cli/modules/module_packages.py` — `FLAT_TO_GROUP` removed, `_make_shim_loader()` removed, `_register_category_groups_and_shims()` renamed to `_register_category_groups()` with shim loop deleted
  - `tests/` — shim-specific tests removed; category group routing tests retained
- **Affected code (NOT in this change)**: `src/specfact_cli/registry/bootstrap.py` shim call sites — cleaned up by `module-migration-03-core-slimming` (Wave 4, follows this change)
- **Backward compatibility**: **Breaking** — `specfact analyze`, `specfact validate`, etc. no longer work as root-level commands. Users must use `specfact code analyze`, `specfact code validate`, etc. (or install the relevant bundle and use the category group).
- **Blocked by**: `module-migration-01-categorize-and-group` — category groups must exist before the shim layer can be safely removed; `FLAT_TO_GROUP` references the group routing established in migration-01.
- **Followed by**: `module-migration-03-core-slimming` — cleans up dead shim registration call sites from `bootstrap.py` after this change removes the machinery those calls referenced.
- **Wave**: Wave 3 — parallel with or after `module-migration-02-bundle-extraction`; must complete before `module-migration-03-core-slimming` begins bootstrap.py cleanup.
- **Test migration boundary**: This change does **not** own broad test-suite migration or legacy test cleanup. It only updates shim-specific tests that directly validate flat-command removal and category-group routing. Modules-repo parity/migration belongs to `module-migration-05`; remaining unrelated full-suite cleanup is handled in follow-up change(s) tracked from migration-03 phase 20.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #330
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/330>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
- **Sanitized**: false
