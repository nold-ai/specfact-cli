# Change: Improve ADO backlog refine error logging and user-facing error UX

## Why

When running SpecFact backlog refinement writeback against Azure DevOps (`specfact backlog refine ado ... --import-from-tmp --write`), API failures (e.g. HTTP 400 due to custom ADO process templates missing fields like `System.AcceptanceCriteria`) produce a generic "400 Client Error: Bad Request" with no indication of which field or patch operation failed. Even with `--debug`, logs do not include the ADO response body or the JSON Patch paths, so root-cause diagnosis required local instrumentation. This blocks production use in enterprises with custom ADO templates and prevents users from self-serving (e.g. applying custom mapping) without maintainer help. Improving error diagnostics and user-facing messages makes the CLI production-grade for all customer sizes and enables faster feedback loops for future improvements.

## What Changes

- **EXTEND**: On ADO PATCH failure (backlog refine body update, status update, comment, create work item), capture response status, parsed ADO message (e.g. from `response.json().get("message", response.text[:500])`), and the list of JSON Patch operation paths; in debug mode log via `debug_log_operation(..., extra={"response_body": safe_snippet, "patch_paths": [...]})` so the failing field is identifiable without code changes.
- **EXTEND**: When re-raising or surfacing the error to the user, include the ADO error message (e.g. "TF51535: Cannot find field System.AcceptanceCriteria") and a short, actionable hint (e.g. "Check custom field mapping; see ado_custom.yaml or docs.").
- **NEW**: Add a small helper (e.g. in `ado.py`) that, given `response` (or `HTTPError.response`) and the patch `operations`, builds a structured error summary (status_code, message, patch_paths) and optionally logs it via `debug_log_operation`; use this helper at all ADO PATCH failure sites for consistency.
- **EXTEND**: Ensure `debug_log_operation` (or callers) safely truncate and redact response body in `extra` (e.g. 1–2 KB max, redact via `LoggerSetup.redact_secrets`) so ADO error payloads are safe to log.
- **EXTEND**: Apply the same error-handling and debug-logging pattern to other ADO PATCH call sites (status update, comment, create work item) so behavior is consistent across the adapter.
- **OPTIONAL (follow-up)**: Document custom mapping and `ado_custom.yaml` in user-facing docs; consider pre-flight field existence validation in a later change.

## Capabilities

- **api-error-diagnostics**: Structured API error capture, debug log content (response body snippet, patch paths), and user-facing error messages for ADO (and consistent pattern for other adapters).

## Impact

- **Affected specs**: `openspec/specs/debug-logging/spec.md` (extend with API failure logging requirements), new `openspec/specs/api-error-diagnostics/spec.md`.
- **Affected code**: `src/specfact_cli/adapters/ado.py` (PATCH failure handling, helper, debug logging), optionally `src/specfact_cli/runtime.py` (truncation/redaction for large `extra`); `src/specfact_cli/commands/backlog_commands.py` and `src/specfact_cli/sync/bridge_sync.py` (temp dir: use `tempfile.gettempdir()` instead of hard-coded `/tmp` for export/import paths).
- **Affected documentation** (<https://docs.specfact.io>): `docs/reference/debug-logging.md` (ADO PATCH failure content, "Examining ADO API Errors"); `docs/guides/troubleshooting.md` (subsection "Backlog refine or work item PATCH fails (400/422)"); `docs/adapters/azuredevops.md` (error diagnostics / troubleshooting link). No new pages; no change to `docs/index.md` or `docs/_layouts/default.html`.
- **Integration points**: Existing `debug_log_operation`, `LoggerSetup.redact_secrets`, console/exception handling in backlog refine and ADO adapter.
- **Backward compatibility**: No change to success paths; only failure paths gain richer logging and messages.

## Source Tracking

- **GitHub Issue**: #162
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/162>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
