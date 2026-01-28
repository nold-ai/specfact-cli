# Design: Add debug logs under ~/.specfact/logs

## Overview

When `--debug` is enabled globally, the CLI will write debug output to both the console (existing `debug_print()`) and a rotating log file under `~/.specfact/logs`. A helper `debug_log_operation()` will write structured metadata for file and API operations so failures can be diagnosed without cluttering normal output.

## Architecture

- **Runtime**: `runtime.debug_print()` continues to control console output; when debug is on, it also writes to a file handler backed by `~/.specfact/logs/specfact-debug.log` (or date-stamped file). The file handler is registered in the app callback after `set_debug_mode(True)`.
- **LoggerSetup**: New `get_specfact_home_logs_dir()` returns `os.path.expanduser("~/.specfact/logs")` and ensures the directory exists (0o755) on first use. No change to `get_runtime_logs_dir()`.
- **Adapters / Commands**: When `runtime.is_debug_mode()` is True, call `debug_log_operation(operation, target, status, error=..., extra=...)` around file IO and API calls; redact secrets via `LoggerSetup.redact_secrets` before logging.

## Contract enforcement

- `get_specfact_home_logs_dir()`: `@require` path is expandable; `@ensure` result is non-empty string and directory exists after first call when used for writing.
- `debug_print()`: existing contract; add side-effect of writing to file when debug on (idempotent per run).
- `debug_log_operation()`: `@require` operation and target are strings when provided; no-op when `not is_debug_mode()`.

## Fallback and offline

- If `~/.specfact` or `~/.specfact/logs` cannot be created (e.g. read-only HOME), fall back to console-only debug output and log a one-line warning via `debug_print()`.
- No network dependency for debug logging; all writes are local file IO.

## Sequence (debug on, first write)

1. User runs `specfact --debug <command>`.
2. App callback sets `set_debug_mode(True)`.
3. Callback ensures debug log file is initialized: `get_specfact_home_logs_dir()`, create dir if needed, open rotating file handler, register with runtime for `debug_print()` and `debug_log_operation()`.
4. During command execution, `debug_print()` and `debug_log_operation()` write to console and file.
5. On exit, close file handler (or let process exit flush).

## Risks

- **Disk usage**: Use rotating file (e.g. RotatingFileHandler, 5 MB × 5) to cap size.
- **Secrets**: Always redact in `debug_log_operation()` and when logging response/request bodies; avoid logging full bodies by default.
