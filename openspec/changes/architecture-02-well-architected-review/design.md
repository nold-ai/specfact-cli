# Design: architecture-02-well-architected-review

## Context

Architecture review in SpecFact currently stops at traceability and structural metadata. The platform needs a first-class reviewer that can evaluate boundaries, interfaces, ADR coverage, and selected Well-Architected dimensions using the same deterministic review model used elsewhere.

## Goals / Non-Goals

**Goals:**

- Define an architecture review finding model and scorer contract.
- Add an interface diff command that turns architecture drift into reviewable evidence.
- Reuse the existing solution-architecture layer and ADR traceability instead of introducing parallel metadata stores.

**Non-Goals:**

- Implementing module-specific graph analyzers or language adapters in core.
- Replacing ADR authoring workflows.
- Automatically remediating architecture issues.

## Decisions

- Architecture findings use the shared review-report envelope with an `architecture` section rather than a standalone report type.
- `specfact architecture diff --since <ref>` is owned in core because interface classification is a contract surface, while deeper graph analysis lives in the modules bundle.
- Well-Architected review dimensions are modeled as finding categories so they can participate in policy, evidence, and distillation flows.
- ADR coverage is evaluated by linking architecture findings to `solution-architecture` references instead of inventing a new traceability layer.

## Risks / Trade-offs

- [Risk] Architecture review becomes too broad and overlaps with code review or resiliency.
  Mitigation: keep categories focused on boundaries, interfaces, ADR traceability, and well-architected framing.
- [Risk] Interface diff output varies by language/runtime.
  Mitigation: core owns the classification contract, while adapters can normalize language-specific details before emitting.
- [Risk] Human judgment is still required for some Well-Architected dimensions.
  Mitigation: allow advisory findings and checklist-backed evidence where automation is incomplete.

## Migration Plan

1. Add the `architecture-review` spec delta and `solution-architecture` extension.
2. Implement the finding model, diff classification, and envelope integration in core.
3. Land the module-side analyzer bundle against the new contract.
4. Update docs and governance evidence guidance.

## Open Questions

- Whether the interface diff command should emit SARIF in addition to JSON/markdown from the first iteration.
- Which Well-Architected dimensions should be mandatory blockers vs advisory-only at launch.
