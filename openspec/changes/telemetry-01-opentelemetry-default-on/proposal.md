# Change: Opt-In Validation Outcome Telemetry

## Why

SpecFact needs honest usage signal only if it earns trust first. Telemetry must
remain opt-in and should measure validation outcomes, not product-management
workflow analytics. The useful questions are whether validation ran, which
bounded module categories participated, how long it took, and what verdict was
returned.

## What Changes

- **NEW**: OpenTelemetry emitter available for CLI invocations only after
  explicit user consent.
- **NEW**: PII-safe payload focused on validation outcomes:
  `command_family`, `validation_surface`, `modules_composed`, `duration_ms`,
  `exit_code`, `outcome`, and bounded `failure_class`.
- **NEW**: Active opt-in consent prompt during `specfact init` or first
  interactive run. Non-interactive, CI, and unattended first runs default to
  disabled until `specfact telemetry enable` or `SPECFACT_TELEMETRY=true`.
- **NEW**: Telemetry disclosure copy available from `specfact telemetry status`.
- **NEW**: Allowlist enforcement rejects file paths, repo names, branch names,
  prompts, spec contents, free-form error text, and planning artifact bodies.
- **NEW**: Enterprise-mode default remains off unless a signed org-admin policy
  opts in.
- **NEW**: Local audit log at `.specfact/telemetry/sent.log` records the exact
  redacted payload transmitted for each invocation.
- **DOCUMENT**: Criteria for ever revisiting default-on: published transparency
  docs, stable allowlist tests, local audit adoption, explicit enterprise
  policy controls, and no unresolved privacy complaints.

## Capabilities

### New Capability

- `validation-outcome-telemetry`: Opt-in OpenTelemetry emitter for bounded
  validation outcome metrics with local auditability and strict PII rejection.

## Migration Notes

- The canonical append-only audit log is `.specfact/telemetry/sent.log`.
- Legacy `~/.specfact/telemetry.log` consumers receive a deprecation warning
  during any dual-write window.
- Existing legacy opt-in settings are honored for one deprecation series when
  new keys are unset.

## Impact

- Downstream analytics may consume validation outcome metrics only after opt-in.
- Enterprise environments remain off by default unless explicitly enabled.
- Air-gapped users pay no runtime cost when no exporter is configured.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #518
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/518>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open
- **Parent Feature**: #515
- **Parent Feature URL**: <https://github.com/nold-ai/specfact-cli/issues/515>
- **Sanitized**: false
