# Backlog Ownership Matrix

## Command Ownership

### Core CLI ownership that must be removed or retired

- `src/specfact_cli/groups/backlog_group.py`
  - Owns the top-level `backlog` category group and the `policy` member registration path.
- `src/specfact_cli/commands/backlog_commands.py`
  - Backward-compatible shim that loads `specfact_backlog.backlog.commands` directly from core.
- `modules/backlog-core/module-package.yaml`
  - Registers the built-in `backlog-core` package into the `specfact-backlog` bundle namespace.
- `modules/backlog-core/src/backlog_core/main.py`
  - Directly owns `backlog add`, `backlog analyze-deps`, `backlog trace-impact`, `backlog sync`, `backlog diff`, `backlog promote`, `backlog verify-readiness`, `backlog generate-release-notes`, and `backlog delta *`.

### Module ownership that already exists

- `/home/dom/git/nold-ai/specfact-cli-modules/packages/specfact-backlog/module-package.yaml`
  - Registers `nold-ai/specfact-backlog` as the official backlog bundle.
- `/home/dom/git/nold-ai/specfact-cli-modules/packages/specfact-backlog/src/specfact_backlog/backlog/commands.py`
  - Owns `backlog daily`, `backlog refine`, `backlog init-config`, `backlog map-fields`, ceremony aliases, and auth flows.
- `/home/dom/git/nold-ai/specfact-cli-modules/packages/specfact-backlog/src/specfact_backlog/policy_engine/commands.py`
  - Owns policy-engine command behavior for the backlog bundle.

## Prompt And Template Ownership

### Core prompt/template assets that must move or stop exporting as backlog-owned resources

- `resources/prompts/specfact.backlog-add.md`
- `resources/prompts/specfact.backlog-daily.md`
- `resources/prompts/specfact.backlog-refine.md`
- `resources/prompts/specfact.sync-backlog.md`
- `resources/templates/backlog/defaults/*`
- `resources/templates/backlog/field_mappings/*`
- `resources/templates/backlog/frameworks/*`
- `resources/templates/backlog/personas/*`
- `resources/templates/backlog/providers/*`
- `src/specfact_cli/templates/defaults/user_story_v1.yaml`
- `src/specfact_cli/templates/frameworks/scrum/user_story_v1.yaml`
- `src/specfact_cli/templates/personas/product-owner/user_story_v1.yaml`
- `src/specfact_cli/utils/ide_setup.py`
  - Hard-codes backlog prompt ids in `SPECFACT_COMMANDS`, so `init ide` currently exports backlog prompts from core resources.

### Module-side prompt/template ownership that already exists

- `/home/dom/git/nold-ai/specfact-cli-modules/packages/specfact-backlog/src/specfact_backlog/templates/registry.py`
- `/home/dom/git/nold-ai/specfact-cli-modules/packages/specfact-backlog/src/specfact_backlog/backlog/template_detector.py`
- `/home/dom/git/nold-ai/specfact-cli-modules/packages/specfact-backlog/src/specfact_backlog/backlog/mappers/template_config.py`

## Runtime Helpers

### Shared backlog contracts/infrastructure retained in core after cleanup

- `src/specfact_cli/backlog/adapters/base.py`
  - Minimal backlog adapter contract used by provider integrations and bundles.
- `src/specfact_cli/backlog/converter.py`
  - Provider-normalization helpers used by core GitHub/ADO adapters.
- `src/specfact_cli/backlog/filters.py`
  - Shared filter model used by provider adapters and bundle command adapters.
- `src/specfact_cli/backlog/mappers/*`
  - Shared provider field mappers used by core GitHub/ADO adapters.
- `src/specfact_cli/adapters/*`
  - Provider adapter infrastructure remains core framework code.
- `src/specfact_cli/models/backlog_item.py`
  - Canonical data model used across providers and bundles.

### Backlog-only helpers removed from core

- `src/specfact_cli/backlog/ai_refiner.py`
- `src/specfact_cli/backlog/template_detector.py`
- `src/specfact_cli/backlog/format_detector.py`
- `src/specfact_cli/backlog/formats/*`
- `src/specfact_cli/backlog/adapters/local_yaml_adapter.py`

## Duplicate Registration Tolerance

- `src/specfact_cli/registry/module_packages.py`
  - `_is_expected_duplicate_extension(...)` currently suppresses duplicate backlog overlaps for `nold-ai/specfact-backlog`.
  - This is tolerated only because command ownership is split today and must be removed after migration.

## Test Ownership

### Core-side tests removed or reduced because they belonged to module-owned backlog behavior

- `modules/backlog-core/tests/unit/*`
- `tests/unit/commands/test_backlog_commands.py`
- `tests/unit/commands/test_backlog_ceremony_group.py`
- backlog refinement/filtering E2E and integration suites under `tests/e2e/backlog/` and `tests/integration/backlog/`
- backlog helper unit suites under `tests/unit/backlog/` for ai-refinement/template/format/local-yaml behavior

### Core-side tests retained

- `tests/unit/test_backlog_module_ownership_cleanup.py`
- `tests/integration/test_command_package_runtime_validation.py`
- `tests/unit/utils/test_ide_setup.py`

### Module tests that should own backlog feature behavior after migration

- `/home/dom/git/nold-ai/specfact-cli-modules/tests/unit/specfact_backlog/test_map_fields_command.py`
- `/home/dom/git/nold-ai/specfact-cli-modules/tests/unit/specfact_backlog/test_auth_commands.py`
- `/home/dom/git/nold-ai/specfact-cli-modules/tests/unit/specfact_backlog/test_refine_adapter_contract.py`
- `/home/dom/git/nold-ai/specfact-cli-modules/tests/integration/specfact_backlog/test_command_apps.py`
- `/home/dom/git/nold-ai/specfact-cli-modules/tests/e2e/specfact_backlog/test_help_smoke.py`

## Docs Impact

- `docs/getting-started/tutorial-backlog-quickstart-demo.md`
- `docs/getting-started/tutorial-backlog-refine-ai-ide.md`
- `docs/guides/backlog-delta-commands.md`
- `docs/guides/backlog-dependency-analysis.md`
- `docs/guides/backlog-refinement.md`
- `docs/guides/policy-engine-commands.md`

These docs currently describe backlog behavior without a strict core-vs-module ownership boundary and will need follow-up alignment once command ownership is cut over.
