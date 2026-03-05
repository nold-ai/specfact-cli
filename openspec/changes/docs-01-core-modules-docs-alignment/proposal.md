# Change: docs-01 - Core and Modules Docs Alignment

## Why

The documentation set still carries drift from the pre-modularized CLI: some pages still imply a large flat command surface, some marketplace guidance is split or duplicated, and command/reference material is not yet clearly separated between permanent core commands and marketplace-installed module bundles. After module-migration-01 through -07, this drift is now a release blocker because users need the docs to match the actual core-plus-marketplace architecture.

## What Changes

- Audit every user-facing Markdown document in the repository, starting with `README.md`, `docs/index.md`, and the published docs tree, for outdated command paths, installation guidance, architecture wording, and module ownership assumptions.
- Align all command documentation to the current grouped command topology and lean-core model, removing or correcting stale references to former flat top-level commands except where explicitly documented as historical or compatibility context.
- Consolidate and update marketplace documentation so official bundle installation, bundle dependencies, trust/signing, and publish/distribution flows are accurate, discoverable, and non-duplicative.
- Restructure command/reference documentation so permanent core commands and marketplace-installed module commands are described through the correct package and category boundaries instead of one legacy catch-all command inventory.
- Update README, landing pages, architecture, directory-structure, dependency-resolution, installation, and module-development docs to reflect the decoupled `specfact-cli` core and `specfact-cli-modules` repository model.
- Add explicit documentation notes describing current docs ownership: core docs remain in `specfact-cli` for now, module-specific docs are planned to migrate to `specfact-cli-modules`, and future module behavior changes should not require long-term maintenance in core release branches.
- Update sidebar/navigation and cross-links where needed so marketplace, module categories, command reference, and architecture pages remain discoverable after the reorganization.
- Add or update validation checks/tests for docs-to-command-surface parity where practical, so future drift is caught earlier.

## Capabilities

### New Capabilities
- `module-docs-ownership`: documentation defines the current and target ownership boundary between `specfact-cli` core docs and `specfact-cli-modules` bundle docs, including an explicit migration note for future relocation of module-specific documentation.

### Modified Capabilities
- `documentation-alignment`: documentation requirements are extended to cover the post-modularization command surface, lean-core architecture, marketplace-distributed bundles, and removal of stale flat-command guidance.
- `implementation-status-docs`: implementation-status and architecture pages must clearly describe which functionality is owned by core, which is delivered by marketplace bundles, and which documentation remains temporarily hosted in core.
- `module-development-guide`: module development and module architecture docs must reflect the dedicated modules repository, bundle/package boundaries, and the expected split between core lifecycle docs and bundle-specific command docs.

## Impact

- **Affected docs**: `README.md`, `docs/index.md`, `docs/README.md`, `docs/reference/commands.md`, `docs/reference/directory-structure.md`, `docs/reference/dependency-resolution.md`, `docs/reference/module-categories.md`, `docs/reference/module-contracts.md`, `docs/reference/module-security.md`, `docs/guides/installing-modules.md`, `docs/guides/module-marketplace.md`, `docs/guides/marketplace.md`, `docs/guides/publishing-modules.md`, `docs/guides/module-development.md`, `docs/getting-started/*`, `docs/adapters/*`, and additional Markdown pages discovered during the audit.
- **Affected navigation/layout**: `docs/_layouts/default.html`, page front-matter, cross-links, and landing-page information architecture.
- **Affected tests/tooling**: existing docs parity checks and any added lightweight validation for command/docs consistency.
- **Dependencies**: must stay aligned with the final outcomes of module-migration-01 through -07, marketplace-01/02, backlog-auth-01, and backlog-core-07.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: TBD
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: local-change-created
- **Sanitized**: false
