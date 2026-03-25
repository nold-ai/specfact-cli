# TDD evidence: init-ide-prompt-source-selection

## Pre-implementation (failing tests)

- Command: `hatch run pytest tests/unit/modules/init/test_init_ide_prompt_selection.py -v`
- Timestamp: 2026-03-25 (session; tests added before implementation in worktree `feature/init-ide-prompt-source-selection`)
- Note: New tests were introduced to lock catalog export, `--prompts` parsing, and CLI failure on invalid tokens; implementation followed in the same change.

## Post-implementation (passing)

- Command: `hatch run pytest tests/unit/modules/init/test_init_ide_prompt_selection.py tests/unit/utils/test_ide_setup.py tests/e2e/test_init_command.py -q`
- Status: green after `ide_setup` catalog + namespaced copy, `init ide` wiring, startup_checks rglob, and e2e path updates.

## Follow-up: flat export + core/module dedupe (2026-03-26)

- **Change:** Multi-source export uses a flat IDE folder; core omits template basenames covered by any module; legacy per-source subfolders are removed on export.
- **Tests:** `hatch test tests/unit/utils/test_ide_setup.py tests/unit/modules/init/test_init_ide_prompt_selection.py -v` — all passed.
- **Contract:** `hatch run contract-test` — PASS.
