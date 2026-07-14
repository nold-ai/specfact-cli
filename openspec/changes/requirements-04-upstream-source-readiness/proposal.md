## Why

The import-first adapter from `openspec-01-intent-trace` can normalize an
unfinished native source into apparently trustworthy requirement evidence. A
local test of the official Spec Kit 0.12.15 scaffold produced six placeholder
records from its untouched `spec.md`. Invalid OpenSpec changes need the same
protection when repository policy requires native OpenSpec validation.

Readiness is part of evidence integrity. It must be decided where native
artifacts are parsed and normalized, before a module can persist a sidecar or
CI can consume coverage findings.

## What Changes

- Add a core-owned, atomic source-readiness preflight to native OpenSpec and
  Spec Kit requirement imports.
- Reject known incomplete Spec Kit sources with structured diagnostics and zero
  normalized records: official draft placeholders, unresolved
  `NEEDS CLARIFICATION`, no substantive Functional Requirement, or no meaningful
  acceptance scenario when user stories exist.
- Under explicit or strict/enterprise upstream-validation policy, invoke
  `openspec validate --strict --json` for the selected change; reject failed
  validation or an unavailable required validator with named diagnostics.
- Preserve portable basic OpenSpec import when policy does not require the
  OpenSpec CLI, without ambient executable probing or a new hard dependency.
- Preserve completed-source stable IDs, SHA-256 provenance, idempotency, and
  read-only behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `openspec-speckit-evidence-adapter`: Native import gains deterministic
  source-readiness outcomes before records are emitted.

## Impact

- Affected core code: `specfact_cli.requirements.importers`, requirements
  import result/diagnostic contracts, and upstream import tests.
- Affected modules runtime: `nold-ai/specfact-cli-modules#346` consumes the
  resulting diagnostics and prevents persistence for rejected sources.
- No upstream authoring schema, upstream write-back, or Spec Kit CLI dependency
  is introduced.
- Compatibility impact: the paired Requirements module must raise its minimum
  core compatibility version after this core release; existing accepted native
  sources remain backward-compatible.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #648
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/648>
- **Parent Feature**: #366 Requirements Layer
- **Follow-up To**: #350
- **Paired Modules Issue**: nold-ai/specfact-cli-modules#346
- **Last Synced Status**: open / Todo (aligned 2026-07-14)
- **Sanitized**: false
