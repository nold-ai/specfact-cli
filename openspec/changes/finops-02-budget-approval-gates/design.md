# Design: finops-02-budget-approval-gates

## Context

FinOps telemetry provides visibility, but budget governance requires a deterministic decision point before an expensive model invocation proceeds. This change introduces that decision contract in core so local, profile-driven, and later enterprise policy can all use the same gate semantics.

## Goals / Non-Goals

**Goals:**

- Define budget policy schema for per-flow and per-project limits.
- Add a gate that can pause execution before projected overspend.
- Provide burndown reporting and auditable approval events.

**Non-Goals:**

- Implementing remote approval services in this change.
- Building billing collectors for every model vendor.
- Enforcing global enterprise budgets; that comes later.

## Decisions

- Budget policy is evaluated before invocation using projected token and cost estimates when available; if estimates are missing, policy can either allow, warn, or require manual approval.
- The gate returns a resume token and a structured wait-state record instead of mutating command handlers with ad hoc approval logic.
- Burndown reporting is generated from FinOps evidence and approval events rather than a separate state store.
- Approval semantics are local-first: profile or project policy can resolve decisions without requiring a network dependency.

## Risks / Trade-offs

- [Risk] Projected cost estimates may be inaccurate.
  Mitigation: record projected vs actual values in evidence and allow profiles to tune gate strictness.
- [Risk] Pause/resume flows could feel heavy for small teams.
  Mitigation: support `auto` approval mode and advisory warnings for low-governance profiles.
- [Risk] Budget gates become entangled with enterprise-specific workflows.
  Mitigation: keep the core gate protocol generic and add remote approval only as an integration point.

## Migration Plan

1. Add the `finops-budget-gates` spec delta and FinOps evidence extension.
2. Implement budget policy parsing, gate evaluation, resume tokens, and reporting in core.
3. Integrate local profile/project policy resolution.
4. Add enterprise routing later without changing the gate contract.

## Open Questions

- Whether resume tokens should be one-time only or reusable until approval state changes.
- Whether burndown reporting should aggregate by profile in addition to project/team.
