# Change: OpenTelemetry Default-On with PII-Safe Payload

## Why

SpecFact needs honest usage signal to improve the platform, but current telemetry is opt-in and under-utilised. Without default-on telemetry we cannot detect command failures, module-composition regressions, or adoption trends. At the same time, any default-on collection must be PII-safe, single-command opt-out, and automatically disabled in enterprise deployments where central governance owns its own observability. This change establishes the primitives consumed by FinOps outcome evidence, distillation loop health, and enterprise audit.

## What Changes

- **NEW**: OpenTelemetry emitter enabled by default for CLI invocations, emitting a PII-safe payload (command shape, module composition, duration, exit code, outcome enum).
- **NEW**: Allowlisted payload contract — explicit enumeration of permitted fields; file paths, repo names, prompt content, spec content, and free-form strings are rejected at the emitter boundary.
- **NEW**: `specfact telemetry [enable|disable|status]` command surface plus `SPECFACT_TELEMETRY=false` environment variable for CI-friendly opt-out.
- **NEW**: Enterprise-mode default: when `.specfact/enterprise.yaml` (or equivalent marker) is detected, telemetry defaults to `off` unless an `org-admin` signed policy opts in.
- **NEW**: Local audit log at `.specfact/telemetry/sent.log` (append-only) recording the exact redacted payload transmitted for each invocation, so users can verify contents.
- **EXTEND**: `specfact --version` surface prints current telemetry status.

## Capabilities

### New Capability: `telemetry-otel`

Emitter, payload contract, opt-out commands, enterprise default, local audit log.

## Impact

- Downstream (finops-01, knowledge-01, distillation) can rely on a single telemetry surface.
- Enterprise tier (enterprise-02 audit) reuses the same emitter path but routes to its own exporter.
- No runtime cost impact for air-gapped users: emitter is a no-op when no exporter is configured.

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
