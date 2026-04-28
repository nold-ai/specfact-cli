# Design: enterprise-01-policy-resolution-extension

## Context

The plan introduces enterprise policy push while preserving local-first behavior. The cleanest way to do that is to extend the existing resolution chain, not replace it, so enterprise layers become additive and optional.

## Goals / Non-Goals

**Goals:**

- Add org-mandatory and team-advisory resolution layers above local overrides.
- Define signed metadata for pushed rules and their precedence.
- Ensure non-enterprise users keep the current local behavior unchanged.

**Non-Goals:**

- Building the remote policy server itself.
- Creating RBAC or audit events; those land in later enterprise changes.
- Persisting remote rules outside the established local cache/config patterns.

## Decisions

- Resolution precedence is explicit: org mandatory, team advisory, explicit CLI flags, project config, profile defaults, built-in fallback.
- Enterprise resolution is opt-in by configuration detection; missing enterprise state results in local-only resolution, not an error.
- **Pushed-rule metadata contract (required fields):** every pushed rule record MUST carry `mandatory` (bool), `override_allowed` (bool), `effective_from` (timestamp/version), `pushed_by` (actor id), and `signed_by` (signing identity or key id). Optional fields may exist, but these five are normative for verification and audit.
- Pushed rules carry signature and provenance metadata so later audit logic can verify how a value entered the chain.
- **Override semantics:** team-advisory rules are overridable in local/project resolution **only when `override_allowed` is true**; when `override_allowed` is false, treat the team rule as non-overridable by local overrides (same practical posture as mandatory for that dimension). **Org-mandatory rules** (`mandatory: true`) remain **non-overridable** unless a future **signed-exception** mechanism is defined and verified in the policy engine.
- Team-advisory rules with `mandatory: false` follow the `override_allowed` rule above; org-mandatory rules remain the highest precedence layer before CLI/project/profile unless a signed exception path exists.

## Risks / Trade-offs

- [Risk] Layering becomes hard to explain to users.
  Mitigation: expose resolution inspection tooling and document precedence clearly.
- [Risk] Cached enterprise rules become stale.
  Mitigation: carry `effective_from` metadata and explicit sync status in the local cache.
- [Risk] Enterprise fields leak into free-tier UX.
  Mitigation: enterprise markers are hidden unless enterprise configuration is present.

## Migration Plan

1. Add the enterprise policy-resolution spec delta and profile-config-layering extension.
2. Implement enterprise-aware resolution ordering and metadata handling.
3. Add inspection and docs.
4. Reuse the same contract in later enterprise policy, audit, and budget flows.

## Open Questions

- Whether team-advisory rules should support local per-project pinning in addition to overrides.
- Whether the resolution inspector should show signature verification state in the first iteration.
