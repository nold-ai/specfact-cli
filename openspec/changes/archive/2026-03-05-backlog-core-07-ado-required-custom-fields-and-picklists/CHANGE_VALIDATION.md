# Change Validation Report: backlog-core-07-ado-required-custom-fields-and-picklists

**Validation Date**: 2026-03-05T14:21:28Z  
**Change Proposal**: [proposal.md](./proposal.md)  
**Validation Method**: Dry-run dependency/surface analysis + strict OpenSpec validation

## Executive Summary

- Breaking Changes: 0 detected / 0 resolved
- Dependent Files: 7 critical paths identified
- Impact Level: Medium
- Validation Result: Pass (with scope-alignment updates required)
- User Decision: N/A (no breaking API changes; scope refinement recommended)

## Breaking Changes Detected

No public interface-breaking changes were detected in the proposed behavior.

## Key Scope Findings (Post-Modularization)

The bug report remains **valid**, but parts of the implementation scope are now split across repositories/modules after 0.40.x modularization:

- `backlog map-fields` ADO mapping flow now lives in `specfact-cli-modules` (`specfact-backlog` package), not `src/specfact_cli/commands/backlog_commands.py`.
- `backlog add` command path is implemented in the `backlog-core` module command (`modules/backlog-core/src/backlog_core/commands/add.py`) and currently lacks `--custom-field` handling.
- ADO create path in core adapter (`src/specfact_cli/adapters/ado.py`) currently does not consume custom mapped provider fields for create-time preflight validation.

## Dependencies Affected

### Critical Updates Required

- `/home/dom/git/nold-ai/specfact-cli-modules/packages/specfact-backlog/src/specfact_backlog/backlog/commands.py`
  - `map_fields` currently maps canonical fields and framework only; no required-field/picklist metadata persistence (`~5270-5550`).
- `/home/dom/git/nold-ai/specfact-cli/modules/backlog-core/src/backlog_core/commands/add.py`
  - `add` has no `--custom-field` option and no required/picklist validation path before create (`~465-667`).
- `/home/dom/git/nold-ai/specfact-cli/src/specfact_cli/adapters/ado.py`
  - `create_issue` builds patch from canonical fields only and does not apply/validate custom mapped provider fields (`~3336-3457`).

### Recommended Updates

- `/home/dom/git/nold-ai/specfact-cli-modules/tests/*` for `map-fields` required/allowed-values metadata persistence.
- `/home/dom/git/nold-ai/specfact-cli/modules/backlog-core/tests/unit/test_add_command.py` for `--custom-field`, fail-fast validation, and hints.
- `/home/dom/git/nold-ai/specfact-cli/tests/unit/adapters/test_ado_backlog_adapter.py` for provider field mapping + allowed-values behavior on create.
- Backlog docs in `specfact-cli-modules/docs/` and command docs in `specfact-cli/docs/` where add/map-fields behavior is surfaced.

## Impact Assessment

- **Code Impact**: Moderate, cross-repo (`specfact-cli-modules` + `specfact-cli`) for command + adapter behavior alignment.
- **Test Impact**: Moderate/high due TDD-first coverage across both repos.
- **Documentation Impact**: Required to prevent stale 0.39-era guidance.
- **Release Impact**: Patch for CLI behavior fix, plus module package version bump(s) where touched.

## Format Validation

- **proposal.md Format**: Pass
- **tasks.md Format**: Pass
- **specs Format**: Pass
- **Config.yaml Compliance**: Pass

## OpenSpec Validation

- **Status**: Pass
- **Command**: `openspec validate backlog-core-07-ado-required-custom-fields-and-picklists --strict`
- **Issues Found/Fixed**: 0

## Revalidation Update (2026-03-05)

- Added scope coverage for markdown-first rendering of ADO multiline text fields (description + acceptance criteria), including html-like input normalization to markdown prior to submit.
- Re-ran strict validation after spec delta update:
  - `openspec validate backlog-core-07-ado-required-custom-fields-and-picklists --strict`
  - Result: Pass

## Lifecycle Update (2026-03-05)

- Modules implementation/deployment status:
  - `specfact-cli-modules` PR <https://github.com/nold-ai/specfact-cli-modules/pull/9> merged to `dev`
  - promotion PR <https://github.com/nold-ai/specfact-cli-modules/pull/11> merged to `main`
  - decoupled publish workflow verification run pass:
    - <https://github.com/nold-ai/specfact-cli-modules/actions/runs/22725544343>
- Source issue #337 remains open in `specfact-cli` (core-side closure/final sync still pending).
- Archive readiness: **not ready yet** (core-side PR/finalization tasks remain open in `tasks.md`).

## Delivery Status Sync (2026-03-05)

- Modules repository delivery has been merged:
  - `nold-ai/specfact-cli-modules#9` (bugfix + decoupled modules publish workflow)
  - `nold-ai/specfact-cli-modules#11` (`dev` -> `main` promotion)
- Publish workflow runtime verification:
  - <https://github.com/nold-ai/specfact-cli-modules/actions/runs/22725544343> (pass)
- Source issue remains open in core tracking:
  - <https://github.com/nold-ai/specfact-cli/issues/337>

## Archive Readiness

- **Not ready to archive yet.**
- Remaining blockers in this change record:
  - Task `7.2` core-side coordinated PR linkage/final state update is still pending.
  - Outstanding quality/documentation/release-note checkboxes (`5.3`, `6.1`, `6.3`) remain open in task list and should be explicitly resolved or descoped before archive.

## Validation Artifacts

- `openspec status --change backlog-core-07-ado-required-custom-fields-and-picklists --json`
- `openspec instructions apply --change backlog-core-07-ado-required-custom-fields-and-picklists --json`
- `openspec validate backlog-core-07-ado-required-custom-fields-and-picklists --strict`
- Dependency discovery:
  - `rg -n "map-fields|required_fields_by_work_item_type|allowed_values|--custom-field|create_issue\\(" ...`
  - file-level inspection in `specfact-cli-modules` and `specfact-cli` code paths noted above
