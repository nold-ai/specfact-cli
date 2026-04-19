# Design: telemetry-01-opentelemetry-default-on

## Architecture

```text
CLI invocation
      │
      ▼
[TelemetryEmitter]  ◄── resolution: env → CLI → project config → profile → builtin; then enterprise overlay (signed policy)
      │
      ├── build payload (allowlist validator)
      ├── write .specfact/telemetry/sent.log (append-only, redacted)
      └── export to OTLP endpoint (if configured) — never blocking
```

### Local audit log migration (`~/.specfact/telemetry.log` → `.specfact/telemetry/sent.log`)

**Strategy:** **dual-write + deprecation window**. New builds always append redacted transmit records to
`.specfact/telemetry/sent.log`. If `~/.specfact/telemetry.log` still exists, the CLI **also** appends the same redacted line
there for one deprecation series, emits a **stderr warning** pointing operators to the new path, and documents removal
timeline in release notes. **Export to OTLP (if configured) never pauses for migration** — it continues from the in-memory
payload after local append succeeds (dual-write failures are isolated: OTLP export errors do not delete local lines).

**Rollback / compatibility:** downgrading restores legacy-only behavior; upgrading re-enables dual-write until the legacy
file is removed. Consumers SHOULD read **both** paths while dual-write is active, then prefer `.specfact/telemetry/sent.log`
only after the deprecation window ends.

**Canonical telemetry resolution (highest precedence first; same order everywhere in this doc):**

1. `SPECFACT_TELEMETRY` environment variable (explicit per-invocation override).
2. `specfact telemetry disable|enable` CLI persisted preference.
3. `.specfact/config.yaml` `telemetry.enabled`.
4. Active profile telemetry defaults.
5. Built-in community default: `true` when no enterprise governance applies.

**Enterprise governance overlay (runs after steps 1–5 produce a candidate state):** when `.specfact/enterprise.yaml` is
present **or** `SPECFACT_ENTERPRISE=true`, telemetry **MUST NOT** finalize as **enabled** unless a **signed org-admin
policy** approves it per `enterprise-01-policy-resolution-extension`. Without that approval, **effective telemetry is
disabled** even if steps 2–5 would enable it; step **1** remains the hard per-process escape hatch.

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
- Usernames, email addresses, hostnames
- Error messages (only error *class* permitted, not content)

## Enterprise default (same overlay as above)

Enterprise detection uses `.specfact/enterprise.yaml` **or** `SPECFACT_ENTERPRISE=true`. The **enterprise governance
overlay** in the canonical list forces **disabled-by-default** telemetry until a **signed org-admin policy** opts in
via `enterprise-01-policy-resolution-extension` contracts (metadata + signing hooks as defined there—not duplicated
here).

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
