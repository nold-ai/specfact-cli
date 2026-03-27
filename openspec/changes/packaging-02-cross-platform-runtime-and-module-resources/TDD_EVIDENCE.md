# TDD Evidence

## Pre-Implementation Failing Run

- Timestamp: 2026-03-24T21:32:21+01:00
- Command:

```bash
HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/unit/utils/test_terminal.py tests/unit/utils/test_ide_setup.py tests/unit/modules/init/test_resource_resolution.py tests/unit/specfact_cli/registry/test_module_packages.py -q
```

- Result: failed during test collection.
- Failure summary:
  - `tests/unit/utils/test_terminal.py` could not import `ensure_output_stream_safety` from `specfact_cli.utils.terminal`.
  - `tests/unit/utils/test_ide_setup.py` could not import `discover_prompt_template_files` from `specfact_cli.utils.ide_setup`.

## Post-Implementation Passing Run

- Timestamp: 2026-03-24T22:07:38+01:00
- Command:

```bash
HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/unit/utils/test_terminal.py tests/unit/utils/test_ide_setup.py tests/unit/modules/init/test_resource_resolution.py tests/unit/specfact_cli/registry/test_module_packages.py -q
```

- Result: passed.
- Summary: 83 tests passed, covering terminal encoding fallback, runtime compatibility diagnostics, repo-scoped module discovery, duplicate prompt-id handling, and backlog field mapping resource resolution.

## Final Review Gate

- Timestamp: 2026-03-24T22:07:18+01:00
- Command:

```bash
HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run specfact code review run src/specfact_cli/utils/terminal.py src/specfact_cli/runtime.py src/specfact_cli/utils/ide_setup.py src/specfact_cli/modules/init/src/commands.py src/specfact_cli/registry/module_packages.py --exclude-tests
```

- Result: passed.
- Summary: `specfact code review run` completed with no findings on the shipped production files.

## Task 3.5 — Remove bundle workflow prompts from core wheel (2026-03-28)

- Change: drop `resources/prompts` from `[tool.hatch.build.targets.wheel.force-include]`, delete repo-root `resources/prompts/`, align startup drift checks and init template resolution with `discover_prompt_template_files`, bump **0.43.1**.

### Pre-implementation failing run (Task 3.5)

- Timestamp: 2026-03-28T00:18:00+01:00 (local)
- Command:

```bash
cd /home/dom/git/nold-ai/specfact-cli-worktrees/chore/packaging-02-finish-core-prompt-cleanup
hatch run smart-test-full
```

- Result: failed.
- Failure summary: exit code 1 — tests and/or checks failed after removing `resources/prompts` from the wheel and repo without updating startup checks, init template resolution, and tests (expected until implementation was completed).

### Post-change verification (Task 3.5)

```bash
cd /home/dom/git/nold-ai/specfact-cli-worktrees/chore/packaging-02-finish-core-prompt-cleanup
hatch env create
hatch run format && hatch run type-check && hatch run contract-test
hatch run smart-test-full
```

- Timestamp: 2026-03-28T00:22:00+01:00 (local)
- Command: `hatch run smart-test-full` (from worktree `chore/packaging-02-finish-core-prompt-cleanup`)
- Result: passed (exit 0).
