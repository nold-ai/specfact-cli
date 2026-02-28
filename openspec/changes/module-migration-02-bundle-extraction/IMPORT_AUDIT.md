# Import Audit: module-migration-02-bundle-extraction (Phase 0)

## Scope

- Audited module source under `src/specfact_cli/modules/**.py` for cross-bundle private imports.
- Bundle/category mapping source: `src/specfact_cli/modules/*/module-package.yaml`.

## Method

Automated AST walk over all module Python files.

- Import target pattern inspected: `specfact_cli.modules.<target_module>...`
- A match is treated as **cross-bundle private** when:
  - source module category != target module category.

Command used:

```bash
python3 - <<'PY'
# AST scanner over src/specfact_cli/modules/**/*.py
# Maps module -> category from module-package.yaml
# Emits cross-bundle private imports where source/target categories differ.
PY
```

## Findings

- Cross-bundle private imports found: **0**

No `specfact_cli.modules.<other-bundle-module>` private imports crossing bundle boundaries were found in the current tree.

## Additional Coupling Candidates (from Phase 0 test gate)

The failing gate tests highlighted plan-model coupling in:

- `src/specfact_cli/modules/generate/src/commands.py`
- `src/specfact_cli/modules/enforce/src/commands.py`

Applied factoring to shared/common layer:

- Added `src/specfact_cli/common/bundle_factory.py`
  - `create_empty_project_bundle(...)`
  - `create_contract_anchor_feature()`
- Updated `generate` and `enforce` modules to use common helper functions instead of directly importing `specfact_cli.models.plan` for these cases.

## Post-factor check

- Cross-bundle private imports remain: **0**
- Targeted phase-0 import-gate tests now have implementation support to proceed to passing run in `4.3`.
