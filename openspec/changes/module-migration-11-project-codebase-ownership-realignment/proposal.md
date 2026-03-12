# Change: Project And Codebase Ownership Realignment

## Why

The post-migration bundle model leaves a fuzzy boundary between `specfact-project` and `specfact-codebase`.

Archived migration changes explicitly classified `import_cmd` under the `project` category, but later migration work also copied major code-analysis subsystems into `specfact_project` even though earlier dependency analysis and later removal-planning documents still treated those subsystems as `specfact-codebase` ownership. The result is an ambiguous runtime and design model:

- `specfact project import from-code` remained the public path even though the command's primary input is a source codebase
- brownfield analysis internals (`analyzers`, `comparators`, `parsers`, related agents/helpers) are not consistently owned across migration documents
- active follow-up changes can accidentally reinforce the wrong bundle boundary because the ownership decision is not explicit

This is not just a docs problem. The product needs a durable ownership rule for what belongs in `project` versus `code`, otherwise future bundle-surface fixes, prompt updates, dependency cleanup, and docs work will continue to drift.

## What Changes

- Define the canonical ownership boundary between the `project` and `codebase` categories after the plan-to-project rename.
- Reclassify code-first brownfield analysis behavior under `specfact code ...`, with `import` treated as codebase-owned rather than project-owned.
- Define `specfact project ...` as the owner of SpecFact bundle/workspace artifact lifecycle commands rather than generic code-ingestion behavior.
- Realign internal subsystem ownership so code-analysis internals live with `specfact-codebase` instead of remaining implicitly attached to `specfact-project`.
- Add a transition plan and validation coverage so pending changes and release docs do not reintroduce contradictory command ownership assumptions.

## Capabilities
### New Capabilities

- `project-codebase-ownership`: Explicit, testable ownership rules for `project` versus `codebase` command families and internal subsystems.

## Acceptance Criteria

- The spec and design explicitly define ownership by primary domain:
  - `specfact code ...` owns commands whose primary input is source code or runtime codebase behavior
  - `specfact project ...` owns commands whose primary subject is the SpecFact project bundle/workspace and its editable artifacts
- `specfact code import` is defined as the canonical codebase-owned command path in the target state, with a documented compatibility plan for any temporary legacy alias that remains during migration.
- Brownfield analysis internals currently split or ambiguously owned across migration documents are assigned to a single canonical bundle owner and the expected bundle boundaries are documented.
- Pending changes that touch command surface, docs, prompts, or migration cleanup reference the new ownership decision instead of encoding conflicting assumptions.
- Validation coverage is planned to fail if runtime command ownership and documented ownership diverge again.

## Dependencies

- `module-migration-06-core-decoupling-cleanup` documented the residual migrated subsystem inventory and still references code-analysis ownership boundaries that need resolution.
- `module-migration-10-bundle-command-surface-alignment` must align with the ownership decision in this change before finalizing public import command paths.
- `backlog-module-ownership-cleanup` is the architectural precedent for fixing post-migration ownership drift after the initial extraction wave.


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #408
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/408>
- **Last Synced Status**: proposed
- **Sanitized**: false
