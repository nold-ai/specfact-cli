## Context

This change implements the narrowed validation-skill scope for
`ai-integration-01-agent-skill`. It is proposal-stage only and defines
implementation strategy without changing runtime code.

## Goals / Non-Goals

**Goals:**

- Define an implementation approach that stays within the proposal scope.
- Keep compatibility with existing module registry, adapter bridge, and contract-first patterns.
- Preserve offline-first behavior and deterministic CLI execution.

**Non-Goals:**

- No production code implementation in this stage.
- No schema-breaking changes outside declared capabilities.
- No upstream intent interviews, requirement authoring, or architecture
  generation.

## Decisions

- Use module-oriented integration and registry lazy-loading patterns already used in SpecFact CLI.
- Keep all public APIs contract-first with `@icontract` and `@beartype`.
- Make all behavior extensions opt-in or backward-compatible by default.
- Add/modify OpenSpec deltas first so tests can be derived before implementation.

## Risks / Trade-offs

- [Dependency ordering drift] -> Mitigation: gate implementation tasks on declared prerequisites.
- [Capability overlap with adjacent changes] -> Mitigation: keep this change scoped to listed capabilities only.
- [Documentation drift] -> Mitigation: include explicit docs update tasks in apply phase.

## Migration Plan

1. Implement this change only after listed dependencies are implemented.
2. Add tests from spec scenarios and capture failing-first evidence.
3. Implement minimal production changes needed for passing scenarios.
4. Run quality gates and then open PR to `dev`.

## Open Questions

- Dependency summary: Depends on governance-01-evidence-output and
  validation-02-full-chain-engine.
- Whether additional cross-change sequencing constraints should be hard-blocked in `openspec/CHANGE_ORDER.md`.
