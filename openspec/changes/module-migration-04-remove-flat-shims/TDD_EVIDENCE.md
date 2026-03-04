# TDD Evidence: module-migration-04-remove-flat-shims

## Pre-Implementation Failing Run

- Timestamp: 2026-03-04T20:23:10+01:00
- Command:

```bash
PYTHONPATH=/home/dom/git/nold-ai/specfact-cli-worktrees/feature/module-migration-04-remove-flat-shims/src \
/home/dom/git/nold-ai/specfact-cli/.venv/bin/python -m pytest \
tests/unit/specfact_cli/registry/test_module_packages.py \
-k grouped_registration_does_not_register_flat_shim_commands -v
```

- Result: **FAILED** (expected red phase)
- Failure summary: `validate` was still registered at root (`{'code', 'validate'}`), proving flat shim machinery was active.

## Post-Implementation Passing Run

- Timestamp: 2026-03-04T20:24:03+01:00
- Commands:

```bash
PYTHONPATH=/home/dom/git/nold-ai/specfact-cli-worktrees/feature/module-migration-04-remove-flat-shims/src \
/home/dom/git/nold-ai/specfact-cli/.venv/bin/python -m pytest \
tests/unit/specfact_cli/registry/test_module_packages.py \
-k grouped_registration_does_not_register_flat_shim_commands -v

PYTHONPATH=/home/dom/git/nold-ai/specfact-cli-worktrees/feature/module-migration-04-remove-flat-shims/src \
/home/dom/git/nold-ai/specfact-cli/.venv/bin/python -m pytest \
tests/unit/registry/test_category_groups.py \
-k "flat_validate_is_not_found_in_copilot_mode or flat_validate_is_not_found_in_cicd_mode" -v

PYTHONPATH=/home/dom/git/nold-ai/specfact-cli-worktrees/feature/module-migration-04-remove-flat-shims/src \
/home/dom/git/nold-ai/specfact-cli/.venv/bin/python -m pytest \
tests/integration/test_category_group_routing.py \
-k validate_flat_command_is_not_available -v
```

- Result: **PASSED**
- Passing summary: flat `validate` is no longer registered as a root command; category-only behavior is enforced for this shim-removal scope.

## Scope Note

- This change intentionally runs shim-removal-focused tests only.
- Broader suite migration/cleanup debt remains out of scope for this change and is deferred per migration planning.
