# Test-to-Scenario Mapping: arch-02-module-package-separation

## Scope

This mapping links OpenSpec scenarios in
`openspec/changes/arch-02-module-package-separation/specs/module-package-separation/spec.md`
to concrete tests and execution evidence.

## Scenario Mapping

### Requirement: Module-local command implementation

- Scenario: `Move command implementation into module package`
- Tests:
  - `tests/unit/specfact_cli/test_module_migration_compatibility.py::test_module_app_entrypoints_import_module_local_commands`
- Coverage:
  - Verifies each `src/specfact_cli/modules/<module>/src/app.py` imports `app` from module-local `commands`.
  - Verifies module package `src/` structure is present for all discovered module packages.

### Requirement: Backward-compatible command shims

- Scenario: `Legacy import path remains valid`
- Tests:
  - `tests/unit/specfact_cli/test_module_migration_compatibility.py::test_legacy_command_shims_reexport_module_app`
  - `tests/unit/specfact_cli/test_module_migration_compatibility.py::test_legacy_command_shims_reexport_public_symbols`
  - `tests/unit/specfact_cli/test_module_boundary_imports.py::test_no_legacy_non_app_command_imports_outside_compat_shims`
- Coverage:
  - Verifies legacy shim modules in `src/specfact_cli/commands/*.py` still expose the same `app` as module-local command implementations.
  - Verifies shim exports are reduced to the required compatibility surface (`app` plus any remaining in-repo legacy import requirements).
  - Verifies new non-`app` imports from `specfact_cli.commands.*` are blocked outside compatibility shims.

### Requirement: Phased migration with verification gates

- Scenario: `Tier-based migration progression`
- Tests:
  - `tests/unit/specfact_cli/registry/test_module_packages.py::test_registry_receives_example_command_when_registered`
  - QA command checks:
    - `hatch run smart-test` (pass)
    - `hatch run contract-test` (pass; contract exploration warnings only)
    - `specfact <command> --help` for all migrated commands (pass)
- Coverage:
  - Verifies registry bootstrap and command discoverability.
  - Verifies representative verification gates for migrated command set.

### Requirement: Module dependency declaration integrity

- Scenario: `Dependency declaration after migration`
- Verification:
  - Manifest review and migration tasks in `tasks.md` section `8.3` completed.
  - Dependency declarations validated through successful command bootstrap and targeted command help checks.

## Execution Evidence

- Command:
  - `hatch run pytest -q tests/unit/specfact_cli/test_module_migration_compatibility.py tests/unit/specfact_cli/test_module_boundary_imports.py tests/unit/specfact_cli/registry/test_module_packages.py::test_registry_receives_example_command_when_registered`
- Result:
  - `5 passed`

## Tier Verification Evidence

### Tier 1 (`drift`, `upgrade`, `validate`, `sdd`)

- Command:
  - `hatch run pytest -q tests/integration/commands/test_drift_command.py tests/unit/commands/test_update.py tests/integration/commands/test_sdd_contract_integration.py`
- Result:
  - `21 passed`

### Tier 2 (`auth`, `repro`, `enforce`, `migrate`, `spec`, `init`)

- Command:
  - `hatch run pytest -q tests/integration/commands/test_auth_commands_integration.py tests/integration/commands/test_repro_command.py tests/integration/commands/test_repro_sidecar.py tests/e2e/test_enforcement_workflow.py tests/e2e/test_init_command.py tests/integration/commands/test_spec_commands.py tests/e2e/test_specmatic_integration_e2e.py`
- Result:
  - `53 passed`

### Tier 3/4 (`contract`, `project`, `generate`, `sync`, `backlog`, `import_cmd`, `plan`)

- Command:
  - `hatch run pytest -q tests/integration/commands/test_contract_commands.py tests/integration/commands/test_project_commands.py tests/integration/commands/test_generate_command.py tests/integration/sync/test_sync_command.py tests/integration/commands/test_sync_intelligent_command.py tests/integration/backlog/test_backlog_filtering_integration.py tests/integration/commands/test_import_enrichment_contracts.py tests/integration/test_plan_command.py tests/unit/commands/test_plan_add_commands.py tests/unit/commands/test_plan_update_commands.py tests/unit/commands/test_plan_telemetry.py`
- Result:
  - `154 passed`

## TDD Order Note (Task 4.2)

The strict pre-implementation "expect failure first" step cannot be replayed after migration is already implemented.
This mapping captures retrospective targeted verification for the same scenarios and records current pass evidence.
