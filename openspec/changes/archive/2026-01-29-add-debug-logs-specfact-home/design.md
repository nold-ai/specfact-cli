# Design: Add debug logs under ~/.specfact/logs

## Overview

When `--debug` is enabled globally, the CLI writes debug output to both the console (existing `debug_print()`) and a rotating log file under `~/.specfact/logs`. Every log line includes a **timestamp**. A helper `debug_log_operation()` writes structured metadata (operation, target, status, error, extra, optional caller) for file and API operations. **File operations** log prepared / finished / failed and status; **API operations** log operation, URL (redacted), payload (sanitized), response, status, error, reason (via extra). Logger-module helpers (`plain_text_for_debug_log`, `format_debug_log_message`) and runtime `_append_debug_log()` centralize formatting so call sites stay minimal.

## Debug log standard (mandatory pattern)

Debug logs are **critical for anomaly analysis, unexpected errors/failures, reporting, and bug reports**. The same standard applies everywhere we emit debug log entries—no single-line “INFO-style” lines; every significant operation must provide **full context** as in a production tool.

**Required pattern for every significant operation:**

1. **Started / prepared**  
   Log once when the operation begins: `status=started` or `status=prepared`, with `target` (path/URL) and optional `extra` (e.g. flow, method, cache).

2. **Progress / attempt** (if multi-step)  
   For each distinct step (e.g. “try interactive browser”, “try device code”, “read file”, “call API”): log `status=attempt` with `extra` (e.g. `method`, `reason`) so the log shows what was tried.

3. **Outcome**  
   Log exactly once when the operation ends:
   - **Success**: `status=success` (or HTTP status for API), with `extra` (e.g. `method`, `cache`, `reason`) so it is clear *why* and *how* it succeeded.
   - **Failure**: `status=failed` (or `status=error`), with `error=<message>` and `extra.reason` (or equivalent) so failures are diagnosable and reproducible.

**What to include (minimum):**

- **Every line**: timestamp (formatter), caller (module:function).
- **Structured lines**: `operation`, `target` (redacted), `status`, and when applicable: `error`, `extra` (payload/response/reason/cache/method—sanitized).

**Apply consistently:** Auth flows, file I/O, API calls, template resolution, and any other operation that can fail or affect behavior must follow this pattern. Reference implementation: `auth azure-devops` (started → cache_prepared → attempt interactive_browser → success/fallback → attempt device_code → success/failed → success token_stored).

## Architecture

- **Runtime**: `debug_print()` writes to console and, via `_append_debug_log()`, to a file handler backed by `~/.specfact/logs/specfact-debug.log`. The file handler uses a formatter with **timestamp** (e.g. `%(asctime)s | %(message)s`). `debug_log_operation(..., caller=...)` writes structured JSON lines; caller (module/method) is included when provided. File handler is initialized in the app callback after `set_debug_mode(True)`.
- **LoggerSetup**: `get_specfact_home_logs_dir()` returns `~/.specfact/logs` and ensures the directory exists (0o755). `plain_text_for_debug_log(text)` strips Rich markup; `format_debug_log_message(*args, **kwargs)` produces a single plain line for the debug log file. No change to `get_runtime_logs_dir()`.
- **Adapters / Commands**: When `runtime.is_debug_mode()` is True, call `debug_log_operation(operation, target, status, error=..., extra=..., caller=...)` around file IO and API calls. For **file ops**: log prepared (status=prepared/started), then finished or failed (status=finished/failed); include path in target. For **API ops**: include in extra (redacted): payload, response, reason; status is HTTP status or success/failure. Redact via `LoggerSetup.redact_secrets` before logging.

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

## Module coverage (consistent debug across commands)

All CLI command modules should support `--debug` with consistent context:

| Command module | Already has debug | Add / extend |
|----------------|-------------------|--------------|
| auth | yes (debug_print, debug_log_operation) | Ensure caller; API payload/response/reason in extra |
| init | yes (debug_print, template resolution) | debug_log_operation for template resolution status; caller |
| backlog_commands | yes (debug_log_operation for file IO) | debug_print for key steps; file prepared/finished/failed |
| analyze | no | debug_print at entry; debug_log_operation for file/API |
| contract_cmd | no | debug_print at entry; file ops with prepared/finished/failed |
| drift | no | debug_print at entry; file/API ops |
| enforce | no | debug_print at entry; file/API ops |
| generate | no | debug_print at entry; file ops |
| import_cmd | no | debug_print at entry; file ops (prepared/finished/failed) |
| migrate | no | debug_print at entry; file ops |
| plan | no | debug_print at entry; file/API ops |
| project_cmd | no | debug_print at entry; file ops |
| repro | no | debug_print at entry; file/API ops |
| sdd | no | debug_print at entry; file ops |
| spec | no | debug_print at entry; API ops (payload/response/reason) |
| sync | no | debug_print at entry; file/API ops |
| update | no | debug_print at entry; API ops |
| validate | no | debug_print at entry; file/API ops |

Adapters (ado, github): already log operation/target/status; extend extra with payload (sanitized), response, reason where applicable.

## Risks

- **Disk usage**: Use rotating file (e.g. RotatingFileHandler, 5 MB × 5) to cap size.
- **Secrets**: Always redact in `debug_log_operation()` and when logging response/request bodies; avoid logging full bodies by default.
