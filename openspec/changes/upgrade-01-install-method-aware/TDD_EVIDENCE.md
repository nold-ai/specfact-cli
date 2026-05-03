## Failing-before

- **Timestamp (UTC):** 2026-04-29 20:52:57
- **Command:** `pytest -q tests/unit/commands/test_update.py`
- **Observed failure:** `SyntaxError: unterminated string literal (detected at line 142)` in `src/specfact_cli/modules/upgrade/src/commands.py` during test collection.
- **Failure lines:**
  - `ERROR collecting tests/unit/commands/test_update.py`
  - `E File "/workspace/specfact-cli/src/specfact_cli/modules/upgrade/src/commands.py", line 142`
  - `E SyntaxError: unterminated string literal (detected at line 142)`

## Passing-after

- **Timestamp (UTC):** 2026-04-29 20:56:00
- **Command:** `pytest -q tests/unit/commands/test_update.py`
- **Result:** all tests passed (12/12).
- **Follow-up verification:** `openspec validate upgrade-01-install-method-aware --strict`

## CI regression follow-up

- **Timestamp (UTC):** 2026-05-03T20:05:33Z
- **Failing-before evidence:** GitHub Actions run `25137859729` for PR #539 failed both `Tests (Python 3.12)` and `Compatibility (Python 3.11)`.
- **Observed failure:** `tests/integration/test_core_slimming.py::test_flat_shim_plan_exits_with_not_found_or_install_instructions` exited with `SystemExit(2)` and empty output for a stale flat `plan` shim.
- **Local failing command before production fix:** `hatch run pytest tests/integration/test_core_slimming.py::test_stale_flat_shim_plan_exits_with_install_instructions -q`
- **Passing command after production fix:** `hatch run pytest tests/integration/test_core_slimming.py -q`
- **Result:** all touched integration tests passed (9/9).
- **Code review evidence (2026-05-03T20:20:21Z):** `SPECFACT_MODULES_ROOTS=/home/dom/git/nold-ai/specfact-cli-modules/packages hatch run specfact code review run --json --out .specfact/code-review.changed.json --scope changed` completed with 0 blocking findings and 0 fixable findings, but exited non-zero for 133 existing non-blocking basedpyright unknown-type warnings across touched `src/specfact_cli/cli.py`. `--level error` passed with exit code 0. Exception accepted for this CI fix because the normal `hatch run type-check` gate passed and the warning set is file-wide typed-dependency noise unrelated to the stale-shim behavior change.
