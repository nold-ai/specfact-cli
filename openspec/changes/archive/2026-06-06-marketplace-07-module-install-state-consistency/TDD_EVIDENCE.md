# TDD Evidence

## 2026-04-28 - Failing regression run

Command:

```bash
hatch run pytest tests/unit/specfact_cli/registry/test_module_availability.py tests/unit/modules/module_registry/test_commands.py::test_install_command_existing_disabled_module_enables_state tests/unit/specfact_cli/test_module_not_found_error.py::test_module_not_found_error_reports_disabled_installed_module tests/unit/modules/init/test_first_run_selection.py::test_init_profile_enables_profile_modules_and_uses_repo_for_discovery tests/unit/specfact_cli/registry/test_init_module_state.py::test_refresh_preserves_unseen_module_state_when_requested -q
```

Result: failed during collection as expected before implementation.

Key failure:

```text
ModuleNotFoundError: No module named 'specfact_cli.registry.module_availability'
```

## 2026-04-28 - Passing regression and touched-scope verification

Focused regression command:

```bash
hatch run pytest tests/unit/specfact_cli/registry/test_module_availability.py tests/unit/modules/module_registry/test_commands.py::test_install_command_existing_disabled_module_enables_state tests/unit/specfact_cli/test_module_not_found_error.py tests/unit/modules/init/test_first_run_selection.py::test_init_profile_enables_profile_modules_and_uses_repo_for_discovery tests/unit/specfact_cli/registry/test_init_module_state.py::test_refresh_preserves_unseen_module_state_when_requested -q
```

Result: 11 passed, 2 warnings.

Touched-area regression command:

```bash
hatch run pytest tests/unit/specfact_cli/registry/test_module_availability.py tests/unit/modules/module_registry/test_commands.py tests/unit/specfact_cli/test_module_not_found_error.py tests/unit/modules/init/test_first_run_selection.py tests/unit/specfact_cli/registry/test_init_module_state.py tests/unit/registry/test_module_lifecycle.py tests/unit/specfact_cli/registry/test_command_registry.py -q
```

Result: 96 passed, 2 warnings.

Quality gates:

```bash
hatch run lint
hatch run specfact code review run --json --out .specfact/code-review.changed.json --scope changed
openspec validate marketplace-07-module-install-state-consistency --strict
```

Results: lint passed; changed-scope SpecFact code review passed with 0 blocking findings; strict OpenSpec validation passed.

## 2026-04-28 - Isolated CLI reality test

Command shape:

```bash
HOME=/tmp/specfact-reality-*/home \
SPECFACT_REGISTRY_DIR=/tmp/specfact-reality-*/registry \
HATCH_DATA_DIR=/home/dom/.local/share/hatch \
HATCH_CACHE_DIR=/home/dom/.cache/hatch \
/home/dom/.local/pipx/venvs/hatch/bin/hatch run specfact ...
```

Scenarios covered with local fixture modules:

- `specfact code` reports `nold-ai/specfact-codebase` as installed but disabled and suggests `specfact module enable nold-ai/specfact-codebase`.
- `specfact module install nold-ai/specfact-codebase` repairs disabled existing install state and preserves an unrelated disabled `modules.json` row.
- `specfact init --repo <tmp-repo> --profile solo-developer` enables `nold-ai/specfact-codebase` and `nold-ai/specfact-code-review` while preserving unrelated state.
- `specfact module upgrade nold-ai/specfact-backlog` takes the deterministic offline path and reports the marketplace registry as unavailable instead of corrupting state.
- `specfact module uninstall nold-ai/specfact-backlog --scope user` removes the user-scoped module directory.

Result: `REALITY_TEST_PASS`.

Reality test fixes added:

- Availability classification now prioritizes an explicit requested module id over other modules sharing the same top-level command group.
- Install repair now merges with existing module lifecycle state instead of replacing unrelated rows.
