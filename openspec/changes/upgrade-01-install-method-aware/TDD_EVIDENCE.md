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
