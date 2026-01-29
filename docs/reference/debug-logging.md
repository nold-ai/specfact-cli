---
layout: default
title: Debug Logging
permalink: /debug-logging/
---

<!-- markdownlint-disable-next-line MD025 -->
# Debug Logging

When you run SpecFact CLI with the global `--debug` flag, the CLI writes debug output to your **console** and to a **rotating log file** under your user directory. This helps diagnose I/O, API, and template issues without cluttering normal output.

## For Users

### Enabling Debug Mode

Pass `--debug` before any command:

```bash
specfact --debug init
specfact --debug backlog refine --adapter ado --project my-project
specfact --debug plan select
```

Debug output appears in the terminal and is also appended to a log file.

### Where Logs Are Written

| Location | Purpose |
|---------|---------|
| **Console** | Same debug messages you see in the terminal (Rich formatting). |
| **`~/.specfact/logs/specfact-debug.log`** | Rotating log file (plain text). Created on first use when `--debug` is set. Directory is created with mode `0o755` if missing. |

- **Path**: `~` is your home directory (e.g. `/home/you` on Linux, `C:\Users\you` on Windows).
- **Rotation**: The file rotates at 5 MB and keeps up to 5 backup files (`specfact-debug.log.1`, …).
- **Scope**: User-level only; not tied to a specific repo or bundle.

### What Gets Logged

When `--debug` is on, the CLI logs:

1. **Debug messages**  
   Any line emitted via the internal `debug_print()`: template resolution steps, path discovery, fallbacks (e.g. in `specfact init`). Each line is prefixed with a **timestamp** and **caller** (module and function) for context.

2. **Structured operation metadata**  
   One JSON line per operation, with:
   - **operation** – Type (e.g. `api_request`, `file_read`, `template_resolution`).
   - **target** – Path or URL (sensitive parts redacted).
   - **status** – Result (e.g. `success`, HTTP status, `error`, `prepared`, `finished`, `failed`).
   - **caller** – Module and function that logged the operation (for context).
   - **error** – Optional error message on failure.
   - **extra** – Optional extra fields (redacted); for API calls may include payload (sanitized), response, reason.

**Log format**: Every line in the debug log file starts with a timestamp (`YYYY-MM-DD HH:MM:SS`), then a pipe and the message or structured JSON. Narrative lines include caller (module:function) before the message. File operations log status `prepared`/`finished`/`failed`; API operations log operation, URL (redacted), payload (sanitized), response, status, error, and reason where applicable.

**Redaction**: URLs, paths, and `extra` are passed through `LoggerSetup.redact_secrets` so tokens and secrets are masked in the log file.

### What Is Logged by Component

| Component | Operations / events logged (when `--debug`) |
|----------|---------------------------------------------|
| **auth azure-devops** | Start, success (PAT or OAuth), or error; key steps (OAuth flow, device code) when `--debug` is on. |
| **init** | Template resolution: paths tried, success/failure, fallbacks (e.g. development path, package path, `importlib` fallbacks). |
| **backlog refine** | File read for import: path, success/error (e.g. `--import-from-tmp`). File write for export: path, success/error (e.g. `--export-to-tmp`). |
| **Azure DevOps adapter** | WIQL request (redacted URL, method, status); Work Items GET (redacted URL, status); Work Items PATCH (redacted URL, status). On PATCH failure: structured log with `operation=ado_patch`, `status=failed`, and `extra` containing `response_body` (redacted snippet of ADO error payload) and `patch_paths` (JSON Patch paths attempted). |
| **GitHub adapter** | API request/response (redacted URL, method, status); on failure, redacted error snippet. |

### Example Log Snippets

**Plain debug line (from `debug_print`; timestamp and caller prefixed):**

```text
2025-01-28 14:30:00 | specfact_cli.commands.init:run | Debug: Trying development path: /path/to/templates
```

**Structured operation (from `debug_log_operation`; timestamp prefixed by formatter):**

```text
2025-01-28 14:30:01 | debug_log_operation {"operation": "file_read", "target": "/path/to/export.md", "status": "success", "caller": "specfact_cli.commands.backlog_commands:export_backlog"}
2025-01-28 14:30:02 | debug_log_operation {"operation": "ado_wiql", "target": "https://dev.azure.com/***/***/_apis/...", "status": "200", "caller": "specfact_cli.adapters.ado:..."}
2025-01-28 14:30:03 | debug_log_operation {"operation": "template_resolution", "target": "/usr/lib/.../templates/backlog", "status": "success", "caller": "specfact_cli.commands.init:..."}
```

### Troubleshooting With Debug Logs

1. Run the failing command with `--debug`:

   ```bash
   specfact --debug <command> <args>
   ```

2. Reproduce the issue, then open `~/.specfact/logs/specfact-debug.log`.
3. Look for:
   - **template_resolution** – Where `init` looked for templates and whether it succeeded.
   - **file_read** / **file_write** – Paths and success/error for backlog export/import.
   - **ado_wiql**, **ado_get**, **ado_patch** – ADO API calls (URLs redacted, status/error present).
   - **api_request** – GitHub (or other) API calls with status and optional error.

See also [Troubleshooting](../guides/troubleshooting.md).

### Examining ADO API Errors

When an Azure DevOps PATCH fails (e.g. HTTP 400 during `backlog refine ado` or work item update), the CLI does two things:

1. **Console** – You see the ADO error message and a short hint (e.g. "Check custom field mapping; see ado_custom.yaml or documentation."). If the ADO message names a field (e.g. "Cannot find field System.AcceptanceCriteria"), that field is highlighted so you can fix mapping or template issues.

