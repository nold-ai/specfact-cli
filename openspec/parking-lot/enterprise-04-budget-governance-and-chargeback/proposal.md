# Change: Enterprise Budget Governance and Chargeback

## Why

Project-level budget gates are useful locally, but enterprise organizations also need org-wide approval routing and chargeback summaries by team or cost center. This change extends the FinOps gate contract so enterprise policy can govern spend across many teams without fragmenting the client behavior.

## What Changes

- **NEW**: `enterprise-chargeback` capability defining org-level budget policy routing and chargeback report payloads.
- **NEW**: Team-aware chargeback fields and reporting contract keyed on enterprise identifiers.
- **NEW**: Integration point for remote approval routing without changing local budget-gate semantics.
- **EXTEND**: Budget gate evidence so org approvals and chargeback attributions are auditable.
- **EXTEND**: Enterprise audit flows so budget approvals and team spend attribution are recorded consistently.

## Capabilities

### New Capabilities

- `enterprise-chargeback`: Enterprise budget-governance routing and team-aware chargeback reporting.

### Modified Capabilities

- `finops-budget-gates`: Extend budget gates so org-level approvals and chargeback identifiers can be recorded.

## Impact

- Depends on `finops-02-budget-approval-gates`, `enterprise-01-policy-resolution-extension`, and `enterprise-02-rbac-and-audit-trail`.
- Supplies the contract reused by enterprise policy clients and future reporting backends.
- Local-only users keep the original budget-gate behavior; enterprise routing is additive.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #530
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/530>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open
- **Parent Feature**: #517
- **Parent Feature URL**: <https://github.com/nold-ai/specfact-cli/issues/517>
- **Sanitized**: false
