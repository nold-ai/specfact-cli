# TDD Evidence: module-migration-08-release-suite-stabilization

## Pre-implementation failing evidence

Timestamp: 2026-03-06 Europe/Berlin

### Broader baselines

- Unit suite baseline log: `logs/tests/unit_test_run_20260306_005445.log`
  - Result: `73 failed, 702 passed, 2 skipped`
- Integration suite baseline log: `logs/tests/integration_test_run_20260306_005734.log`
  - Result: `118 failed, 64 passed`

### Representative targeted failures

1. `HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/unit/groups/test_codebase_group.py -q`
   - Result: `1 failed`
   - Failure: test assumes `code` group is always registered in core, but current lean-core registry only has `init`, `module`, `upgrade`, `backlog`, `project` in the local state.

2. `HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/unit/modules/init/test_first_run_selection.py -q`
   - Result: `5 failed, 14 passed`
   - Failures:
     - installer-call tests patch `first_run_selection.install_bundles_for_init`, while command code calls the alias imported into `commands.py`
     - invalid profile path fails at `@require` precondition instead of returning the intended user-facing CLI error.

3. `HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/integration/test_category_group_routing.py -q`
   - Result: `1 failed, 2 passed`
   - Failure: retained integration test invokes `specfact code analyze --help` without mocking `specfact-codebase` as installed.

4. `HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/unit/registry/test_cross_bundle_imports.py -q`
   - Result: `3 failed`
   - Failure: tests still read removed in-core bundle files under `src/specfact_cli/modules/analyze|generate|enforce/...`.

## Planned implementation direction

- Rewrite or retire core tests that still assume extracted bundle files/commands remain inside `specfact-cli`.
- Fix `init` CLI validation so invalid user input produces a CLI error instead of an `icontract` violation.
- Update retained command-group tests to explicitly simulate installed bundles when asserting grouped command availability.

## Post-implementation evidence

### Targeted retained-core buckets

1. `HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/unit/groups/test_codebase_group.py tests/unit/modules/init/test_first_run_selection.py tests/unit/modules/test_reexport_shims.py tests/unit/utils/test_suggestions.py tests/integration/test_category_group_routing.py tests/e2e/test_first_run_init.py -q`
   - Result: `42 passed`

2. `HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/unit/specfact_cli/registry/test_command_registry.py tests/unit/specfact_cli/registry/test_help_cache.py -q`
   - Result: `19 passed`

### Broader reruns

3. `HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/integration -q`
   - Result: `143 passed`

4. `HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/e2e -q`
   - Result: `41 passed, 1 skipped`

5. `HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/unit -q`
   - Result: `2050 passed, 1 skipped`
