# Change: Remove Flat Shims — Category-Only CLI (0.40.x)

## Why


Module-migration-01 introduced category group commands (`code`, `backlog`, `project`, `spec`, `govern`) and backward-compatibility shims so existing flat commands (e.g. `specfact validate`, `specfact analyze`) still worked while emitting a deprecation notice. The proposal stated: "Shims are removed after one major version cycle."

The 0.40.x series completes that migration: the top-level CLI surface should show only core commands (`init`, `auth`, `module`, `upgrade`) and the five category groups. Scripts and muscle memory that still invoke flat commands must switch to the category form (e.g. `specfact code validate`). This reduces noise in `specfact --help`, clarifies the canonical command topology, and avoids maintaining two code paths.

## What Changes


- **REMOVE**: Registration of compat shims for all 17 non-core flat commands. No more top-level `analyze`, `drift`, `validate`, `repro`, `backlog`, `policy`, `project`, `plan`, `import`, `sync`, `migrate`, `contract`, `spec`, `sdd`, `generate`, `enforce`, `patch` at root.
- **MODIFY**: `_register_category_groups_and_shims()` in `module_packages.py` becomes category-group-only registration (no `FLAT_TO_GROUP` shim loop). Optionally rename to `_register_category_groups()`.
- **REMOVE**: `FLAT_TO_GROUP` and `_make_shim_loader()` (and any shim-specific tests that assert deprecation or shim delegation).
- **KEEP**: Core commands (`init`, `auth`, `module`, `upgrade`) and the five category groups with their sub-commands unchanged. `category_grouping_enabled` remains supported; when `false`, behavior can remain "flat" by mounting module commands directly (no groups, no shims).
- **MODIFY**: Docs and CHANGELOG to state the breaking change and migration path (flat → category).

## Capabilities
### Modified Capabilities

- `category-command-groups`: Sole top-level surface for non-core module commands. No flat shims; users must use `specfact code analyze`, `specfact backlog ceremony`, etc.
- `command-registry`: Bootstrap no longer registers shim loaders; only group typers and (when grouping disabled) direct module commands.

### Removed Capabilities

- Backward-compat shim layer (deprecation delegates) for the 17 flat command names.


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #330
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/330>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
- **Sanitized**: false