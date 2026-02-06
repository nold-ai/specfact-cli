# Change Validation Report: arch-03-module-lifecycle-management

**Validation Date**: 2026-02-06 18:35:22Z
**Change Proposal**: [proposal.md](./proposal.md)
**Validation Method**: Dry-run interface/dependency simulation in temporary workspace

## Executive Summary

- Breaking Changes: 1 potential behavior break detected, 0 unmitigated
- Dependent Files: 27 identified in impacted surfaces
- Impact Level: Medium
- Validation Result: Pass (safe to implement)
- User Decision: Proceed without scope extension; keep compatibility safeguards in implementation

## Breaking Changes Detected

### Interface/Behavior: `specfact init --disable-module <id>`

- **Type**: Behavioral contract tightening
- **Old Behavior**: Disable operation persisted directly
- **New Behavior**: Disable blocked if enabled dependents require the module (unless `--force`)
- **Breaking**: Potentially yes for automation/scripts that currently rely on unconditional disable
- **Mitigation in scope**:
  - Explicit `--force` override
  - Clear error message listing dependent modules
  - Documentation updates for new disable semantics

### Interface/Behavior: Cross-module helper imports

- **Type**: Internal import path migration (module code)
- **Old Behavior**: module-to-module imports from `specfact_cli.modules.<other>.src.commands`
- **New Behavior**: shared helpers in `specfact_cli.utils.bundle_converters`
- **Breaking**: Not if wrappers are retained in `plan/src/commands.py` and `sdd/src/commands.py`
- **Mitigation in scope**:
  - Keep compatibility wrappers for `_convert_*` and `is_constitution_minimal`
  - Update module imports in sync/generate/enforce

## Dependencies Affected

### Critical Updates Required

- `src/specfact_cli/modules/init/src/commands.py`: add safe-disable gate and preserve clear CLI UX.
- `src/specfact_cli/registry/module_packages.py`: add compatibility/dependency checks without startup hard-fail.
- `src/specfact_cli/registry/module_state.py`: add reverse dependency helper used by safe-disable logic.
- `src/specfact_cli/modules/sync/src/commands.py`: replace cross-module helper imports with core utility imports.
- `src/specfact_cli/modules/generate/src/commands.py`: replace cross-module helper imports with core utility imports.
- `src/specfact_cli/modules/enforce/src/commands.py`: replace cross-module helper imports with core utility imports.
- `tests/unit/specfact_cli/test_module_boundary_imports.py`: extend guard for cross-module non-`app` imports.

### Recommended Updates

- `tests/unit/specfact_cli/registry/test_module_packages.py`: add assertions for `core_compatibility` parsing/validation behavior.
- `tests/unit/specfact_cli/registry/test_init_module_state.py`: add safe-disable behavior coverage.
- New tests planned in tasks (`test_module_dependencies.py`, `test_version_constraints.py`, `test_bundle_converters.py`).

### Optional / No Immediate Action

- Existing tests importing `_convert_*` from plan commands (18 files) are compatible if wrapper strategy is kept.

## Impact Assessment

- **Code Impact**: Registry lifecycle logic, init disable flow, cross-module helper import paths, new shared utility module.
- **Test Impact**: New contract-first tests required plus boundary guard extension; existing helper-import tests remain stable with wrappers.
- **Documentation Impact**: Update CLI/module lifecycle docs for `core_compatibility`, dependency enforcement, and `--force` behavior.
- **Release Impact**: Minor (`0.29.0`) remains appropriate; behavior change is intentional and mitigated.

## User Decision

**Decision**: Proceed

**Rationale**: Detected breaking risk is bounded and explicitly mitigated (`--force` + compatibility wrappers). No additional proposal scope expansion is required at validation stage.

**Next Steps**:

1. Keep wrapper compatibility explicitly during implementation.
2. Add tests before code per tasks section 4.
3. Validate strict gates after implementation tasks.

## Format Validation

- **proposal.md Format**: Pass
  - Title format: Correct (`# Change: ...`)
  - Required sections: Present (`Why`, `What Changes`, `Capabilities`, `Impact`)
  - `What Changes` format: Correct bullet list with NEW/EXTEND markers
  - `Capabilities` section: Present
  - `Impact` section: Present
  - Source Tracking: Present and populated (issue #203)
- **tasks.md Format**: Pass
  - Section headers: Hierarchical numbered groups present
  - Task format: Checkbox format present
  - Config compliance:
    - TDD/SDD ordering block: Present
    - Test tasks before implementation tasks: Present
    - Quality gate tasks: Present
    - Git workflow tasks: Present (branch first, PR last)
    - GitHub issue task: Present
  - **Note**: Placeholder `<issue-number>` remains in branch/PR task text; acceptable for proposal stage but should be resolved before apply.
- **specs Format**: Pass
  - Given/When/Then scenarios present
  - Requirement statements are clear and test-mappable
- **design.md Format**: Pass
  - Architectural decisions, risks, and mitigations documented
  - Sequence diagram not required for this non-multi-repo control-plane change
- **Format Issues Found**: 0 blocking, 1 advisory placeholder note
- **Config.yaml Compliance**: Pass

## OpenSpec Validation

- **Status**: Pass
- **Validation Command**: `openspec validate arch-03-module-lifecycle-management --strict`
- **Issues Found**: 0
- **Issues Fixed**: 0
- **Re-validated**: Yes

## Validation Artifacts

- Temporary workspace: `/tmp/specfact-validation-arch-03-module-lifecycle-management-1770402822`
- Interface scaffolds: `/tmp/specfact-validation-arch-03-module-lifecycle-management-1770402822/interface_scaffolds.md`
- Dependency graph: `/tmp/specfact-validation-arch-03-module-lifecycle-management-1770402822/dependency_graph.md`
- Dependency file list: `/tmp/specfact-validation-arch-03-module-lifecycle-management-1770402822/dependency_files.txt`
