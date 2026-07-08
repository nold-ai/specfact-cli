## Context

This change implements the core-owned proposal scope for
`requirements-02-module-commands` from the 2026-02-15 architecture-layer
integration plan. Runtime grouped commands remain paired module scope in
`nold-ai/specfact-cli-modules#165`.

## Goals / Non-Goals

**Goals:**

- Define an implementation approach that stays within the proposal scope.
- Keep compatibility with existing module registry, adapter bridge, and contract-first patterns.
- Preserve offline-first behavior and deterministic CLI execution.
- Provide core helpers that module runtimes can reuse for import diagnostics,
  ProjectBundle extension IO, validation reports, and coverage summaries.

**Non-Goals:**

- No requirement authoring workflow in this core repository.
- No runtime `specfact requirements ...` command handlers in this core
  repository.
- No schema-breaking changes outside declared capabilities.
- No dependency expansion beyond the proposal and plan.

## Decisions

- Use module-oriented integration and registry lazy-loading patterns already used in SpecFact CLI.
- Keep all public APIs contract-first with `@icontract` and `@beartype`.
- Make all behavior extensions opt-in or backward-compatible by default.
- Add/modify OpenSpec deltas first so tests can be derived before implementation.
- Store normalized requirement context through the existing
  `requirements.inputs` extension from `requirements-01-data-model`.
- Treat missing downstream evidence links as profile-sensitive validation
  findings: strict/enterprise profiles fail, lighter profiles warn.

## Risks / Trade-offs

- [Dependency ordering drift] -> Mitigation: gate implementation tasks on declared prerequisites.
- [Capability overlap with adjacent changes] -> Mitigation: keep this change scoped to listed capabilities only.
- [Documentation drift] -> Mitigation: include explicit docs update tasks in apply phase.
- [Command ownership confusion] -> Mitigation: core ships reusable helpers only;
  runtime command handlers stay in modules scope.

## Migration Plan

1. Implement this change only after listed dependencies are implemented.
2. Add tests from spec scenarios and capture failing-first evidence.
3. Implement minimal production changes needed for passing scenarios.
4. Update public docs, issue body, and internal wiki mirror metadata.
5. Run quality gates and then open PR to `dev`.

## Open Questions

- Dependency summary: requirements-01-data-model and
  arch-07-schema-extension-system are implemented and archived.
- Runtime module command implementation remains tracked by paired modules issue
  `nold-ai/specfact-cli-modules#165`.
