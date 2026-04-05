# TDD Evidence: module-migration-10-bundle-command-surface-alignment

## Pre-Implementation Failing Run

- Timestamp: 2026-03-10T23:24:22+01:00
- Command:

```bash
python -m pytest tests/integration/test_command_package_runtime_validation.py tests/unit/registry/test_category_groups.py tests/unit/test_backlog_module_ownership_cleanup.py -q
```

- Failure summary:
  - `tests/integration/test_command_package_runtime_validation.py::test_command_audit_help_cases_execute_cleanly_in_temp_home`
    - In the direct `python -m pytest` shell, spawned CLI subprocesses used `/usr/local/bin/python` and failed before command auditing with `ModuleNotFoundError: No module named 'typer'`.
    - Prior repo failure capture showed the actual command-surface drift under the installed marketplace backlog bundle: `backlog add`, `backlog analyze-deps`, `backlog delta`, `backlog diff`, `backlog promote`, `backlog sync`, and `backlog verify-readiness` were missing at runtime.
  - `tests/integration/test_command_package_runtime_validation.py::test_marketplace_backlog_bundle_registers_cleanly_without_core_overlap`
    - Same subprocess interpreter issue in the direct shell (`typer` missing), masking the bundle-surface assertion.
  - `tests/unit/registry/test_category_groups.py::test_bootstrap_with_category_grouping_disabled_registers_flat_commands`
    - Expected `code` and `govern` not to appear, but current flat bundle registration keeps those bundle-native root commands even when category grouping is disabled.
  - `tests/unit/registry/test_category_groups.py::test_spec_api_validate_routes_correctly`
    - Expected `spec api --help` to resolve, but current runtime mounts the bundle-native `spec` root directly, so `spec api` is not registered.
  - `tests/unit/test_backlog_module_ownership_cleanup.py::test_core_repo_no_longer_ships_backlog_owned_command_surfaces`
    - Failed because `modules/backlog-core` still exists in the workspace, but current contents are generated residue (`logs/`, `__pycache__/`) rather than shipped command source.

## Post-Implementation Passing Run

- Timestamp: 2026-03-10T23:35:57+01:00
- Command:

```bash
/bin/bash -lc 'HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch test -- tests/integration/test_command_package_runtime_validation.py tests/unit/registry/test_category_groups.py tests/unit/test_backlog_module_ownership_cleanup.py -q'
```

- Result:
  - `12 passed in 197.87s (0:03:17)`
  - Runtime validation passed cleanly after rerunning against the updated modules state.
