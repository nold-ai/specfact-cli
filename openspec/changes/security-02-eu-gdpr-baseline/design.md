# Design: security-02-eu-gdpr-baseline

## Context

`security-01-unified-findings-model` normalizes findings, but it does not define which GDPR and EU constraints are mandatory by default. This change provides the baseline pack that scanners, policy resolution, and future enterprise overlays can all reuse without hardcoding privacy law assumptions into every bundle.

## Goals / Non-Goals

**Goals:**

- Define a core `security.gdpr` policy-pack contract with deterministic keys and enforcement semantics.
- Ship a default EU/GDPR baseline covering lawful basis, data minimization, retention, deletion, residency, and breach-handling checks.
- Keep the baseline portable across local-first and enterprise deployments.

**Non-Goals:**

- Implementing the module-side privacy scanners themselves.
- Providing legal advice or region-specific interpretation beyond the baseline rule vocabulary.
- Adding hosted policy distribution; enterprise push is handled later by the enterprise change family.

## Decisions

- The baseline is owned in core as YAML-backed policy-pack schema, not in a bundle, because enforcement semantics must be stable even when scanner implementations differ.
- GDPR findings reuse the unified security finding model and populate category-specific fields (`gdpr_article`, `data_residency`, `pii_type`) rather than inventing a parallel privacy report.
- Residency enforcement is allowlist-based by default: EU-hosted destinations are explicitly permitted, and non-EU targets require policy exception or advisory-only operation.
- Data subject rights are modeled as policy dimensions (`erasure`, `access`, `rectification`, `retention`) so downstream bundles can attach findings without redefining terminology.

## Risks / Trade-offs

- [Risk] GDPR interpretation varies by workflow and jurisdiction.
  Mitigation: keep the baseline focused on a narrow, documented control surface and route local deviations through policy packs and exception management.
- [Risk] Overly rigid residency defaults could block air-gapped or transitional deployments.
  Mitigation: allow advisory mode and explicit exceptions while preserving a consistent default baseline.
- [Risk] Privacy packs may drift from security finding semantics.
  Mitigation: require all emitted findings to use the unified security model and shared rule vocabulary.

## Migration Plan

1. Add the baseline spec delta and policy vocabulary.
2. Update core policy-engine parsing/validation to accept the `security.gdpr` namespace.
3. Land the module-side privacy bundle changes against the new baseline contract.
4. Document the default residency posture and exception path.

## Open Questions

- Whether Schrems II transfer-risk handling should remain metadata-only in core or gain a first-class policy key.
- Whether default retention windows belong in the baseline or in profile-specific overlays.
