## Context

`specfact-cli` now operates as a lean core with bundle-owned workflow behavior implemented in `specfact-cli-modules`, but a large set of active OpenSpec changes and GitHub issues still reflect the pre-split monolithic layout. The drift is visible in three places:

- active proposals still describe `modules/<name>/...` implementation inside the core repo for bundle-owned backlog, ceremony, and similar workflow features
- GitHub issues for bundle-owned work are still open in `nold-ai/specfact-cli`, even though their canonical implementation surface belongs in `nold-ai/specfact-cli-modules`
- `specfact-cli` has a cleaned Epic -> Feature -> User Story hierarchy, while `specfact-cli-modules` does not yet have an equivalent planning hierarchy for module-owned work

This change is cross-cutting because it affects active OpenSpec artifacts, both repositories' issue trackers, and planning metadata such as `CHANGE_ORDER.md`.

## Goals / Non-Goals

**Goals:**

- define one repeatable classification workflow for active changes and linked GitHub issues: keep in core, move to modules, or split/rescope
- define the required proposal updates for changes that still refer to obsolete monolithic structure
- define the operational rule for GitHub issue reassignment between repos
- define how planning inventories and parent hierarchy must be updated in both repos when ownership changes
- define the required Epic and Feature creation work in `specfact-cli-modules` before module-owned user stories are reassigned

**Non-Goals:**

- implement the actual issue transfers, closes, or recreation in this change
- create the `specfact-cli-modules` project board itself
- implement any product behavior from the reclassified changes
- redesign the canonical five-bundle taxonomy already established by module migration

## Decisions

### Decision: Canonical ownership comes from archived core-vs-bundle specs, not from active proposals

Use the archived and canonical ownership documents as the source of truth for assignment decisions:

- `core-lean-package`
- `module-categories`
- `bundle-extraction`
- `backlog-module-ownership`
- `project-codebase-ownership`
- `code-review-module`

Rationale: active proposals are precisely what drifted. Classification must be based on the post-migration architecture rather than on stale proposal language.

Alternative considered: trust the active proposal’s current repo and path references.
Rejected because that would preserve obsolete ownership and keep planning drift unresolved.

### Decision: Reassignment is a two-step decision, not a blanket move

For each affected GitHub issue:

1. classify the capability as `core`, `modules`, or `split/rescope`
2. if `modules`, decide `transfer-existing-issue` or `close-and-recreate`

`transfer-existing-issue` is preferred when GitHub supports moving the issue between these repositories with acceptable metadata preservation for the specific issue type and workflow. `close-and-recreate` is required when transfer support is unavailable, restricted, or would break planning clarity.

Rationale: this preserves history when possible, but avoids blocking the cleanup on a platform limitation.

Alternative considered: always recreate.
Rejected because it discards useful history and adds unnecessary churn when native transfer is viable.

### Decision: Parent hierarchy must exist in the target repo before user stories are reassigned

Module-owned user stories must not be moved into `specfact-cli-modules` as flat orphan issues. The target repo needs its own aligned Epic -> Feature -> User Story hierarchy first, with Features created before story reassignment.

Rationale: reassignment without parent structure would recreate the same planning problem already fixed in `specfact-cli`.

Alternative considered: move user stories first and normalize hierarchy later.
Rejected because it produces an intermediate state that is hard to audit and easy to forget.

### Decision: Rescope stale proposals in place before implementation resumes

Changes that remain in `specfact-cli` but still describe the old monolithic package layout must be updated in place so their proposal, design, and tasks reflect current architecture. Changes classified as module-owned must either be retired from the core repo after replacement tracking is established, or reduced to core-owned contract/integration deltas only.

Rationale: implementation against stale proposals would produce incorrect code ownership even if issue tracking were fixed.

Alternative considered: postpone proposal cleanup until implementation starts.
Rejected because the stale proposal is itself the thing currently driving incorrect planning and ownership assumptions.

## Risks / Trade-offs

- [Issue-transfer support differs from expectation] -> Mitigation: encode `transfer` as preferred but require a documented recreate fallback per issue.
- [A change mixes core contracts and module behavior] -> Mitigation: allow `split/rescope` classification instead of forcing a single repo.
- [Modules repo hierarchy diverges from core hierarchy naming] -> Mitigation: require explicit mapping from moved user stories to target Epic and Feature, not just title similarity.
- [CHANGE_ORDER updates become asymmetric across repos] -> Mitigation: require paired updates in `specfact-cli` and the target planning inventory in `specfact-cli-modules`.
- [Users interpret old issue numbers as the active source of truth after recreation] -> Mitigation: require cross-links both ways and closure comments that name the replacement issue.

## Migration Plan

1. Inventory active changes and linked GitHub issues in `specfact-cli`.
2. Classify each as `core`, `modules`, or `split/rescope` using the canonical ownership specs.
3. For each `modules` item, define the target bundle/domain and the target Epic/Feature in `specfact-cli-modules`.
4. Create any missing Epic and Feature parents in `specfact-cli-modules`.
5. Reassign each module-owned issue by transfer when supported, otherwise close and recreate with updated scope and cross-links.
6. Update `CHANGE_ORDER.md` in `specfact-cli` and the matching planning inventory in `specfact-cli-modules`.
7. Update the affected active proposals so their repo assignment and implementation paths reflect the final decision.

Rollback strategy:

- if reassignment starts but target hierarchy is incomplete, stop before changing child issue ownership
- if a transfer path proves unusable, fall back to close-and-recreate while preserving the old issue as a historical pointer

## Open Questions

- Which file in `specfact-cli-modules` will serve as the canonical equivalent of `CHANGE_ORDER.md` for this cleanup?
- Which active changes should be split into paired core-plus-modules changes instead of being wholly reassigned?
- Should non-backlog bundle families beyond `specfact-backlog` and `specfact-code-review` gain explicit Epic/Feature hierarchy immediately, or only the currently affected module-owned work?
