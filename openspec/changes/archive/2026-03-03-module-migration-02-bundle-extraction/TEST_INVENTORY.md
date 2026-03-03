# TEST_INVENTORY.md

## 18.1.1 Module-to-bundle mapping (17 migrated modules)

- `project` -> `specfact-project`
- `plan` -> `specfact-project`
- `import_cmd` -> `specfact-project`
- `sync` -> `specfact-project`
- `migrate` -> `specfact-project`
- `backlog` -> `specfact-backlog`
- `policy_engine` -> `specfact-backlog`
- `analyze` -> `specfact-codebase`
- `drift` -> `specfact-codebase`
- `validate` -> `specfact-codebase`
- `repro` -> `specfact-codebase`
- `contract` -> `specfact-spec`
- `spec` -> `specfact-spec`
- `sdd` -> `specfact-spec`
- `generate` -> `specfact-spec`
- `enforce` -> `specfact-govern`
- `patch_mode` -> `specfact-govern`

## 18.1.2 Unit-test inventory (bundle-related in specfact-cli)

### Primary module tests

- `tests/unit/modules/plan/test_module_io_contract.py` -> `tests/unit/modules/test_module_io_contracts.py` (migrated, aggregated)
- `tests/unit/modules/sync/test_module_io_contract.py` -> `tests/unit/modules/test_module_io_contracts.py` (migrated, aggregated)
- `tests/unit/modules/backlog/test_module_io_contract.py` -> `tests/unit/modules/test_module_io_contracts.py` (migrated, aggregated)
- `tests/unit/modules/generate/test_module_io_contract.py` -> `tests/unit/modules/test_module_io_contracts.py` (migrated, aggregated)
- `tests/unit/modules/enforce/test_module_io_contract.py` -> `tests/unit/modules/test_module_io_contracts.py` (migrated, aggregated)
- `tests/unit/bundles/test_bundle_layout.py` -> `tests/unit/test_repo_layout.py` (migrated, scoped to modules repo)

### Additional bundle-coupled unit suites (deferred)

- `tests/unit/commands/test_plan_telemetry.py` -> target `tests/unit/specfact_project/` (deferred: heavy CLI patching)
- `tests/unit/commands/test_backlog_commands.py` -> target `tests/unit/specfact_backlog/` (deferred: adapter mocks + CLI glue)
- `tests/unit/commands/test_project_cmd.py` -> target `tests/unit/specfact_project/` (deferred: core CLI dependencies)
- `tests/unit/commands/test_import_feature_validation.py` -> target `tests/unit/specfact_project/` (deferred)
- `tests/unit/commands/test_backlog_*` suite -> target `tests/unit/specfact_backlog/` (deferred)
- `tests/unit/specfact_cli/modules/test_patch_mode.py` -> target `tests/unit/specfact_govern/` (deferred: package path rewrite)

## 18.1.3 Integration-test inventory (bundle command usage)

- `tests/integration/test_plan_command.py` -> target `tests/integration/specfact_project/` (deferred: interactive prompt patching)
- `tests/integration/commands/test_generate_command.py` -> target `tests/integration/specfact_spec/` (deferred)
- `tests/integration/commands/test_enforce_command.py` -> target `tests/integration/specfact_govern/` (deferred)
- `tests/integration/commands/test_repro_command.py` -> target `tests/integration/specfact_codebase/` (deferred)
- `tests/integration/sync/test_sync_command.py` -> target `tests/integration/specfact_project/` (deferred)
- `tests/integration/test_bundle_install.py` -> target `tests/integration/` (deferred: core registry/install path)
- New migrated smoke: `tests/integration/test_bundle_command_apps.py` (added in modules repo)

## 18.1.4 E2E inventory (bundle behavior)

- `tests/e2e/test_bundle_extraction_e2e.py` -> target `tests/e2e/` (deferred: full CLI harness)
- `tests/e2e/test_plan_review_*` -> target `tests/e2e/specfact_project/` (deferred)
- `tests/e2e/backlog/test_backlog_*` -> target `tests/e2e/specfact_backlog/` (deferred)
- New migrated smoke: `tests/e2e/test_bundle_help_smoke.py` (added in modules repo)

## Notes

- Migration in this pass prioritizes low-coupling tests that validate bundle module contracts and command surface availability.
- High-coupling integration/e2e suites remain dependent on `specfact_cli` runtime orchestration and are tracked as deferred migration work for follow-up tasks.
