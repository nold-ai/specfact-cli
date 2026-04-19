# Change: Enterprise Aggregation and Drift Analytics

## Why

Enterprise governance should learn across teams without flattening all local context into one generic ruleset. This change defines how client-side learning contributions and drift metrics are aggregated so organizations can spot stale rules, overused overrides, and repeat patterns.

## What Changes

- **NEW**: `enterprise-drift-analytics` capability defining aggregation payloads, contribution flags, and drift metrics.
- **NEW**: `contribute-to-org` metadata so local learnings can opt into enterprise aggregation.
- **NEW**: Drift metrics for override rate, stale distillation cycles, cross-team pattern reuse, and unresolved rule churn.
- **EXTEND**: Enterprise audit and knowledge flows so promotions and overrides can be measured at the organization level.
- **EXTEND**: Enterprise evidence/reporting surfaces so drift analytics can be published back into local review and planning loops.

## Capabilities

### New Capabilities

- `enterprise-drift-analytics`: Aggregation payloads, contribution flags, and drift metrics for enterprise learning.

### Modified Capabilities

- `enterprise-audit-trail`: Extend audit events so drift analytics can correlate promotions, overrides, and approvals.

## Impact

- Depends on `knowledge-01-distillation-engine`, `enterprise-02-rbac-and-audit-trail`, and `knowledge-02-preflight-context-assembly`.
- Supplies the contract reused by future enterprise dashboards and analytics backends.
- Free-tier users are unaffected unless enterprise aggregation is explicitly configured.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #529
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/529>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open
- **Parent Feature**: #517
- **Parent Feature URL**: <https://github.com/nold-ai/specfact-cli/issues/517>
- **Sanitized**: false
