## Context

This change defines an auditable dogfooding path proving SpecFact's validation
and AI-bloat defense loop on real project artifacts.

## Goals / Non-Goals

**Goals:**

- Produce objective proof artifacts for JSON evidence, AI-bloat findings,
  remediation packets, rerun comparison, and improved validation evidence.
- Ensure proof is reproducible in CI and local workflows.
- Tie proof to release readiness and product positioning.

**Non-Goals:**

- No unrelated feature expansion.
- No synthetic-only demo path; evidence must use real project artifacts.
- No requirement that SpecFact own the upstream planning lifecycle.

## Decisions

- Use a bounded PR or demo repository slice to keep proof practical and repeatable.
- Require machine-readable evidence output and rerun comparison artifacts.
- Couple proof completion to the validation-positioning wave exit criteria.

## Risks / Trade-offs

- [Proof too narrow] -> Mitigation: include at least one AI-bloat finding, one
  remediation packet, and one evidence improvement.
- [Proof too expensive] -> Mitigation: optimize for deterministic CI runs and
  reusable fixtures.

## Migration Plan

1. Select dogfooding slice and capture baseline evidence.
2. Implement tests and fail-first evidence.
3. Produce validation-loop artifacts and docs updates.

## Open Questions

- Which repository slice should be canonical for long-term regression proof.
