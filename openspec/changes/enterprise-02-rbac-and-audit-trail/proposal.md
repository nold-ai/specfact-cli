# Change: Enterprise RBAC and Audit Trail

## Why

Once enterprise policy can be pushed into the client, SpecFact also needs role-aware actions and a signed audit trail for promotions, approvals, and overrides. Without those controls, enterprise governance would be opaque and untrustworthy.

## What Changes

- **NEW**: `enterprise-audit-trail` capability defining enterprise roles, signed audit events, and local audit persistence.
- **NEW**: Canonical roles `org-admin`, `team-lead`, `developer`, and `auditor` with action-level expectations.
- **NEW**: Signed audit-event schema for rule pushes, promotions, approvals, overrides, and telemetry opt-in changes.
- **EXTEND**: Enterprise policy-resolution flow so resolved values can be linked back to audited actions.
- **EXTEND**: Future budget and distillation features so they can emit events through a shared audit contract.

## Capabilities

### New Capabilities

- `enterprise-audit-trail`: Enterprise roles and signed audit events for client-side governance actions.

### Modified Capabilities

- `enterprise-policy-resolution`: Extend policy resolution with audit references for pushed and overridden values.

## Impact

- Depends on `enterprise-01-policy-resolution-extension` for enterprise value provenance.
- Supplies the contract reused by later enterprise drift and budget-governance changes, plus the module-side audit client.
- Adds audit visibility without changing free-tier workflows.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #528
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/528>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open
- **Parent Feature**: #517
- **Parent Feature URL**: <https://github.com/nold-ai/specfact-cli/issues/517>
- **Sanitized**: false
