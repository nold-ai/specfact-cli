# Tasks: Add debug logs under ~/.specfact/logs

## 1. Create git branch

- [x] 1.1.1 Ensure we're on dev and up to date: `git checkout dev && git pull origin dev`
- [x] 1.1.2 Create branch with Development link to issue: `gh issue develop 158 --repo nold-ai/specfact-cli --name feature/add-debug-logs-specfact-home --checkout` (or `git checkout -b feature/add-debug-logs-specfact-home` if gh not available)
- [x] 1.1.3 Verify branch: `git branch --show-current`

## 2. User-level debug log directory

- [x] 2.1.1 Add `get_specfact_home_logs_dir()` in `src/specfact_cli/common/logger_setup.py` returning `os.path.expanduser("~/.specfact/logs")`, creating directory with `os.makedirs(..., mode=0o755, exist_ok=True)` on first use.
- [x] 2.1.2 Add `@icontract` and `@beartype` decorators; ensure result is non-empty string.
- [x] 2.1.3 Add unit test for `get_specfact_home_logs_dir()` (temp HOME, verify path and directory creation).
- [x] 2.1.4 Run `hatch run format` and `hatch run type-check`

## 3. Debug file routing in runtime

- [x] 3.1.1 In `src/specfact_cli/runtime.py`, when `debug_print()` is called and `_debug_mode` is True, also write the same content to a debug log file under `~/.specfact/logs` (e.g. rotating `specfact-debug.log`). Initialize file handler lazily on first debug_print when debug is on.
- [x] 3.1.2 Add `debug_log_operation(operation: str, target: str, status: str, error: str | None = None, extra: dict | None = None)` that no-ops when `not is_debug_mode()` and when debug is on writes a structured line to the debug log file (and optionally calls `debug_print()` for key info). Redact `target`/`extra` via `LoggerSetup.redact_secrets` if needed.
- [x] 3.1.3 In `src/specfact_cli/cli.py` app callback, after `set_debug_mode(debug)`, if `debug` is True ensure debug log file is initialized (e.g. call a one-time init that creates dir and sets up file handler for runtime).
- [x] 3.1.4 Add unit tests for `debug_print()` writing to file when debug on (temp dir); for `debug_log_operation()` no-op when debug off and write when on.
- [x] 3.1.5 Run `hatch run format` and `hatch run type-check`

## 4. Operation metadata in adapters and commands

- [x] 4.1.1 In `src/specfact_cli/adapters/ado.py`, when `is_debug_mode()` is True, log operation metadata for WIQL, Work Items fetch, and PATCH (URL redacted, method, status code; on failure error snippet).
- [x] 4.1.2 In `src/specfact_cli/adapters/github.py`, when debug is on, log API request/response metadata (URL redacted, method, status; on failure redacted snippet).
- [x] 4.1.3 In `src/specfact_cli/commands/backlog_commands.py`, when debug is on, log file read/write for export/import (path, success/failure, error).
- [x] 4.1.4 In `src/specfact_cli/commands/init.py`, when debug is on, ensure template resolution steps are also written to debug log (in addition to existing `debug_print()`).
- [x] 4.1.5 Run `hatch run format` and `hatch run type-check`

## 5. Tests and quality

- [x] 5.1.1 Add or extend tests for debug log file creation, routing, and `debug_log_operation()` (unit with temp dir; mock `is_debug_mode()`).
- [x] 5.1.2 Run `hatch run contract-test` (or `hatch run smart-test`)
- [x] 5.1.3 Run `hatch run lint`
- [x] 5.1.4 Run `openspec validate add-debug-logs-specfact-home --strict`

## 6. Documentation and PR

- [x] 6.1.1 Update CLI help for `--debug` to mention log location (`~/.specfact/logs`) and purpose.
- [x] 6.1.2 Update versions and increase patch version. Sync versions across `pyproject.toml`, `setup.py`, `__init__.py`and `src/__init__.py`.
- [x] 6.1.3 Update CHANGELOG.md with new behavior and use the new patch version from 6.1.2.
- [ ] 6.1.4 Create Pull Request from feature/add-debug-logs-specfact-home to dev