2. **Debug log** (only when `--debug` is on) – One structured line is written with:
   - **operation**: `ado_patch`
   - **status**: `failed`
   - **error**: Parsed ADO message or short summary
   - **extra.response_body**: Redacted snippet of the ADO response (up to ~1–2 KB). Use this to see the exact server error (e.g. TF51535, field name).
   - **extra.patch_paths**: List of JSON Patch paths that were sent (e.g. `["/fields/System.AcceptanceCriteria", "/fields/System.Description"]`). Use this to see which field path failed.

To analyze an ADO API error:

1. Run the command with `--debug` and reproduce the failure.
2. In the console, read the red error line: it contains the ADO message and the custom-mapping hint.
3. Open `~/.specfact/logs/specfact-debug.log` and search for `"operation": "ado_patch"` and `"status": "failed"`.
4. In that line, use `extra.response_body` to see the server’s error text and `extra.patch_paths` to see which field paths were attempted.
5. If the error is about a missing or invalid field (e.g. custom process template), update [custom field mapping](../guides/custom-field-mapping.md) (e.g. `.specfact/templates/backlog/field_mappings/ado_custom.yaml`) or see [Azure DevOps Issues](../guides/troubleshooting.md#azure-devops-issues) in Troubleshooting.

---

## For Developers

### Debug log standard (apply consistently)

Debug logs are **critical for anomaly analysis, unexpected errors/failures, reporting, and bug reports**. Every debug log must follow the same pattern so logs are useful like in a regular production tool—**no single-line INFO-style entries**; every significant operation must provide **full context**.

**Required pattern for every significant operation:**

| Phase | What to log | Example status / extra |
|-------|----------------|-------------------------|
| **Started / prepared** | Once when the operation begins | `status=started` or `prepared`; `target`; `extra` (e.g. flow, method, cache) |
| **Progress / attempt** | For each distinct step (if multi-step) | `status=attempt`; `extra.method`, `extra.reason` (what was tried) |
| **Outcome** | Exactly once when the operation ends | **Success**: `status=success` (or HTTP status); `extra` (method, cache, reason). **Failure**: `status=failed` or `error`; `error=<message>`; `extra.reason` |

**Minimum content:**

- **Every line**: timestamp (automatic), caller (automatic or explicit).
- **Structured lines**: `operation`, `target` (redacted), `status`; when applicable: `error`, `extra` (payload, response, reason, method, cache—sanitized).

**Apply everywhere:** Auth flows, file I/O, API calls, template resolution, and any operation that can fail or affect behavior. Reference: `auth azure-devops` (started → cache_prepared → attempt interactive_browser → success/fallback → attempt device_code → success/failed → success token_stored).

### Runtime API

- **`specfact_cli.runtime.set_debug_mode(debug: bool)`**  
  Turn global debug mode on or off (e.g. from the CLI callback when `--debug` is set).

- **`specfact_cli.runtime.is_debug_mode() -> bool`**  
  Returns whether debug mode is currently on.

- **`specfact_cli.runtime.init_debug_log_file()`**  
  Ensures the debug log file under `~/.specfact/logs` is created and the file handler is set up. Called by the CLI when `--debug` is True so the first write goes to the file immediately.

- **`specfact_cli.runtime.debug_print(*args, **kwargs)`**  
  If debug is on: prints to the configured Rich console and appends a plain-text line to `~/.specfact/logs/specfact-debug.log` (args only; no Rich markup in the file). If debug is off: no-op.

- **`specfact_cli.runtime.debug_log_operation(operation, target, status, error=None, extra=None, caller=None)`**  
  If debug is on: writes one JSON line to the debug log file with `operation`, `target`, `status`, optional `error`, optional `extra`, and `caller` (inferred if not provided). `target` and `extra` are redacted via `LoggerSetup.redact_secrets`. If debug is off: no-op. Follow the debug log standard: log started/prepared → attempt → success/failed with reason.

### User-Level Log Directory

- **`specfact_cli.common.logger_setup.get_specfact_home_logs_dir() -> str`**  
  Returns `os.path.expanduser("~/.specfact/logs")`, creating the directory with `mode=0o755` and `exist_ok=True` on first use. Use this if you need the path for the debug log or related files.

### When to Use What

- **`debug_print(...)`**  
  For human-oriented messages (template paths, “trying X”, “using Y”). Shown in console and written as a single plain line to the log file.

- **`debug_log_operation(...)`**  
  For machine-friendly operation records (API calls, file I/O, template resolution result). Always use for URLs or paths; redaction is applied to `target` and `extra`.

### Adding New Log Points

1. **Follow the debug log standard**  
   For each significant operation: log **started/prepared** → **attempt** (if multi-step) → **success** or **failed** with **reason/error**. Include operation, target, status, error, extra (payload/response/reason—sanitized). Never log only one line for an operation that can succeed or fail; always log outcome and reason.

2. **New adapter or command**  
   When `is_debug_mode()` is True, call `debug_log_operation(operation, target, status, error=..., extra=..., caller=...)` at start, at each attempt, and at outcome. Use clear operation names (e.g. `ado_wiql`, `file_read`, `template_resolution`). For file ops: prepared → finished/failed. For API ops: attempt → success/failed with payload (sanitized), response, reason.

3. **New debug messages**  
   Use `debug_print(...)` for narrative steps; they will appear in console and in `specfact-debug.log` as plain text. Prefer pairing with `debug_log_operation` so the log has both human-readable and machine-friendly context.

4. **Sensitive data**  
   Pass URLs/paths/tokens only as `target` or inside `extra`; they are redacted before being written to the log file.

### Relation to Other Logging

- **`~/.specfact/logs/`** is for the **global** `--debug` session log only (`specfact-debug.log`). It is **not** the same as bundle-specific `.specfact/projects/<bundle>/logs/` (used for other runtime/agent logs). See [Directory Structure](directory-structure.md).
