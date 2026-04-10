# Change: Backlog Module Ownership Cleanup

## Why

Backlog command ownership is still split across `specfact-cli` core shims, the built-in `backlog-core` package, and the marketplace bundle `nold-ai/specfact-backlog`. That violates the intended module boundary, causes duplicate command overlap, and leaves backlog prompts/templates coupled to core code even though they belong to backlog behavior.

## What Changes

- Make `nold-ai/specfact-backlog` the sole owner of user-facing backlog and policy commands.
- Remove backlog command ownership and backlog-specific prompt/template assets from `specfact-cli` core.
- Keep only truly shared runtime contracts, provider adapters, and generic data models in core.
- Move backlog-coupled prompt and template resources out of core so prompt ownership matches command ownership.
- Remove duplicate-registration fallback behavior once backlog is module-owned and no longer overlaps with core.

## Capabilities

### New Capabilities

- `backlog-module-ownership`: Backlog commands, prompts, and templates are owned by the backlog module instead of being split across core and module layers.

## Acceptance Criteria

- Running `specfact` with `nold-ai/specfact-backlog` installed does not produce duplicate backlog command overlap warnings during normal startup.
- User-facing backlog commands are provided only by the installed backlog module, not by a parallel core backlog command surface.
- Backlog-specific prompts and templates are shipped from the backlog module instead of core CLI resources.
- Core retains only shared runtime contracts, provider integrations, and generic data models required by multiple modules.
- Validation and command-audit coverage prove the backlog command tree works end-to-end with module-only ownership.

## Dependencies

- `module-migration-06-core-decoupling-cleanup` (#338) and `module-migration-07-test-migration-cleanup` (#339) establish the broader module-migration baseline.
- `cli-val-07-command-package-runtime-validation` documents the duplicate-command/runtime-noise findings this cleanup resolves.
- `init-ide-prompt-source-selection` depends on this cleanup to finalize prompt ownership boundaries.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #383
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/383>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: d481ea8b14a140e7 -->