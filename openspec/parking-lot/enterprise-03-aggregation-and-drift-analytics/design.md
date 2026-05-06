# Design: enterprise-03-aggregation-and-drift-analytics

## Context

The platform vision includes an enterprise learning loop, but that loop needs a stable contract for what can be contributed, how drift is measured, and how analytics come back to local teams. This change defines the client-side half of that contract.

## Goals / Non-Goals

**Goals:**

- Define a client-side contribution flag and aggregation payload.
- Define drift metrics that enterprise analytics can compute consistently.
- Reuse audit and knowledge evidence instead of adding a separate telemetry silo.

**Non-Goals:**

- Implementing the central analytics service.
- Building visualization dashboards in this change.
- Forcing every team to contribute local learnings to the organization.

## Decisions

- Aggregation is opt-in per learning/rule via `contribute-to-org: true`; the client never forwards local artifacts by default.
- Drift metrics are based on existing event streams: rule overrides, stale distillation windows, repeated pattern hits, and unresolved churn.
- Audit events are the backbone for enterprise correlation because they already identify actor, role, and action.
- Analytics are published back as evidence-like summaries so local tooling can consume them without a new client-only UI contract.

## Risks / Trade-offs

- [Risk] Aggregation could leak sensitive local context.
  Mitigation: require explicit contribution flags and keep payloads structured and minimal.
- [Risk] Drift metrics may be gamed if teams suppress contributions.
  Mitigation: treat metrics as advisory analytics, not sole compliance signals.
- [Risk] Multiple sources of truth could appear between analytics summaries and raw evidence.
  Mitigation: make summaries derivable from stable audit/evidence references.

## Migration Plan

1. Add the drift analytics spec delta and audit-trail extension.
2. Implement contribution metadata and aggregation payload builders.
3. Implement local publication of analytics summaries.
4. Connect a future enterprise backend without changing the payload contract.

## Open Questions

- Whether analytics summaries should always be stored locally or only when enterprise sync is enabled.
- Whether stale distillation thresholds belong in profiles or enterprise policy.
