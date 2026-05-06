# Change: OpenTelemetry Active Opt-In with PII-Safe Payload

## Why

SpecFact needs honest usage signal to improve the platform, but the first public telemetry release must earn developer trust before collecting anything. Default-on telemetry would create avoidable community backlash even with a PII-safe payload because developers reasonably expect explicit consent for CLI usage reporting. This change therefore reverts the default-on posture and ships an active opt-in flow during `specfact init` or the first interactive run, with a concise disclosure of what is tracked, what is never tracked, and how to change the setting later.

## What Changes

- **NEW**: OpenTelemetry emitter available for CLI invocations only after explicit user consent, emitting a PII-safe payload (command shape, module composition, duration, exit code, outcome enum).
- **NEW**: Active opt-in consent prompt during `specfact init` or the first interactive `specfact` run. Non-interactive, CI, and unattended first runs default to disabled until `specfact telemetry enable` or `SPECFACT_TELEMETRY=true` is provided.
- **NEW**: Telemetry disclosure copy shown before consent and available from `specfact telemetry status`, clearly stating the tracked fields and rejected categories.
- **NEW**: Allowlisted payload contract — the five permitted **semantic** telemetry fields are **`command`**, **`duration`**, **`exit_code`**, **`outcome`** (enum), and **`module_composition`** (bundle/module names), mapped onto the versioned schema in `specs/telemetry-otel/spec.md` (additional bounded metadata such as `schema_version`, `run_id`, and coarse platform facts remain allowlisted there). Rejections are **per disallowed category** at the emitter boundary:
  - **File paths** — any filesystem path or repo-relative path is rejected.
  - **Repo names / branches** — repository identifiers, default-branch names, or remote URLs are rejected.
  - **Prompt content** — user prompts, system prompts, or chat transcripts are rejected.
  - **Spec content** — OpenSpec bodies, markdown specs, or large free-text blobs are rejected.
  - **Free-form strings** — unconstrained error text, log lines, or narrative strings are rejected (bounded error **class** only).
- **NEW**: `specfact telemetry [enable|disable|status]` command surface plus `SPECFACT_TELEMETRY=true|false` environment variable for CI-friendly per-process overrides.
- **NEW**: Enterprise-mode default: when `.specfact/enterprise.yaml` (or equivalent marker) is detected, telemetry defaults to `off` unless an `org-admin` signed policy opts in.
- **NEW**: Local audit log at `.specfact/telemetry/sent.log` (append-only) recording the exact redacted payload transmitted for each invocation, so users can verify contents.
- **EXTEND**: `specfact --version` surface prints current telemetry status.
- **DOCUMENT**: Criteria for revisiting default-on later: published telemetry transparency docs, stable allowlist tests, local audit log adoption, explicit enterprise policy controls, and evidence that the community accepts the opt-in payload contract without privacy complaints.

## Capabilities

### New Capability: `telemetry-otel`

Emitter, payload contract, active opt-in commands, enterprise default, local audit log.

## Migration Notes

- **Path change:** the canonical append-only audit log for transmitted telemetry moves to **`.specfact/telemetry/sent.log`**
  (per-project). Operators and automation should update tail/grep/ship scripts to the new location.
- **Legacy file:** if `~/.specfact/telemetry.log` exists after upgrade, the CLI **detects** it on first run, emits a
  **deprecation warning**, and (per `design.md`) follows the **dual-write** window so historical consumers keep working
  while new consumers prefer the project-local path. Optional one-time **copy/merge** tooling MAY ship as a follow-up
  command, but the contract only requires dual-append plus warning until the legacy file is removed.

## Impact

- Downstream (finops-01, knowledge-01, distillation) can rely on a single telemetry surface when users opt in.
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
