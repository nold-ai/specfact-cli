# Change: Bundle Command Surface Alignment

## Why


The released `v0.40.x` CLI command surface does not fully match the documented grouped command API. Several command implementations exist inside official bundles such as `specfact-project` and `specfact-spec`, but the installed bundle command trees do not expose the documented paths at runtime. This creates a release-quality gap: README/site/blog examples describe commands that fail with `No such command ...`, while users can only discover the subset currently mounted by the bundle root apps.

This must be treated as a product/runtime alignment issue first, not just a docs refresh. Release documentation must match shipped behavior, and intended commands that are already implemented in bundle source should either be exposed correctly or removed from the documented surface explicitly.

## What Changes


- Audit the documented grouped command surface against the installed official bundle command trees for `project`, `spec`, and any other affected bundles.
- Expose implemented-but-unreachable commands through the official bundle registration/runtime surface where they are intended to be public.
- Mark any non-shipped or intentionally unsupported command forms as removed from the documented release surface instead of leaving them implied by source-only code.
- Add regression coverage that validates the released bundle command trees include the documented grouped CLI paths.
- Align README/docs/release-content references so `v0.40.x` documentation reflects the actual shipped command surface.

## Capabilities
### New Capabilities

- `bundle-command-surface-alignment`: Official bundle command trees match the documented grouped CLI surface for shipped releases.

## Acceptance Criteria
- Installed official bundles expose documented grouped commands such as `specfact project import from-code`, `specfact project plan ...`, and `specfact spec generate ...` when those commands are intended to be public in `v0.40.x`.
- If a command path is intentionally not part of the shipped runtime surface, README/docs/release content no longer describe it as available.
- Runtime validation fails when a documented grouped command path is missing from the installed official bundle command tree.
- Release-content examples no longer rely on slash-command-only fallbacks to paper over missing CLI registration.
- Validation evidence distinguishes between runtime-surface fixes and docs-only removals.

## Dependencies
- `module-migration-02-bundle-extraction` established the official bundle packaging model.
- `module-migration-06-core-decoupling-cleanup` and `module-migration-07-test-migration-cleanup` established the current post-migration command ownership baseline.
- `cli-val-07-command-package-runtime-validation` provides the runtime audit harness that should be extended to catch this drift.
- `backlog-module-ownership-cleanup` remains a separate cleanup scope and should not absorb unrelated `project`/`spec` bundle-surface fixes.


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #385
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/385>
- **Last Synced Status**: proposed
- **Sanitized**: false
