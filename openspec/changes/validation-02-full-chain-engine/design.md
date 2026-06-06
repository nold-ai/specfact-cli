## Context

This change implements the narrowed validation evidence graph scope for
`validation-02-full-chain-engine`. It is proposal-stage only and defines
implementation strategy without changing runtime code.

## Goals / Non-Goals

**Goals:**

- Define an implementation approach that stays within the validation evidence
  graph proposal scope.
- Keep compatibility with existing module registry, adapter bridge, and contract-first patterns.
- Preserve offline-first behavior and deterministic CLI execution.

**Non-Goals:**

- No production code implementation in this stage.
- No schema-breaking changes outside declared capabilities.
- No ownership of upstream planning, requirements authoring, or architecture
  generation.

## Decisions

- Use module-oriented integration and registry lazy-loading patterns already used in SpecFact CLI.
- Keep all public APIs contract-first with `@icontract` and `@beartype`.
- Make all behavior extensions opt-in or backward-compatible by default.
- Add/modify OpenSpec deltas first so tests can be derived before implementation.
- Treat Spec Kit, OpenSpec, backlog, ADR, contract, code, test, and review
  artifacts as inputs to validation evidence.

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

- Dependency summary: Depends on traceability-01-index-and-orphans,
  governance-01-evidence-output, requirements input adapters where present,
  architecture-boundary input adapters where present, and policy-engine-01.
- Whether additional cross-change sequencing constraints should be hard-blocked in `openspec/CHANGE_ORDER.md`.
