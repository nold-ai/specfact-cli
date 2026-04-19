# Design: telemetry-01-opentelemetry-default-on

## Architecture

```text
CLI invocation
      │
      ▼
[TelemetryEmitter]  ◄── enabled? resolution chain: env > CLI flag > project config > profile > builtin
      │
      ├── build payload (allowlist validator)
      ├── write .specfact/telemetry/sent.log (append-only, redacted)
      └── export to OTLP endpoint (if configured) — never blocking
```

Resolution chain (telemetry enablement):

1. `SPECFACT_TELEMETRY` env var (explicit override)
2. `specfact telemetry disable|enable` CLI persistence
3. `.specfact/config.yaml` `telemetry.enabled`
4. Enterprise marker (`.specfact/enterprise.yaml`): default `false` unless org-admin policy overrides
5. Built-in default: `true` (community tier)

## Payload contract (allowlist)

Permitted fields only:

- `schema_version` (str, literal "1.0")
- `run_id` (uuid)
- `timestamp` (ISO-8601 UTC)
- `command` (enum: validated against registered command names)
- `subcommand` (enum, optional)
- `modules_composed` (list[str], bundle names)
- `duration_ms` (int)
- `exit_code` (int)
- `outcome` (enum: `ok | error | cancelled`)
- `python_version` (str, major.minor only)
- `platform` (enum: `linux | darwin | windows`)

Rejected at emitter boundary (hard fail during build, never transmitted):

- File paths, repo names, branch names
- Prompt content, spec content, rule content
- User names, email addresses, hostnames
- Error messages (only error *class* permitted, not content)

## Enterprise default

Detection via presence of `.specfact/enterprise.yaml` or `SPECFACT_ENTERPRISE=true`. When detected, built-in default flips to `false` and enable must come from a signed org-admin policy (`enterprise-01-policy-resolution-extension` provides signature verification hook).

## Non-goals

- Server-side collection stack (owned by ops).
- Per-user consent UI beyond the enable/disable CLI surface.
- Rich telemetry (spans, traces) — only counter/histogram-equivalent summary events in v1.

## Alternatives considered

1. **Opt-in default**: rejected. Historical adoption was ~0; no signal for platform improvement.
2. **Telemetry inside every module independently**: rejected. Each module would re-invent the allowlist; easy to leak PII.
3. **Full OpenTelemetry spans for every CLI run**: deferred. Excessive payload; v1 emits a single summary event per invocation.

## Risks

- Over-redaction may hide useful debugging signal. Mitigated by local `sent.log` that users can inspect and attach to bug reports voluntarily.
- Accidental payload schema drift. Mitigated by pydantic model + allowlist validator enforced in unit tests.
