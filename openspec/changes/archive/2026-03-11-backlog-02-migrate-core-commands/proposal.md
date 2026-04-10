# Change: Migrate backlog-core commands to specfact-backlog bundle

## Why

Commit 978cc82 deleted the `backlog-core` module (containing `add`, `analyze-deps`, `trace-impact`, `verify-readiness`, `diff`, `sync`, `promote`, `generate-release-notes`, `delta` commands) as part of backlog ownership cleanup. However, these commands were never migrated to the `nold-ai/specfact-backlog` bundle. Result: documented commands are missing from the CLI, creating a product/runtime alignment gap where README and docs describe commands that fail with "No such command".

## What Changes

- **RECOVER** deleted backlog-core command implementations from worktree/git history
- **MIGRATE** commands into `specfact-backlog` bundle under appropriate subcommand structure
- **INTEGRATE** command registrations with specfact-backlog's Typer app structure
- **ADD** ceremony aliases for high-impact commands (e.g., `backlog ceremony add` → `backlog add`)
- **UPDATE** docs to reflect restored command availability
- **DEPRECATE** legacy backlog-core module references in favor of bundle-only ownership

## Capabilities

### New Capabilities

- `backlog-add`: Interactive and non-interactive backlog item creation with parent validation, DoR checks, and adapter-specific payload construction (GitHub, ADO).
- `backlog-sync`: Bidirectional backlog synchronization with cross-adapter state mapping and lossless round-trip support.
- `backlog-delta`: Delta analysis commands (status, impact, cost-estimate, rollback-analysis) for backlog graph change tracking.
- `backlog-analyze-deps`: Dependency graph analysis for backlog items with cycle detection and impact surfacing.
- `backlog-verify-readiness`: Definition of Ready (DoR) validation against configurable rules before sprint planning.
- `backlog-diff`: Compare backlog states between snapshots or adapters.
- `backlog-promote`: Promote backlog items through hierarchy (story → feature → epic) with state preservation.
- `backlog-generate-release-notes`: Generate release notes from backlog item collections and completion status.

### Modified Capabilities

- `daily-standup`: Extend ceremony alias coverage to include migrated commands where appropriate.
- `backlog-daily-markdown-normalization`: Ensure migrated commands support Markdown normalization for consistency.

## Dependencies

- `backlog-module-ownership-cleanup` (archived): Established that specfact-backlog should own all backlog commands.
- `module-migration-10-bundle-command-surface-alignment`: Validates documented vs runtime command surface; this change closes the backlog gap.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #389
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/389>
- **Last Synced Status**: in-progress
- **Sanitized**: false
