# Change Validation Report: module-migration-04-remove-flat-shims

**Validation Date**: 2026-02-28T01:06:06+01:00  
**Change Proposal**: [proposal.md](./proposal.md)  
**Validation Method**: Dry-run validation per /wf-validate-change workflow; OpenSpec validate --strict; dependency grep.

## Executive Summary

- **Breaking Changes**: 1 (intentional): removal of 17 flat CLI command names from root surface.
- **Dependent Files**: 4 affected (1 source, 3 test files).
- **Impact Level**: Medium (breaking UX; migration path documented).
- **Validation Result**: Pass
- **User Decision**: N/A (change is intentionally breaking; no scope extension requested).

## Breaking Changes Detected

### Interface: Root CLI command list

- **Type**: Command removal (17 flat shim names no longer registered).
- **Old behaviour**: `specfact --help` listed core + category groups + 17 flat shims (e.g. `validate`, `analyze`, `plan`). `specfact validate ...` delegated to `specfact code validate ...` with optional deprecation message.
- **New behaviour**: `specfact --help` lists only core + category groups. `specfact validate` returns "No such command".
- **Breaking**: Yes (by design for 0.40.x).
- **Dependent files**:
  - **tests/unit/registry/test_category_groups.py**: `test_flat_shim_validate_emits_deprecation_in_copilot_mode`, `test_flat_shim_validate_silent_in_cicd_mode` — must be removed or rewritten (assert flat command absent or error).
  - **tests/integration/test_category_group_routing.py**: `test_validate_shim_help_exits_zero` — must be removed or changed to assert `specfact code validate --help` (or assert `specfact validate` fails).
  - **tests/integration/commands/test_validate_sidecar.py**: Invokes `app` with `["validate", "sidecar", ...]` — should be updated to `["code", "validate", "sidecar", ...]` for 0.40.x.

## Dependencies Affected

### Critical updates required

- **src/specfact_cli/registry/module_packages.py**: Remove `FLAT_TO_GROUP`, `_make_shim_loader()`, and the shim-registration loop in `_register_category_groups_and_shims()`; rename to `_register_category_groups()` and keep only group registration.

### Recommended updates (tests)

- **tests/unit/registry/test_category_groups.py**: Remove or rewrite tests that assert flat shim deprecation/silent behaviour; add/keep tests that root help contains only core + groups.
- **tests/integration/test_category_group_routing.py**: Remove `test_validate_shim_help_exits_zero` or replace with test that `specfact validate` fails and suggests `specfact code validate`.
- **tests/integration/commands/test_validate_sidecar.py**: Update invocations from `["validate", "sidecar", ...]` to `["code", "validate", "sidecar", ...]`.

## Impact Assessment

- **Code impact**: Single module (`module_packages.py`) reduced by removing shim layer; call sites of flat commands (scripts, docs) must migrate to category form.
- **Test impact**: 3 test files need updates; no new interfaces, only removal of shim behaviour.
- **Documentation impact**: commands.md, getting-started.md, README.md, CHANGELOG.md (0.40.0 BREAKING entry).
- **Release impact**: Minor version 0.40.0 (breaking CLI surface).

## User Decision

**Decision**: Proceed with change as proposed (intentionally breaking).  
**Rationale**: Migration path documented in proposal; 0.40.x scope agreed.  
**Next steps**: Implement per tasks.md; create GitHub issue and link in proposal Source Tracking; run specfact sync bridge to sync issue.

## Format Validation

- **proposal.md format**: Pass
  - Title format: Correct (`# Change: Remove Flat Shims — ...`)
  - Required sections: All present (Why, What Changes, Capabilities, Impact)
  - "What Changes" format: Correct (REMOVE/MODIFY/KEEP bullets)
  - "Capabilities" section: Present
  - "Impact" format: Correct
  - Source Tracking section: Present (placeholders for GitHub issue)
- **tasks.md format**: Pass
  - Section headers: Correct (`## 1. Branch and prep`, etc.)
  - Task format: Correct (`- [ ] 1.1 ...`)
  - Sub-task format: Correct
  - Config compliance: Branch creation first (1.1), PR last (6.2); GitHub issue task (6.1). Optional: add worktree bootstrap pre-flight in 1.x if using worktree.
- **specs format**: Pass
  - Delta headers: REMOVED Requirements, MODIFIED Requirements with Scenario blocks
  - Parsed deltas: 2 (1 MODIFIED, 1 REMOVED)
- **design.md**: Not present (optional for this change).
- **Config.yaml compliance**: Pass.

## OpenSpec Validation

- **Status**: Pass
- **Validation command**: `openspec validate module-migration-04-remove-flat-shims --strict`
- **Issues found**: 0 (after adding spec delta under `specs/category-command-groups/spec.md`)
- **Issues fixed**: 1 (added spec delta so change has at least one delta with Scenario blocks)
- **Re-validated**: Yes

## Validation Artifacts

- Spec delta added: `openspec/changes/module-migration-04-remove-flat-shims/specs/category-command-groups/spec.md`
- Dependency search: `rg FLAT_TO_GROUP|_make_shim_loader|_register_category_groups_and_shims` and `rg validate.*--help|flat shim|deprecation` in tests.
