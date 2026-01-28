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

### Requirement: Backward compatibility

The system SHALL preserve existing behavior when debug mode is disabled.

#### Scenario: get_runtime_logs_dir unchanged

- **GIVEN** any mode
- **WHEN** `get_runtime_logs_dir()` is called
- **THEN** returns the same path as before (repo-relative logs or /app/logs in Docker)
- **AND** behavior of LoggerSetup and existing loggers is unchanged
