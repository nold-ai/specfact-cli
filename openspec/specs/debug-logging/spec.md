# debug-logging Specification

## Purpose

TBD - created by archiving change add-debug-logs-specfact-home. Update Purpose after archive.

## Requirements

### Requirement: User-level debug log directory

The system SHALL provide a user-level directory for debug logs when debug mode is enabled.

#### Scenario: Resolve ~/.specfact/logs

- **GIVEN** debug mode may be enabled
- **WHEN** `get_specfact_home_logs_dir()` is called
- **THEN** returns path equivalent to `os.path.expanduser("~/.specfact/logs")`
- **AND** creates the directory with `os.makedirs(..., mode=0o755, exist_ok=True)` on first use

#### Scenario: No directory when debug is off

- **GIVEN** debug mode is disabled
- **WHEN** no debug log has been written in this run
- **THEN** `~/.specfact/logs` is not required to exist
- **AND** `get_specfact_home_logs_dir()` may still return the path for callers that need it

### Requirement: Debug output routing

The system SHALL route debug output to both console and a debug log file when debug mode is enabled.

#### Scenario: debug_print writes to console and file when debug on

- **GIVEN** debug mode is enabled and debug log file is initialized
- **WHEN** `debug_print(...)` is called
- **THEN** output is written to the configured Rich console (current behavior)
- **AND** the same content is appended to the debug log file under `~/.specfact/logs`

#### Scenario: debug_print console-only when debug off

- **GIVEN** debug mode is disabled
- **WHEN** `debug_print(...)` is called
- **THEN** no output is produced (current behavior)
- **AND** no debug log file is written

### Requirement: Structured operation metadata

The system SHALL support logging structured operation metadata when debug mode is enabled.

#### Scenario: debug_log_operation no-op when debug off

- **GIVEN** debug mode is disabled
- **WHEN** `debug_log_operation(operation=..., target=..., status=..., error=...)` is called
- **THEN** no log file write occurs
- **AND** no console output is produced

#### Scenario: debug_log_operation writes metadata when debug on

- **GIVEN** debug mode is enabled and debug log file is initialized
- **WHEN** `debug_log_operation(operation="api_request", target=url_redacted, status=200, error=None)` is called
- **THEN** a structured log line (or block) is written to the debug log file
- **AND** the line includes operation, target, status, and optionally error and extra fields
- **AND** sensitive values in target or extra are redacted (e.g. via LoggerSetup.redact_secrets)

#### Scenario: Adapters log API metadata when debug on

- **GIVEN** debug mode is enabled
- **WHEN** an adapter performs an API request (e.g. ADO WIQL, Work Items PATCH, GitHub REST)
- **THEN** the adapter logs operation metadata (operation type, URL redacted, method, status code)
- **AND** on failure, logs error snippet or response body (redacted)
- **AND** does not log full request/response bodies that may contain secrets

### Requirement: Debug log standard (consistent pattern for anomaly analysis and bug reports)

The system SHALL apply a consistent debug log pattern for every significant operation when debug mode is enabled, so that logs support anomaly analysis, unexpected error/failure diagnosis, reporting, and bug reports (production-tool quality).

#### Scenario: Every significant operation has started, progress, and outcome

- **GIVEN** debug mode is enabled
- **WHEN** a significant operation is performed (auth flow, file I/O, API call, template resolution, or any operation that can fail or affect behavior)
- **THEN** the implementation logs at least: **started/prepared** (once at begin), **attempt** (for each distinct step if multi-step), and **outcome** (exactly once: success with reason/method/cache or failed with error and reason)
- **AND** no operation is represented by only a single INFO-style line without outcome and reason
- **AND** structured lines include operation, target (redacted), status, and when applicable error, extra (payload/response/reason sanitized), caller

#### Scenario: Reference implementation

- **GIVEN** the auth azure-devops flow
- **WHEN** debug mode is enabled and the user runs the OAuth flow
- **THEN** the debug log contains: started → cache_prepared → attempt (interactive_browser) → success or fallback (with reason) → attempt (device_code) → success or failed (with error/reason) → success (token_stored with method/cache)
- **AND** a reader can determine from the log alone whether the flow succeeded or failed and why

### Requirement: Debug log context (timestamp, caller, file/API details)

The system SHALL include context in every debug log line when debug mode is enabled.

#### Scenario: Timestamp on every line

- **GIVEN** debug mode is enabled and debug log file is initialized
- **WHEN** any line is written to the debug log file (via debug_print or debug_log_operation)
- **THEN** the line is prefixed with a timestamp (e.g. `%(asctime)s | %(message)s` with datefmt `%Y-%m-%d %H:%M:%S`)

