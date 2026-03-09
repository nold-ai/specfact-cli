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

## Additional pre-implementation failing run (2026-03-09 regressions, modules repo)

- **Timestamp (UTC):** 2026-03-09T21:05:54Z
- **Command:** `cd /home/dom/git/nold-ai/specfact-cli-modules && HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/unit/specfact_backlog/test_map_fields_command.py -q -k "reports_progress_for_selected_work_item_type_metadata or interactive_ignores_builtin_required_hierarchy_ids"`
- **Result:** FAIL

### Failure summary

- `tests/unit/specfact_backlog/test_map_fields_command.py::test_map_fields_reports_progress_for_selected_work_item_type_metadata` failed because `map-fields` still prints only the initial selected-type status line and never reports incremental follow-up field-metadata progress.
- `tests/unit/specfact_backlog/test_map_fields_command.py::test_map_fields_interactive_ignores_builtin_required_hierarchy_ids` failed before the prompt flow could complete because the command still treats `System.IterationId` and `System.AreaId` like mappable required fields and attempts provider-field fetches for them.

## Additional pre-implementation failing run (2026-03-09 regressions, core repo)

- **Timestamp (UTC):** 2026-03-09T21:05:54Z
- **Command:** `python -m pytest tests/unit/registry/test_module_installer.py -q -k satisfied_dependencies_without_warning`
- **Result:** FAIL

### Failure summary

- `tests/unit/registry/test_module_installer.py::test_install_module_logs_satisfied_dependencies_without_warning` failed because `install_module()` still logs `Dependency ... already satisfied` through `logger.warning(...)` during a successful bundled upgrade path.

## Additional post-implementation passing run (2026-03-09 regressions, modules repo)

- **Timestamp (UTC):** 2026-03-09T21:07:05Z
- **Command:** `cd /home/dom/git/nold-ai/specfact-cli-modules && HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/unit/specfact_backlog/test_map_fields_command.py -q -k "reports_progress_for_selected_work_item_type_metadata or interactive_ignores_builtin_required_hierarchy_ids"`
- **Result:** PASS

### Passing summary

- `backlog map-fields` now reports incremental `Fetching field metadata details N/M` progress while resolving follow-up metadata requests for the selected ADO work item type.
- The interactive mapping flow now skips non-mappable built-in required hierarchy identifiers such as `System.IterationId` and `System.AreaId`, so successful runs are gated only by actually mappable required fields.

## Additional post-implementation passing run (2026-03-09 regressions, core repo)

- **Timestamp (UTC):** 2026-03-09T21:07:05Z
- **Command:** `python -m pytest tests/unit/registry/test_module_installer.py -q -k satisfied_dependencies_without_warning`
- **Result:** PASS

### Passing summary

- Successful bundled installs and upgrades now keep already-satisfied dependency notices out of warning severity while preserving the message as non-warning runtime context.

## Additional pre-implementation failing run (2026-03-09 logger-output regression, core repo)

- **Timestamp (UTC):** 2026-03-09T21:19:19Z
- **Command:** `python -m pytest tests/unit/test_runtime.py -q -k bridge_logger_stays_off_console_when_debug_disabled`
- **Result:** FAIL

### Failure summary

- `tests/unit/test_runtime.py::TestBridgeLoggerOutput::test_bridge_logger_stays_off_console_when_debug_disabled` failed because the shared bridge logger still streamed raw `name | timestamp | level | message` lines to the console even when debug mode was disabled.

## Additional post-implementation passing run (2026-03-09 logger-output regression, core repo)

- **Timestamp (UTC):** 2026-03-09T21:20:09Z
- **Command:** `python -m pytest tests/unit/test_runtime.py -q -k bridge_logger_stays_off_console_when_debug_disabled`
- **Result:** PASS

### Passing summary

- Shared bridge logger diagnostics no longer leak raw log-formatted lines to the normal console when `--debug` is off.
- Explicit user-facing warnings still remain the responsibility of formatted prompt helpers rather than raw logger output.

## Additional pre-implementation failing run (2026-03-09 module-upgrade output regression, core repo)

- **Timestamp (UTC):** 2026-03-09T21:20:09Z
- **Command:** `python -m pytest tests/unit/modules/module_registry/test_commands.py -q -k one_line_per_module_with_versions`
- **Result:** FAIL

### Failure summary

- `tests/unit/modules/module_registry/test_commands.py::test_upgrade_without_module_name_reports_one_line_per_module_with_versions` failed because `specfact module upgrade` still reported upgraded modules as one comma-joined line and did not include `old -> new` version transitions.

## Additional post-implementation passing run (2026-03-09 module-upgrade output regression, core repo)

- **Timestamp (UTC):** 2026-03-09T21:23:21Z
- **Command:** `python -m pytest tests/unit/modules/module_registry/test_commands.py -q -k "upgrade_command or upgrade_without_module_name_upgrades_all_marketplace or one_line_per_module_with_versions"`
- **Result:** PASS

### Passing summary

- `specfact module upgrade` now prints upgraded modules one per line instead of collapsing them into a single comma-joined summary.
- Each upgraded module line now includes the resolved version transition in `old -> new` form, sourced from the post-install manifest written by the upgrade.
