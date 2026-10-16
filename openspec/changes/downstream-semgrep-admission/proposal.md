# Change: Downstream Semgrep build and admission

## Why

The frozen Semgrep 1.179.0 distribution requires MCP 1.29.0, which is affected by
CVE-2026-59951. Normal resolution cannot select the fixed MCP 1.30.0 while that
metadata remains unchanged. The owner authorized a separate implementation PR on
2026-10-16 Europe/Berlin. No merge or main promotion is authorized.

## What Changes

- Build a distinct downstream Semgrep local version from exact reviewed upstream
  wheel hashes. Preserve every runtime byte, archive permission and entry point;
  change only the distribution version, MCP requirement, associated directory names
  and complete RECORD.
- Verify seven platform wheel variants on Python 3.11, 3.12 and 3.13. Test actual
  installation, dependency coherence, unchanged SAST rules and positive/negative
  controls, plus MCP stateful session expiry, capacity and cleanup behavior.
- Add a standard-library admission boundary that requires exact artifacts, recipe,
  expiry, platform coverage and independently authenticated protected provenance.
  PR-built candidates cannot authorize themselves for production consumption.
- Bind vulnerability queries to the exact authenticated upstream Semgrep identity
  while retaining the actual local identity and complete fixed dependency graph.
  Unknown, skipped, missing, duplicate or failed audit results remain blocking.
- Keep production adoption blocked until protected producer evidence is available.
  Candidate validation does not replace the existing frozen graph or its audit.

## Capabilities

### New Capabilities

- `downstream-semgrep-admission`: deterministic metadata-only builds, platform
  verification and exact authenticated downstream artifact admission.

### Modified Capabilities

None. Existing provider, native capsule, Requirements, signature, Socket, FULL
review, coverage and timeout policies retain their authority.

## Impact

Affected surfaces: repository-owned tooling under scripts, reviewed build inputs
under ci, focused regression tests and a dedicated candidate/protected build
workflow. This does not modify the trusted Code Review provider catalog, issue
511, module signatures or existing application runtime behavior.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->

- GitHub Issue: #772, <https://github.com/nold-ai/specfact-cli/issues/772>
- Parent: #747; project: SpecFact CLI #1, Todo at implementation bootstrap.
- Labels: openspec, change-proposal, dependencies, security.
- Native blocked-by/blocking issue edges: empty at verified bootstrap.
- Production dependency: protected producer and full admission proof, not a
  prerequisite for isolated candidate implementation and testing.
