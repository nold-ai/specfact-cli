# api-error-diagnostics Specification

## Purpose
TBD - created by archiving change improve-ado-backlog-refine-error-logging. Update Purpose after archive.
## Requirements
### Requirement: ADO PATCH failure debug logging

When an ADO PATCH request fails (HTTP 4xx/5xx), the system SHALL log structured diagnostic data in debug mode so the failing field and server message are identifiable.

#### Scenario: Debug log contains response and patch paths on PATCH failure

- **GIVEN** debug mode is enabled (`--debug`)
- **AND** an ADO PATCH request fails (e.g. 400 Bad Request)
- **WHEN** the failure is handled (before re-raise or user message)
- **THEN** `debug_log_operation` is called with operation (e.g. `ado_patch`), target (URL redacted), status (e.g. `failed`), error (exception or message string)
- **AND** `extra` includes a safe snippet of the response body (e.g. parsed `message` or truncated `response.text`, redacted, max ~1–2 KB)
- **AND** `extra` includes the list of JSON Patch operation paths attempted (e.g. `["/fields/System.AcceptanceCriteria", "/fields/System.Description"]`)
- **AND** sensitive values in response body and extra are redacted (e.g. via `LoggerSetup.redact_secrets`)

#### Scenario: No sensitive data in debug log

- **GIVEN** debug mode is enabled and ADO returns an error body containing tokens or secrets
- **WHEN** the error is logged to the debug log
- **THEN** the logged snippet is redacted so that tokens, keys, and known secret patterns are not written in plain text

### Requirement: User-facing error message on ADO PATCH failure

When an ADO PATCH request fails, the user SHALL see the server error message and an actionable hint without requiring `--debug`.

#### Scenario: Console shows ADO message and mapping hint on 400

- **GIVEN** an ADO PATCH request fails with HTTP 400 and a body containing a message (e.g. "TF51535: Cannot find field System.AcceptanceCriteria")
- **WHEN** the error is surfaced to the user (console or exception)
- **THEN** the visible message includes the ADO error message (e.g. "Cannot find field System.AcceptanceCriteria")
- **AND** the visible message includes a short hint that custom field mapping may be required (e.g. "Check custom field mapping; see ado_custom.yaml or documentation.")
- **AND** the message is concise and actionable (no raw stack trace unless debug)

#### Scenario: Re-raised exception carries ADO context

- **GIVEN** the implementation re-raises an exception after handling ADO PATCH failure
- **WHEN** the exception is raised
- **THEN** the exception message (or attached attribute) includes the ADO error message and mapping hint so that upstream handlers or tests can display or assert on it

#### Scenario: User message highlights failing field when present

- **GIVEN** the ADO response message contains a field reference (e.g. “Cannot find field System.AcceptanceCriteria”)
- **WHEN** the error is surfaced to the user
- **THEN** the visible message quotes or emphasizes the field reference (e.g. “Field ‘System.AcceptanceCriteria’ not found”) so the failing field is obvious at a glance
- **AND** the hint about custom mapping follows

### Requirement: Consistent behavior across ADO PATCH call sites

The same error capture, debug logging, and user-facing message behavior SHALL apply to all ADO PATCH operations (backlog refine body update, work item status update, add comment, create work item).

#### Scenario: Backlog refine body PATCH failure

- **GIVEN** `_update_work_item_body` or the backlog-refine PATCH path fails with 400/422
- **WHEN** the failure is handled
- **THEN** debug log (if enabled) contains response snippet and patch paths
- **AND** user sees ADO message and mapping hint

#### Scenario: Status update or comment PATCH failure

- **GIVEN** status update or add-comment PATCH fails with 4xx/5xx
- **WHEN** the failure is handled
- **THEN** the same debug logging and user-facing message pattern is applied (response snippet, patch paths in debug; ADO message and hint to user)

### Requirement: Safe response body handling

The system SHALL safely parse and truncate response bodies to avoid large logs and parsing errors.

#### Scenario: Non-JSON or oversized response body

- **GIVEN** the ADO response body is non-JSON or very large
- **WHEN** building the error summary for debug log or user message
- **THEN** the implementation uses `response.text[:N]` (e.g. 500–2000 chars) as fallback for message extraction
- **AND** JSON parsing failures do not suppress logging; a safe string is used instead

