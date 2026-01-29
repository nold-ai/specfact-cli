# Design: Improve ADO backlog refine error logging and user-facing error UX

## Bridge adapter integration

- **Scope**: ADO adapter (`src/specfact_cli/adapters/ado.py`) only for this change. The pattern (capture response + operations, log in debug, surface message + hint) can be reused for GitHub or other adapters in a follow-up.
- **Existing hooks**: `debug_log_operation(operation, target, status, error=..., extra=...)` already supports `extra`; we will pass `response_body` (truncated/redacted) and `patch_paths` (list of strings). No change to `runtime.py` contract unless we need a shared truncation helper.
- **Redaction**: Use existing `LoggerSetup.redact_secrets` for any string or dict passed into `extra` so tokens and URLs are redacted before writing to the debug log file.

## Error handling strategy

1. **Capture**: On `requests.HTTPError` (or any PATCH failure), obtain `e.response`; parse `e.response.json()` for `message`; fallback to `e.response.text[:500]`. Extract patch paths from the `operations` list (the document we sent): `[op.get("path") for op in operations]`.
2. **Debug log**: If `is_debug_mode()`, call `debug_log_operation("ado_patch", url_redacted, "failed", error=message_or_str(e), extra={"response_body": snippet, "patch_paths": paths})`. Truncate snippet to ~1–2 KB; redact via `LoggerSetup.redact_secrets(snippet)` or redact the whole `extra` dict.
3. **User message**: Before re-raise, build a user-facing string: `f"{ado_message} Check custom field mapping; see ado_custom.yaml or documentation."` (or similar). Either set this as the exception message (e.g. wrap in a custom exception or replace `e.args`) or ensure `console.print(...)` is called with this message so the user always sees it.
4. **Re-raise**: Re-raise the original exception (or a wrapper that preserves cause) so callers and tests still get an exception; the console message is already printed so the user has context.

## Sequence (backlog refine PATCH failure)

```
User          CLI                ado.py                    ADO API
  |             |                    |                         |
  |  refine     |                    |                         |
  |  --write    |  PATCH body        |  PATCH /workitems/:id   |
  | ----------> | -----------------> | ----------------------> |
  |             |                    |         400             |
  |             |                    | <----------------------|
  |             |                    |  parse response.message |
  |             |                    |  extract patch_paths    |
  |             |                    |  if debug: log_operation|
  |             |                    |  console.print(msg+hint)|
  |             |                    |  raise                  |
  |             |  <----------------- |                        |
  |  [red] msg  |  print already     |                         |
  |  + hint     |  done in ado.py     |                         |
  | <----------- |                    |                         |
```

## Contract enforcement

- No new public API surface; only internal helper (e.g. `_log_ado_patch_failure`) and extended behavior of existing PATCH paths. Existing `@icontract` and `@beartype` on public methods remain; the helper can be private and optionally typed.
- Tests: unit tests for the helper (given mock response and operations, assert debug_log_operation called with correct extra; assert user message contains ADO text and hint). Integration test: simulate 400 with JSON body, run with `--debug`, assert debug log file contains patch paths and response snippet.

## Risks and mitigations

- **Large response body**: Truncate to 1–2 KB and redact; avoid logging huge HTML or JSON.
- **Non-JSON response**: Use `response.text[:N]` and do not fail; log the truncated text.
- **Regression on success path**: No change to success path; only failure branches are extended.

## Production-grade UX (implementation guidance)

To make error UX and debug usefulness “really good” for all customer sizes and complex infrastructures:

1. **Actionable hint with doc link**: Include a concrete doc link in the user message when available (e.g. ADO custom mapping docs) so users can resolve mapping issues without searching.
2. **Optional --debug pointer**: Append to the hint: “Run with --debug and check ~/.specfact/logs for full response and patch paths.” so users know how to get more detail.
3. **Log every failed attempt**: In paths with retries (e.g. backlog-refine PATCH), call the logging helper before each retry and on final failure so the debug log shows the sequence of attempts and the final response/paths.
4. **Highlight field name**: When the ADO message contains a field reference (e.g. “System.AcceptanceCriteria”), quote or emphasize it in the user message (e.g. “Field ‘System.AcceptanceCriteria’ not found. Check custom field mapping…”) so the failing field is obvious at a glance.
