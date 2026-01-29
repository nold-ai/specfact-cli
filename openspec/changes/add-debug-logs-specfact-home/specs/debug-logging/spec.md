# debug-logging (delta)

## ADDED Requirements

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
