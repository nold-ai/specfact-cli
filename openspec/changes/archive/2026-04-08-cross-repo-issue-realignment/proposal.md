## Why

Active OpenSpec changes and linked GitHub issues still mix the old monolithic `specfact-cli` structure with the current lean-core plus `specfact-cli-modules` ownership model. That drift now blocks planning: some module-owned backlog, ceremony, and code-review work is still tracked in the core repo, while several active proposals describe obsolete in-repo module layouts and do not map cleanly to the canonical bundle boundaries.

## GitHub Tracking

- GitHub issue: [#484](https://github.com/nold-ai/specfact-cli/issues/484)
- Parent Feature: [#486](https://github.com/nold-ai/specfact-cli/issues/486)
- Parent Epic: [#485](https://github.com/nold-ai/specfact-cli/issues/485)

## What Changes

- Define a single decision framework for classifying active OpenSpec changes and linked GitHub issues as `core`, `modules`, or `split/rescope`.
- Require every affected active proposal in `specfact-cli` to be updated with the steps needed to fit the current architecture and repo assignment.
- Define the operational rule for handling GitHub issues that no longer belong in `specfact-cli`: either move the existing issue to `specfact-cli-modules` when the platform supports it, or close the old issue and create a replacement issue in `specfact-cli-modules` with updated scope and cross-links.
- Define how `openspec/CHANGE_ORDER.md` in `specfact-cli` and the corresponding planning inventory in `specfact-cli-modules` must be updated when ownership changes.
- Define the required Epic -> Feature -> User Story hierarchy to create in `specfact-cli-modules` so module-owned changes have the same planning structure now present in `specfact-cli`.
- Require a reconciled mapping from active core-repo user stories/change proposals to modules-repo epics/features when their implementation ownership is bundle-side.

## Capabilities

### New Capabilities

- `cross-repo-backlog-alignment`: Governance rules for assigning active changes and GitHub issues to the correct repository, reconciling issue migration or recreation, and maintaining aligned Epic -> Feature -> User Story planning hierarchies across `specfact-cli` and `specfact-cli-modules`.

### Modified Capabilities

- `backlog-module-ownership`: Active backlog and ceremony changes must align their repository ownership, issue tracking, and proposal scope with the canonical `specfact-backlog` bundle boundary.
- `project-codebase-ownership`: Active changes that describe outdated module/package ownership must be reconciled to the canonical post-migration core-versus-bundle split before implementation proceeds.

## Impact

- Affected systems: `openspec/changes/*` active proposals/tasks/designs, `openspec/CHANGE_ORDER.md`, GitHub issues in `nold-ai/specfact-cli`, and the corresponding issue/planning inventory in `nold-ai/specfact-cli-modules`.
- Operational impact: maintainers get an explicit move-vs-recreate workflow for issue reassignment and a required hierarchy creation plan for the modules repo.
- Cross-repo coordination: this change depends on inspecting both repositories together and documenting the resulting ownership mapping before further implementation work continues on stale proposals.
