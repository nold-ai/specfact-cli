## Pre-implementation failing run

- **Timestamp (UTC):** 2026-03-06T08:06:49Z
- **Command:** `/bin/bash -lc 'HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/unit/validation/test_command_audit.py tests/unit/registry/test_module_discovery.py tests/unit/specfact_cli/registry/test_module_packages.py tests/integration/test_command_package_runtime_validation.py -q'`
- **Result:** FAIL

### Failure summary

- `tests/unit/validation/test_command_audit.py` failed during collection with `ModuleNotFoundError: No module named 'specfact_cli.validation'`.
- `tests/integration/test_command_package_runtime_validation.py` failed during collection with the same missing helper-module error.
- This is the expected first red phase for tasks 3.1 and 3.2: the command-audit inventory/runtime helper has not been implemented yet.

## Post-implementation passing run

- **Timestamp (UTC):** 2026-03-06T08:43:12Z
- **Command:** `/bin/bash -lc 'HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/unit/validation/test_command_audit.py tests/unit/registry/test_module_discovery.py tests/unit/specfact_cli/registry/test_module_packages.py tests/integration/test_command_package_runtime_validation.py -q'`
- **Result:** PASS

### Passing summary

- The command-audit helper now inventories the exported CLI surface for core plus official bundle roots and verifies 82 command paths.
- The temp-home acceptance run installs the five official marketplace bundles into an isolated environment and executes every audited command path without leaking internal module-discovery or protocol-compliance diagnostics.
- The canonical `~/.specfact/modules` startup regression is covered by the module-discovery tests and no longer reports a duplicate/shadow warning when the working directory is the user home root.

## Additional pre-implementation failing run

- **Timestamp (UTC):** 2026-03-06T09:37:00Z
- **Command:** `HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest modules/backlog-core/tests/unit/test_add_command.py tests/unit/adapters/test_ado_backlog_adapter.py tests/integration/test_command_package_runtime_validation.py -q -k 'saved_required_custom_field or validates_and_forwards_custom_fields or applies_provider_custom_fields or overlap_is_silent'`
- **Result:** FAIL

### Failure summary

- `modules/backlog-core/tests/unit/test_add_command.py::test_backlog_add_ado_requires_saved_required_custom_field` failed because `backlog add` succeeded without enforcing saved required custom-field metadata.
- `modules/backlog-core/tests/unit/test_add_command.py::test_backlog_add_ado_validates_and_forwards_custom_fields` failed because `--custom-field` is not exposed on `backlog add` yet.
- `tests/unit/adapters/test_ado_backlog_adapter.py::TestAdoBacklogAdapter::test_create_issue_applies_provider_custom_fields` failed because `AdoAdapter.create_issue()` ignores provider custom field payloads.
- `tests/integration/test_command_package_runtime_validation.py::test_backlog_core_and_marketplace_overlap_is_silent_in_normal_output` failed before validation because the seeded bundled `backlog-core` module tripped integrity verification in the temp-home setup and still needs a stable overlap-validation path.

## Additional pre-implementation failing run (modules repo)

- **Timestamp (UTC):** 2026-03-06T09:37:00Z
- **Command:** `cd /home/dom/git/nold-ai/specfact-cli-modules && HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/unit/specfact_backlog/test_map_fields_command.py -q -k progress_for_selected_work_item_type_metadata`
- **Result:** FAIL

### Failure summary

- `tests/unit/specfact_backlog/test_map_fields_command.py::test_map_fields_reports_progress_for_selected_work_item_type_metadata` failed because `map-fields` prints nothing between work item type selection and the next prompt/save step, so the command appears stalled while fetching required-field and picklist metadata.

## Additional pre-implementation failing run (modules repo adapter interop)

- **Timestamp (UTC):** 2026-03-06T09:38:00Z
- **Command:** `cd /home/dom/git/nold-ai/specfact-cli-modules && HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/unit/specfact_backlog/test_refine_adapter_contract.py -q`
- **Result:** FAIL

### Failure summary

- `tests/unit/specfact_backlog/test_refine_adapter_contract.py::test_fetch_backlog_items_accepts_core_backlog_adapter` failed with `NotImplementedError: Adapter ado does not implement BacklogAdapter interface`, confirming the bundle-local adapter type mismatch against the core adapter contract.

## Additional post-implementation passing run

- **Timestamp (UTC):** 2026-03-06T09:45:00Z
- **Command:** `HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest modules/backlog-core/tests/unit/test_add_command.py tests/unit/adapters/test_ado_backlog_adapter.py tests/integration/test_command_package_runtime_validation.py -q -k 'saved_required_custom_field or validates_and_forwards_custom_fields or applies_provider_custom_fields or overlap_is_silent'`
- **Result:** PASS

### Passing summary

- `backlog add` now enforces saved required ADO custom-field metadata, validates allowed picklist values, and forwards resolved provider fields into the create payload.
- `AdoAdapter.create_issue()` now applies forwarded provider custom fields into the JSON patch document.
- The temp-home runtime validation path now tolerates the expected `backlog-core` plus `nold-ai/specfact-backlog` overlap without leaking duplicate-subcommand warnings in normal output.

## Additional post-implementation passing run (modules repo)

- **Timestamp (UTC):** 2026-03-06T09:45:00Z
- **Command:** `cd /home/dom/git/nold-ai/specfact-cli-modules && HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/unit/specfact_backlog/test_map_fields_command.py tests/unit/specfact_backlog/test_refine_adapter_contract.py -q -k "progress_for_selected_work_item_type_metadata or accepts_core_backlog_adapter"`
- **Result:** PASS

### Passing summary

- The backlog marketplace bundle now shares the core backlog adapter contract, so `refine ado` no longer fails on the adapter type check.
- `backlog map-fields` now emits an explicit status line before fetching required-field and picklist metadata for the selected work item type, eliminating the silent post-selection stall.
