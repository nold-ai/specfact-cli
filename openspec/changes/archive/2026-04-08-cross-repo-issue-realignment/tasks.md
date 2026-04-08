## 1. Inventory And Classification

- [ ] 1.1 Create a dedicated worktree branch for this change before applying repository edits.
- [x] 1.2 Inventory all active `specfact-cli` OpenSpec changes and linked GitHub issues that still describe pre-split monolithic ownership.
- [x] 1.3 Classify each inventoried change as `core`, `modules`, or `split/rescope` using the canonical ownership specs and current `CHANGE_ORDER.md`.
- [x] 1.4 Record the classification matrix in a change-local analysis artifact so later edits are traceable.

## 2. Decide Reassignment Strategy

- [x] 2.1 For every `modules`-classified issue, decide whether to use native GitHub transfer or close-and-recreate in `specfact-cli-modules`.
- [x] 2.2 Define the required replacement-linking and closure-comment format for any close-and-recreate path.
- [x] 2.3 Identify every active proposal that must be rewritten to remove obsolete `modules/<name>/` core-repo implementation paths.
- [x] 2.4 Identify every `split/rescope` change that needs paired core and modules follow-up ownership instead of a single-repo implementation.

## 3. Plan Modules-Repo Hierarchy

- [x] 3.1 Map every module-owned user story to its target modules-repo domain, Epic, and Feature parent.
- [x] 3.2 Determine which Epics already exist in `specfact-cli-modules` and which new Epics must be created.
- [x] 3.3 Determine which Features must be created in `specfact-cli-modules` to parent the moved or recreated user stories.
- [x] 3.4 Define the order of operations so target Epic and Feature parents are created before any child story is reassigned.

## 4. Update Core-Repo Planning Artifacts

- [x] 4.1 Update `openspec/CHANGE_ORDER.md` in `specfact-cli` to annotate which active changes remain core-owned, which move to modules repo, and which are split/rescoped.
- [x] 4.2 Update each affected active proposal in `specfact-cli` so its scope and implementation location match the current architecture decision.
- [x] 4.3 Where a core-repo proposal is no longer the implementation owner, reduce it to retained core contract or integration scope, or mark it for paired modules-repo follow-up.
- [x] 4.4 Add explicit cross-references from the affected core-repo changes to their target modules-repo issues or replacement changes.

## 5. Apply Modules-Repo Issue And Hierarchy Changes

- [x] 5.1 Create the required Epics in `specfact-cli-modules` for the module-owned work that is currently tracked only in `specfact-cli`.
- [x] 5.2 Create the required Feature issues in `specfact-cli-modules` under those Epics.
- [x] 5.3 Reassign each module-owned user story by transfer when supported; otherwise close the `specfact-cli` issue and create the replacement issue in `specfact-cli-modules`.
- [x] 5.4 Link every moved or recreated user story under its target Feature and ensure each Feature is linked to the correct Epic.
- [x] 5.5 Add all created or reassigned modules-repo issues to the new `specfact-cli-modules` GitHub project once it exists.

## 6. Align Modules-Repo Planning Inventory

- [x] 6.1 Update the planning inventory in `specfact-cli-modules` so it reflects the new Epics, Features, moved/recreated user stories, and dependency links.
- [x] 6.2 Ensure the modules-repo planning inventory cross-references the original `specfact-cli` issue numbers where historical continuity matters.
- [x] 6.3 Verify that module-owned backlog and ceremony changes no longer remain listed as active implementation work in the core-repo planning flow.

## 7. Validate And Close Out

- [x] 7.1 Validate that every affected active change now has an explicit ownership decision and correct repository assignment.
- [x] 7.2 Validate that every module-owned issue has exactly one authoritative issue in `specfact-cli-modules` and no ambiguous active duplicate in `specfact-cli`.
- [x] 7.3 Validate that both repositories' planning inventories and issue hierarchies agree on Epic -> Feature -> User Story relationships.
- [x] 7.4 Run `openspec validate cross-repo-issue-realignment --strict` and capture the result.
- [x] 7.5 Update any affected docs or contributor guidance that still imply monolithic ownership for module-implemented work.
