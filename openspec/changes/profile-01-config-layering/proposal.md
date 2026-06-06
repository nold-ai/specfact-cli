# Change: Profile and Validation Config Layering

## Why

SpecFact needs adoption modes that tune validation strictness without changing
the evidence contract. A solo developer should get fast local feedback, while a
regulated team can hard-fail CI and require exception evidence. Profiles should
therefore configure severity, policy mode, module activation, and local/org
layering around validation.

## Ownership Alignment (2026-06-06)

- Repository assignment: stays in `specfact-cli` core.
- Canonical owner: core `init`, core config resolution, and validation severity
  defaults.
- The legacy `modules/profile/...` package structure is stale and MUST NOT be
  used as an implementation target.
- Implementation MUST keep profiles focused on validation rollout and evidence
  strictness, not broad ceremony enablement.

## What Changes

- **NEW**: Deterministic config layering: profile defaults -> org baseline -> repo
  overlay -> developer local.
- **NEW**: Built-in profile defaults for validation severity, policy mode,
  evidence persistence, clean-code enforcement mode, and module activation.
- **NEW**: `specfact init --profile <tier>` configures the validation posture for
  the project.
- **NEW**: Resolved-config display with source annotations.
- **NEW**: Divergence warnings when local overrides weaken org validation policy.
- **EXTEND**: Existing init behavior remains the implicit solo profile when no
  profile is specified.

## Capabilities

### New Capabilities

- `profile-validation-config-layering`: Profile-driven config resolution for
  validation severity, evidence behavior, policy mode, clean-code defaults, and
  module activation.

### Modified Capabilities

- `init-module-state`: Extended with profile-aware initialization while
  preserving the existing default.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #237
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/237>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: d7dfe1519fa64668 -->
