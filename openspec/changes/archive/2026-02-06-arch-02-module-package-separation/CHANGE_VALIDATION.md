# Change Validation Report: arch-02-module-package-separation

**Validation Date**: 2026-02-05
**Change Proposal**: [proposal.md](./proposal.md)
**Validation Method**: Dry-run dependency and interface-impact analysis with temporary workspace artifacts in `/tmp`

## Executive Summary

- Breaking Changes: 1 class of breaking change detected (legacy non-`app` command symbol imports)
- Dependent Files: 35 affected (7 in `src/`, 28 in `tests/`)
- Impact Level: High
- Validation Result: Pass with approved scope extension (hybrid compatibility + decoupling strategy)
- User Decision: Approved hybrid strategy (temporary compatibility re-exports plus decoupling and boundary enforcement)

## Breaking Changes Detected

### Interface: `specfact_cli.commands.<module>` symbol surface

- **Type**: Public module export reduction risk
- **Old Signature**: Command modules expose `app` plus additional helpers/constants/functions used by internal code and tests (for example `_convert_project_bundle_to_plan_bundle`, `match_section_pattern`, `check_persona_ownership`, `AZURE_DEVOPS_RESOURCE`, `sync_spec_kit`, `is_constitution_minimal`).
- **New Signature (as currently described in proposal/tasks)**: Re-export shims in `src/specfact_cli/commands/*.py` expose only `app`.
- **Breaking**: Yes, if shims only export `app`.
- **Dependent Files**:
  - `src/specfact_cli/commands/generate.py`: imports `_convert_project_bundle_to_plan_bundle` from `specfact_cli.commands.plan`
  - `src/specfact_cli/commands/enforce.py`: imports `_convert_project_bundle_to_plan_bundle` from `specfact_cli.commands.plan`
  - `src/specfact_cli/commands/sync.py`: imports `_convert_project_bundle_to_plan_bundle` and `is_constitution_minimal`
  - `src/specfact_cli/commands/plan.py`: imports `sync_spec_kit` from `specfact_cli.commands.sync`
  - `src/specfact_cli/parsers/persona_importer.py`: imports `match_section_pattern` from `specfact_cli.commands.project_cmd`
  - `src/specfact_cli/generators/persona_exporter.py`: imports `match_section_pattern` from `specfact_cli.commands.project_cmd`
  - `src/specfact_cli/merge/resolver.py`: imports `check_persona_ownership` from `specfact_cli.commands.project_cmd`
  - `tests/` files: 28 files import non-`app` symbols from `specfact_cli.commands.*`

## Dependencies Affected

### Critical Updates Required

- Preserve compatibility for non-`app` symbol imports, either by:
  - Re-exporting required symbols from each `src/specfact_cli/commands/<name>.py` shim, or
  - Refactoring all imports to module-local paths in same change.
- Add explicit migration tasks for helper/constant/function import mapping and regression tests.

### Recommended Updates

- Add a compatibility policy section in `proposal.md` and `tasks.md` defining whether command modules are intentionally importable API surfaces or internal-only.
- Add test matrix that validates both command invocation and symbol-level imports during migration waves.

### Optional Updates

- Consolidate cross-command helper functions into shared core packages (`utils`, `models`, dedicated helper modules) to reduce command-to-command coupling over time.

## Impact Assessment

- **Code Impact**: High; command-to-command and parser/generator/resolver imports depend on non-`app` symbols.
- **Test Impact**: High; 28 tests import command-module helpers/constants/functions directly.
- **Documentation Impact**: Medium; docs should clarify compatibility guarantees for `specfact_cli.commands.*` imports during and after migration.
- **Release Impact**: Potentially Major if compatibility is not preserved; Minor if compatibility is explicitly preserved in shims.

## User Decision

**Decision**: Approved by user (2026-02-05): hybrid strategy.

**Approved strategy**:

1. **Temporary compatibility**: Preserve behavior during migration by re-exporting `app` and currently used non-`app` symbols in command shims.
2. **Active decoupling**: Move shared helper/constant logic out of command modules into stable shared packages and migrate imports.
3. **Boundary enforcement**: Add checks so new non-`app` imports from `specfact_cli.commands.*` fail CI.
4. **Exit criteria**: Drive non-`app` imports to zero and then reduce command shims toward `app`-only.

**Rationale**: This preserves runtime/test compatibility while achieving long-term module encapsulation and lower merge-conflict surface.

## Format Validation

- **proposal.md Format**: Pass
  - Title format: Correct (`# Change: ...`)
  - Required sections: Present (`Why`, `What Changes`, `Capabilities`, `Impact`)
  - "What Changes" format: Correct (bullet list with NEW/EXTEND markers)
  - "Capabilities" section: Present
  - "Impact" format: Correct
  - Source Tracking section: Present for public-facing repo
- **tasks.md Format**: Pass with one quality note
  - Section headers: Correct hierarchical numbering
  - Task format: Correct checklist numbering
  - Config compliance: Mostly pass
  - 2-hour maximum chunks: Not explicitly verifiable from current task granularity
  - Contract decorator tasks: Implicit only; should be explicit for any newly exposed public API adjustments
  - Test tasks: Present
  - Quality gate tasks: Present
  - Git workflow tasks: Present (branch first, PR last)
  - GitHub issue creation task: Present
- **specs Format**: Pass
  - Given/When/Then format: Verified
  - Existing pattern alignment: Verified
- **design.md Format**: Not applicable (no `design.md` yet; status is `ready`)
- **Format Issues Found**: 0 blocking
- **Format Issues Fixed**: 0
- **Config.yaml Compliance**: Pass (proposal/spec/tasks level)

## OpenSpec Validation

- **Status**: Pass
- **Validation Command**: `openspec validate arch-02-module-package-separation --strict`
- **Issues Found**: 0 blocking issues
- **Issues Fixed**: 0
- **Re-validated**: Yes

## Validation Artifacts

- Temporary workspace: `/tmp/specfact-validation-arch-02-module-package-separation-1770329891`
- Dependency scan (raw): `/tmp/specfact-validation-arch-02-module-package-separation-1770329891/dependency-raw.txt`
- Dependent files list: `/tmp/specfact-validation-arch-02-module-package-separation-1770329891/dependent-files.txt`
- Source dependents: `/tmp/specfact-validation-arch-02-module-package-separation-1770329891/dependent-src-files.txt`
- Test dependents: `/tmp/specfact-validation-arch-02-module-package-separation-1770329891/dependent-test-files.txt`
- Interface scaffold notes: `/tmp/specfact-validation-arch-02-module-package-separation-1770329891/interface-scaffold.txt`
