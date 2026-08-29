## Why

Core module discovery and `specfact module doctor` describe normal
project-over-user shadowing as stale state and recommend uninstalling the
user-scoped copy. Review/bootstrap workflows surface and follow that
recommendation, repeatedly removing `specfact-codebase` and
`specfact-code-review` from the user scope even though those installations are
still needed in other repositories.

## What Changes

- Keep project-over-user precedence unchanged.
- Replace user-scope uninstall recovery advice with non-destructive scope
  guidance in module discovery warnings and doctor output.
- State explicitly that the user-scoped copy remains installed, normal
  shadowing alone does not require uninstalling it, and availability elsewhere
  still depends on module state and higher-priority copies.
- Add regression tests that reject destructive user-scope uninstall
  recommendations while preserving origin diagnostics.

## Capabilities

### Modified Capabilities

- `module-scope-diagnostics`: Discovery and doctor diagnostics report shadowing
  without treating a valid user installation as cleanup residue.

## Impact

- Affected code: `src/specfact_cli/registry/module_discovery.py` and
  `src/specfact_cli/modules/module_registry/src/commands.py`.
- Affected tests: focused module discovery and module doctor unit tests.
- Paired modules delivery: `nold-ai/specfact-cli-modules#454` corrects the
  repository bootstrap surfaces that trigger this behavior during review work.
- Compatibility and data impact: none. Discovery order, module state, explicit
  uninstall behavior, manifests, and persistent installation data remain
  unchanged.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **Parent Feature**: [#353](https://github.com/nold-ai/specfact-cli/issues/353)
- **Parent Epic**: [#194](https://github.com/nold-ai/specfact-cli/issues/194)
- **Bug Issue**: [#699](https://github.com/nold-ai/specfact-cli/issues/699)
- **Paired Modules Bug**:
  [nold-ai/specfact-cli-modules#452](https://github.com/nold-ai/specfact-cli-modules/issues/452)
- **Issue Relationships**: `#699` is a sub-issue of Feature `#353`; Feature
  `#353` is a sub-issue of Epic `#194`.
- **Blocked By**: none
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: issue type, labels, assignee, parent, project
  assignment, In Progress status, and blocker metadata verified on 2026-08-29
- **Sanitized**: false
