# Change: Policy Packs & Enforcement Modes (Advisory/Mixed/Hard)

## Why




Policy enforcement today is binary — pass or fail. Different team sizes need different enforcement levels: a solo developer needs advisory warnings, a startup needs some hard gates, an enterprise needs full enforcement with tracked exceptions. Additionally, policies should be distributable as reusable packs (DoR/DoD basics, compliance packs, domain-specific rules) so teams don't reinvent quality gates. Three enforcement modes (advisory/mixed/hard) with installable policy packs make governance progressive and composable.

## What Changes




- **NEW**: Three enforcement modes with distinct local and CI behavior:
  - **Advisory (shadow)**: Warnings only locally, annotations + exit 0 in CI
  - **Mixed**: Configurable per rule (some warn, some block); partial blocking in CI
  - **Hard**: All violations block locally and in CI; evidence emission required
- **NEW**: Gradual escalation path: new policies start in shadow mode for a configurable period (default 2 weeks), then auto-promote to the profile's default mode. Manual override available.
- **NEW**: Policy packs — installable bundles of related policy rules:
  - `specfact policy install specfact/dor-dod-basics` — install built-in DoR/DoD policy pack
  - `specfact policy install org/payments-compliance` — install org-specific policy pack
  - Pack format: YAML manifest + rule definitions, versioned, signable (arch-06)
- **NEW**: `specfact policy list --show-mode` — list active policies with their current enforcement mode (shadow/advisory/mixed/hard) and escalation schedule
- **NEW**: Per-rule mode override in `.specfact/policy.yaml`:
  ```yaml
  policies:
    dor-dod-basics:
      mode: mixed
      rules:
        require-acceptance-criteria: hard
        require-business-value: advisory
  ```
- **EXTEND**: Policy engine (policy-engine-01) extended with mode-aware execution — `policy.validate` respects the configured mode per rule and per pack
- **EXTEND**: Profile integration — each profile tier has a default enforcement mode (solo=advisory, startup=advisory→mixed, mid-size=mixed, enterprise=hard)
- **NEW**: Ownership authority — this change is authoritative for policy mode execution semantics; dependent governance changes must consume this contract without redefining mode behavior.

## Capabilities
### New Capabilities

- `policy-packs-and-modes`: Distributable policy packs with three enforcement modes (advisory/mixed/hard), gradual escalation, per-rule mode overrides, and profile-driven defaults. Packs are installable, versioned, and signable.

### Modified Capabilities

- `policy-engine`: Extended with mode-aware execution (advisory/mixed/hard per rule), shadow-start for new policies, and gradual escalation scheduling


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #246
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/246>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: 36edfe3fb07e6226 -->