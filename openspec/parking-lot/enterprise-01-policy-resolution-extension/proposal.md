# Change: Enterprise Policy Resolution Extension

## Why

SpecFact already resolves local policy from flags, project config, and profiles, but the enterprise tier needs two higher-priority layers for centrally pushed rules. This change adds those layers without altering the free-tier local-first experience.

## What Changes

- **NEW**: `enterprise-policy-resolution` capability adding org-mandatory and team-advisory layers above the existing local resolution chain.
- **ADDS**: Signed metadata fields for pushed rules (`mandatory`, `override_allowed`, `effective_from`, `pushed_by`, `signed_by`).
- **INTRODUCES**: Client-side resolution behavior that gracefully no-ops when no enterprise policy source is configured.
- **EXTEND**: Profile and policy resolution docs to describe enterprise precedence.
- **EXTEND**: Future budget and audit flows so they can depend on a common resolution contract.

## Capabilities

### New Capabilities

- `enterprise-policy-resolution`: Enterprise resolution-chain layers and signed pushed-rule metadata.

### Modified Capabilities

- `profile-config-layering`: Extend profile/config resolution so enterprise layers can precede project and profile values.

## Impact

- Depends on existing local resolution patterns from `profile-01-config-layering` and `policy-engine`.
- Supplies the contract reused by all later enterprise changes and module-side policy clients.
- Free-tier behavior remains unchanged when no enterprise adapter is configured.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #527
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/527>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open
- **Parent Feature**: #517
- **Parent Feature URL**: <https://github.com/nold-ai/specfact-cli/issues/517>
- **Sanitized**: false
