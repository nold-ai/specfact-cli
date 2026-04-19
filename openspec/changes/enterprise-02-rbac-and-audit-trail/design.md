# Design: enterprise-02-rbac-and-audit-trail

## Context

Enterprise governance needs more than rule precedence: it needs to prove who changed what and under which authority. This change defines that client-side trust surface so later enterprise features can share one audit model.

## Goals / Non-Goals

**Goals:**

- Define a stable role vocabulary for enterprise actions.
- Define a signed audit-event schema for enterprise-sensitive actions.
- Ensure audit events can be stored locally and forwarded later by enterprise adapters.

**Non-Goals:**

- Implementing a full hosted audit backend.
- Defining human approval UI flows.
- Replacing local CLI history or git history.

## Decisions

- Roles are coarse-grained and explicit to avoid early over-modeling: `org-admin`, `team-lead`, `developer`, `auditor`.
- Audit events are append-only structured records carrying actor, action, scope, target, signature metadata, and optional linked evidence ids.
- Policy resolution links to audit events by stable ids instead of embedding whole event payloads in configuration values.
- Local persistence is required so air-gapped and disconnected environments still have a verifiable audit trail.

## Risks / Trade-offs

- [Risk] Signature verification could introduce operational complexity.
  Mitigation: keep signature metadata mandatory while allowing pluggable verification backends.
- [Risk] Users may misinterpret roles as permission enforcement before server-side checks exist.
  Mitigation: document that this change defines client-side contracts and auditing first.
- [Risk] Audit logs may grow quickly.
  Mitigation: keep records structured and append-only, with downstream rotation/export handled later.

## Migration Plan

1. Add the enterprise audit spec delta and enterprise policy-resolution extension.
2. Implement role vocabulary and audit-event schema in core.
3. Link enterprise policy changes and overrides to audit event ids.
4. Reuse the same schema for budget and drift analytics later.

## Open Questions

- Whether audit events should always include hashed repository/project context or only when enterprise policy requires it.
- Whether local audit storage should be one file or partitioned by event type.
