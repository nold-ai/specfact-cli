# Design: telemetry-01-opentelemetry-default-on

This folder name is historical. The retained scope is opt-in validation outcome
telemetry only.

## Architecture

```text
CLI invocation
      │
      ▼
[TelemetryEmitter]  ◄── resolution: env → CLI → project config → init/first-run consent → profile → builtin; then enterprise overlay (signed policy)
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
4. Recorded `specfact init` or first-interactive-run consent.
5. Active profile telemetry defaults.
6. Built-in community default: `false` until explicit consent exists.

**Enterprise governance overlay (runs after steps 1–6 produce a candidate state):** when `.specfact/enterprise.yaml` is
present **or** `SPECFACT_ENTERPRISE=true`, telemetry **MUST NOT** finalize as **enabled** unless a **signed org-admin
policy** approves it per `enterprise-01-policy-resolution-extension`. `SPECFACT_TELEMETRY=false` is always a hard
per-process disable. `SPECFACT_TELEMETRY=true` is a transient per-process enable only outside enterprise governance, or
inside enterprise governance when the signed policy allows telemetry; it never bypasses a missing or disabling enterprise
policy.

**Legacy override compatibility:** `SPECFACT_TELEMETRY_OPT_IN` is treated as a deprecated alias for
`SPECFACT_TELEMETRY` only when `SPECFACT_TELEMETRY` is unset. `.specfact/config.yaml` `telemetry.opt-in` is treated as a
deprecated alias for `telemetry.enabled` only when `telemetry.enabled` is unset. New keys take precedence over legacy
keys, legacy usage emits a runtime deprecation warning, and conflicting legacy/new values emit a conflict warning while
using the new value.

## Active opt-in flow

`specfact init` and the first interactive `specfact` run SHALL present a consent prompt before any telemetry is emitted.
If the user accepts, the current command MAY emit exactly one summary event after consent is recorded and payload
validation passes. If the user declines, the current command remains silent. The prompt SHALL be short, neutral, and
explicit:

- What is tracked: bounded validation outcome fields (`command_family`, `validation_surface`, `modules_composed`,
  `duration_ms`, `exit_code`, `outcome`, `failure_class`), `schema_version`, `run_id`, `timestamp`, major/minor Python
  version, and coarse platform.
- What is not tracked: file paths, repository names, branch names, remotes, prompts, chat transcripts, OpenSpec/spec
  content, usernames, emails, hostnames, free-form logs, and raw error messages.
- How to change it: `specfact telemetry enable`, `specfact telemetry disable`, `specfact telemetry status`, and
  `SPECFACT_TELEMETRY=true|false`.

Non-interactive and CI sessions SHALL NOT prompt. They SHALL remain disabled unless an explicit env/config/persisted
enable source is present. First-run consent SHALL be stored as a normal user/project preference so `status` can report the
source.

## Payload contract (allowlist)

Permitted fields only. Required semantic fields:

- `command_family` (enum: validated against registered command families)
- `validation_surface` (enum: code_review, spec_validation, contract_validation, governance, other)
- `modules_composed` (list[str], bundle names)
- `duration_ms` (int)
- `exit_code` (int)
- `outcome` (enum: `ok | error | cancelled`)

Optional bounded semantic field:

- `failure_class` (enum, optional)

Required bounded metadata:

- `schema_version` (str, literal "1.0")
- `run_id` (uuid)
- `timestamp` (ISO-8601 UTC)
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
- Default-on collection in this release.
- Consent UI beyond `specfact init`, first interactive run, and the telemetry command surface.
- Rich telemetry (spans, traces) — only counter/histogram-equivalent summary events in v1.

## Alternatives considered

1. **Default-on community telemetry**: rejected for this release. Even PII-safe payloads need explicit trust-building
   before collection starts.
2. **Telemetry inside every module independently**: rejected. Each module would re-invent the allowlist; easy to leak PII.
3. **Full OpenTelemetry spans for every CLI run**: deferred. Excessive payload; v1 emits a single summary event per invocation.

## Default-on revisit criteria

SpecFact MAY revisit a default-on posture only after the opt-in release proves the trust contract:

- Published telemetry transparency documentation matches the shipped payload schema.
- Allowlist validator and regression tests block every rejected category listed above.
- Local `.specfact/telemetry/sent.log` lets users inspect transmitted payloads before filing privacy concerns.
- Enterprise signed-policy controls are implemented and documented.
- Community feedback shows no material privacy complaints against the opt-in payload contract for at least one release cycle.

## Risks

- Over-redaction may hide useful debugging signal. Mitigated by local `sent.log` that users can inspect and attach to bug reports voluntarily.
- Accidental payload schema drift. Mitigated by pydantic model + allowlist validator enforced in unit tests.
- Consent fatigue may reduce signal volume. Accepted for the first public telemetry release because developer trust is the gating adoption constraint.
