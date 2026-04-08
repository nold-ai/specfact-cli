# Design: Bundle Command Surface Alignment

## Context

The official bundles in `specfact-cli-modules` are currently mounted at the top-level grouped roots (`project`, `spec`, `code`, `backlog`, `govern`). However, runtime validation and release-content verification show that some documented grouped command paths are not actually reachable from the installed bundle roots even though source implementations exist in subpackages such as:

- `specfact_project/import_cmd/commands.py`
- `specfact_project/plan/commands.py`
- `specfact_spec/generate/commands.py`
- `specfact_spec/contract/commands.py`

The mismatch can come from one or more of:

1. bundle root apps not mounting intended subgroup apps
2. module manifests exposing only a coarse root while nested Typer apps are never registered under that root
3. docs/release pages describing intended command paths that are not part of the shipped bundle runtime

## Goals

- Make the shipped bundle command tree and the documented grouped CLI surface agree.
- Preserve grouped command UX (`specfact project ...`, `specfact spec ...`) as the primary CLI contract.
- Extend runtime validation so missing documented command paths fail before release docs drift again.

## Non-Goals

- Redesign the grouped command model.
- Reintroduce removed flat command shims.
- Fold backlog ownership cleanup into this scope.

## Design Decisions

### 1. Treat documented grouped commands as a release contract

For commands documented in README/docs/release content, we treat their grouped CLI path as part of the shipped release surface. If the implementation exists and is intended, the bundle must expose it. If it is not intended, the docs must be corrected in the same change.

### 2. Fix runtime exposure at the bundle layer, not in core

The correct fix location is the bundle command tree in `specfact-cli-modules`, not ad hoc core shims in `specfact-cli`. Core should validate and consume the official bundle surface, not patch around missing bundle registration.

### 3. Separate runtime fixes from docs-only removals

Each missing command path discovered by the audit must be classified as one of:

- `public-runtime`: implemented and intended, must be exposed by the bundle
- `docs-only-drift`: not actually part of the shipped command surface, docs must change
- `owner-decision-required`: ambiguous public intent, block release-doc updates until resolved

This avoids silently deleting user-facing commands just because they are currently unreachable.

### 4. Extend runtime validation to assert documented grouped paths

The existing command-package runtime validation should include an explicit set of documented grouped command paths that must resolve in an installed-bundle environment. This closes the current gap where source code exists but the release surface is not actually mounted.

## Implementation Outline

1. Inventory documented grouped command paths from README/docs/release-content pages that claim `v0.40.x` support.
2. Compare those paths against installed official bundle help/runtime behavior.
3. For `public-runtime` paths, patch the affected bundle root apps/manifests so the subgroup commands are mounted.
4. For `docs-only-drift` paths, update release docs in `specfact-cli` so shipped examples are truthful.
5. Add targeted regression tests plus command-audit assertions for the documented grouped paths.

## Risks

- Some source-only commands may depend on assumptions that never held in installed-bundle mode, so mounting them can expose follow-on runtime bugs.
- Docs and runtime may have diverged in multiple repos (`specfact-cli` and `specfact-cli-modules`), so the implementation may require coordinated PRs.
- Public examples in blog/website content may need synchronized updates outside the repo docs set.
