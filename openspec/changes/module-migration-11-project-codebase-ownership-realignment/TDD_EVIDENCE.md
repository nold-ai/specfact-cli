# TDD Evidence: module-migration-11-project-codebase-ownership-realignment

## Pre-Implementation Failing Evidence

### Core Ownership And Audit Coverage

Command:

```bash
hatch run pytest tests/unit/groups/test_codebase_group.py tests/unit/groups/test_project_group.py tests/unit/validation/test_command_audit.py -q
```

Result: failed

Key failures:

- `tests/unit/groups/test_codebase_group.py`
  - expected `import` under the `code` group
  - actual subcommands: `['analyze', 'drift', 'validate', 'repro']`
- `tests/unit/groups/test_project_group.py`
  - expected `import` to be absent from the `project` group
  - actual subcommands: `['project', 'plan', 'import', 'sync', 'migrate']`
- `tests/unit/validation/test_command_audit.py`
  - expected audit coverage for `code import`
  - actual command audit paths did not include `code import`

### Modules Codebase Command App Coverage

Command:

```bash
hatch run pytest tests/integration/specfact_codebase/test_command_apps.py -q
```

Result: failed

Key failures:

- `specfact_codebase.import_cmd.commands` does not exist yet
- existing codebase command modules also fail to import in the worktree test env because `specfact-cli` dev dependencies have not been synced into the local Hatch environment yet (`ModuleNotFoundError: specfact_cli`, `ModuleNotFoundError: beartype`)

Interpretation:

- the canonical `specfact code import` surface is not implemented yet
- the project-owned import surface is still present
- the modules worktree needs `dev-deps` synchronized before post-implementation verification can be trusted

## Post-Implementation Passing Evidence

### Core Ownership And Command Audit Coverage

Command:

```bash
SPECFACT_MODULES_REPO=/home/dom/git/nold-ai/specfact-cli-modules-worktrees/bugfix/module-migration-11-project-codebase-ownership-realignment hatch run pytest tests/unit/groups/test_codebase_group.py tests/unit/groups/test_project_group.py tests/unit/validation/test_command_audit.py -q
```

Result: passed

Verified:

- `code` group now exposes `import`
- category-level `project` group no longer mounts brownfield import as a top-level group member
- command audit inventory now includes `code import`

### Modules Codebase Command App Coverage

Command:

```bash
PYTHONPATH=/home/dom/git/nold-ai/specfact-cli-worktrees/bugfix/module-migration-11-project-codebase-ownership-realignment/src:/home/dom/.local/lib/python3.11/site-packages:/usr/lib/python3/dist-packages hatch run pytest tests/integration/specfact_codebase/test_command_apps.py tests/e2e/specfact_codebase/test_help_smoke.py -q
```

Result: passed

Verified:

- `specfact_codebase.import_cmd.commands` exists and exports a Typer app
- `specfact_codebase.code.commands` mounts the new import surface
- `code import --help` renders cleanly at the module-app level

### Notes

- The implementation intentionally uses temporary delegation from `specfact_codebase.import_cmd` into the existing brownfield import logic in `specfact_project.import_cmd.commands` while ownership is realigned.
- A broader temp-home marketplace install/runtime audit was started in the core worktree, but it did not complete in a timely way during this turn, so the passing evidence above is the recorded verification baseline.
