# Change: Add debug logs under ~/.specfact/logs with rich operation metadata

## Why

When `--debug` is enabled globally, users and developers need consistent debug logs to diagnose IO, file handling, and API issues. Today debug output is only printed to the console via `debug_print()` and is not persisted; there is no user-level log directory and no structured operation metadata (status, return, error) for file or API operations. Storing debug logs under `~/.specfact/logs` and including rich operation metadata makes it possible to identify issues when something does not work as expected without cluttering normal CLI output.

## What Changes

- **NEW**: User-level debug log directory `~/.specfact/logs` (create on first use when debug is enabled; mode 0o755). Add `get_specfact_home_logs_dir()` in `logger_setup.py` returning this path.
- **EXTEND**: When `--debug` is set, route `debug_print()` output to both console (current) and a debug log file under `~/.specfact/logs` (e.g. rotating `specfact-debug.log`).
- **NEW**: Optional helper `debug_log_operation(operation, target, status, error=None, extra=None)` that no-ops when debug is off and when debug is on writes structured metadata to the debug log file and optionally calls `debug_print()`.
- **EXTEND**: In key places (file IO, API calls), when debug is on, log operation metadata: operation type, target (path/URL redacted), status/result, error snippet; use `LoggerSetup.redact_secrets` for any response/request bodies.
- **EXTEND**: Adapters (ADO, GitHub) and commands (backlog refine, init) log file/API operation metadata when debug is enabled.
- **NOTE**: `get_runtime_logs_dir()` remains unchanged for existing callers (agent_flow, etc.); `~/.specfact/logs` is used only for the dedicated debug session log.

## Capabilities

- **debug-logging**: ADDED requirement for user-level debug log directory, debug file routing, and structured operation metadata when --debug is enabled.

## Impact

- **Affected specs**: debug-logging (new capability).
- **Affected code**: `src/specfact_cli/runtime.py` (debug_print file routing, debug_log_operation); `src/specfact_cli/common/logger_setup.py` (get_specfact_home_logs_dir); `src/specfact_cli/cli.py` (debug file init); `src/specfact_cli/adapters/ado.py`, `src/specfact_cli/adapters/github.py` (operation metadata); `src/specfact_cli/commands/backlog_commands.py`, `src/specfact_cli/commands/init.py` (file/operation metadata).
- **Integration points**: runtime.set_debug_mode / is_debug_mode (existing); LoggerSetup.redact_secrets (existing).

## Source Tracking

- **GitHub Issue**: #158
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/158>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
