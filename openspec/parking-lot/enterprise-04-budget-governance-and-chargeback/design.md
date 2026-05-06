# Design: enterprise-04-budget-governance-and-chargeback

## Context

`finops-02-budget-approval-gates` defines local pause/resume and reporting semantics, but enterprise customers need those semantics to flow through org-wide approvals and chargeback reporting. This change adds the client-side enterprise extension without changing the core gate contract.

## Goals / Non-Goals

**Goals:**

- Define enterprise-specific budget approval routing metadata.
- Add team-aware chargeback reporting identifiers and summaries.
- Reuse FinOps evidence and enterprise audit events as the underlying source of truth.

**Non-Goals:**

- Implementing the hosted budget approval service.
- Replacing local budget gates for non-enterprise users.
- Introducing a separate enterprise-only FinOps schema.

## Decisions

- Enterprise budget routing reuses the same gate states from `finops-budget-gates`; the only addition is where approvals are resolved and how they are attributed.
- Chargeback reporting uses stable team or cost-center identifiers, not mutable display names, so enterprise reports stay joinable.
- Audit events remain the authoritative record for approvals and attribution changes.
- Enterprise configuration is optional and additive; if absent, local budget governance remains unchanged.

## Risks / Trade-offs

- [Risk] Enterprise routing can introduce latency or unavailable remote dependencies.
  Mitigation: preserve local wait-state semantics and allow explicit fallback behavior when routing is unavailable.
- [Risk] Chargeback identifiers may drift from org systems.
  Mitigation: validate identifiers locally and treat mismatches as auditable findings.
- [Risk] Teams may conflate chargeback reports with billing truth.
  Mitigation: document that chargeback summarizes attributed usage from FinOps evidence and approvals, not provider invoices.

## Migration Plan

1. Add the enterprise chargeback spec delta and FinOps gate extension.
2. Implement team-aware routing and chargeback payload support in core.
3. Extend audit/event flows with chargeback identifiers.
4. Connect remote enterprise routing later without changing core gate semantics.

## Open Questions

- Whether chargeback reports should always aggregate by team first or support cost center as the primary grouping.
- Whether enterprise routing failures should require explicit operator acknowledgement before local fallback.
