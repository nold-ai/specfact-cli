## Context

## Scope rescope — 2026-09-20

Measure bounded defect-detection and operational overhead on real changes. Use existing CI artifacts; retain failures/reproductions that demonstrate test sensitivity. No mandatory immutable RED history or repeated seal approvals for the lean dogfood path. Stronger assurance experiments remain explicitly selected.

This owner-requested scope amendment takes precedence over conflicting default-workflow or dependency wording below. It changes planning only; runtime policy is unchanged. [Replacement policy](../requirements-09-minimal-evidence/proposal.md).

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
- Reuse machine-readable validation output and rerun comparison artifacts;
  summarize defect detection and overhead without a new evidence framework.
- Require full-chain links only for an explicitly selected experiment, preserving
  its missing-link failure semantics without making it the ordinary workflow.
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