#### Scenario: Caller (module/method) in structured lines

- **GIVEN** debug mode is enabled
- **WHEN** `debug_log_operation(..., caller=...)` is called with a caller string (e.g. `module:function`)
- **THEN** the structured log line includes the caller in the payload
- **AND** call sites may infer caller via inspect or pass explicitly

#### Scenario: File operations log prepared / finished / failed

- **GIVEN** debug mode is enabled
- **WHEN** a command or adapter performs file IO (read/write)
- **THEN** it logs operation metadata with status prepared/started before the operation
- **AND** logs again with status finished or failed and error/reason when applicable
- **AND** target is the path (redacted if sensitive); extra may include size, mime, etc.

#### Scenario: API operations log operation, URL, payload (sanitized), response, status, error, reason

- **GIVEN** debug mode is enabled
- **WHEN** an adapter performs an API request
- **THEN** it logs operation metadata with operation type, target (URL redacted), status (HTTP or success/failure)
- **AND** extra includes payload (sanitized via LoggerSetup.redact_secrets), response (sanitized), and reason when applicable
- **AND** on failure, error and reason are included

### Requirement: Backward compatibility

The system SHALL preserve existing behavior when debug mode is disabled.

#### Scenario: get_runtime_logs_dir unchanged

- **GIVEN** any mode
- **WHEN** `get_runtime_logs_dir()` is called
- **THEN** returns the same path as before (repo-relative logs or /app/logs in Docker)
- **AND** behavior of LoggerSetup and existing loggers is unchanged

### Requirement: Non-Debug Runtime Diagnostics Stay User-Facing

The system SHALL keep raw internal runtime diagnostics out of normal command output and only show explicitly formatted user-facing messages when the user must take action.

#### Scenario: Expected backlog command overlap stays quiet in normal output

- **GIVEN** the built-in `backlog-core` module and the published `nold-ai/specfact-backlog` bundle both contribute to the public `backlog` command surface by design
- **WHEN** a user runs a normal `specfact backlog ...` command without `--debug`
- **THEN** expected overlap handling does not emit duplicate-subcommand warnings
- **AND** only unexpected or actionable ownership conflicts remain visible.

#### Scenario: Routine bundled dependency satisfaction stays non-warning

- **GIVEN** `--debug` is not enabled
- **AND** a bundled module upgrade sees that a declared bundled dependency is already installed at the required version
- **WHEN** the upgrade completes without conflict, trust, or integrity problems
- **THEN** normal output does not emit a warning for that already-satisfied dependency
- **AND** any optional trace for the satisfied dependency is routed to debug or informational channels instead.

#### Scenario: Bridge logger lines stay out of normal console output

- **GIVEN** `--debug` is not enabled
- **WHEN** internal bridge or registry code records non-actionable informational or warning diagnostics through the shared logger
- **THEN** those raw logger lines do not appear in the user's console output
- **AND** only explicitly formatted user-facing warnings remain visible when the user must take action.

### Requirement: Bridge logger used in all production source paths

Every production code path in `src/specfact_cli/` SHALL use `get_bridge_logger()` from `specfact_cli.common` for all diagnostic output, replacing any remaining `print()` builtin calls.

#### Scenario: Adapter module writes diagnostic output via bridge logger

- **WHEN** an adapter module (e.g., `adapters/ado.py`, `adapters/github.py`) performs a network call or state change
- **THEN** diagnostic messages are written via `logger = get_bridge_logger(__name__)` and `logger.debug(...)` / `logger.info(...)`
- **AND** no `print()` call appears in the adapter module

#### Scenario: Sync module writes diagnostic output via bridge logger

- **WHEN** `sync/bridge_sync.py` or `sync/spec_to_code.py` processes a file
- **THEN** all progress and error messages are routed through `get_bridge_logger(__name__)`
- **AND** no `print()` call appears in the sync module

### Requirement: Script-layer logging uses stdlib or Rich, not print()

Scripts in `scripts/` and `tools/` that run as standalone CLI programs SHALL use `logging.getLogger(__name__)` with a `StreamHandler` for progress output, or `rich.console.Console()` for formatted terminal output. The stdlib `print()` builtin SHALL NOT be used.

#### Scenario: Standalone script writes progress via logging

- **WHEN** a script in `scripts/` needs to write a status message to stdout
- **THEN** it calls `logging.getLogger(__name__).info(...)` or `console.print(...)` from a Rich Console instance
- **AND** semgrep `print-in-src` reports zero findings for that script
