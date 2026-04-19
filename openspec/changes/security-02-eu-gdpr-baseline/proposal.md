# Change: EU and GDPR Baseline Security Policy Pack

## Why

SpecFact needs a first-party EU/GDPR baseline so privacy, residency, and lawful-basis checks are enforced consistently before downstream module scanners emit findings. Without a core baseline, every bundle would invent its own privacy posture and the security review surface would drift across teams.

## What Changes

- **NEW**: `security-gdpr-baseline` capability defining a versioned EU/GDPR baseline pack for lawful basis, retention, deletion, data minimization, residency, and breach-handling checks.
- **NEW**: Residency allowlist rules for EU-hosted models, exporters, and evidence storage targets.
- **NEW**: Rule vocabulary for GDPR references (`gdpr_article`, `lawful_basis`, `data_subject_request`, `data_residency`) consumed by the unified security finding model.
- **EXTEND**: Security policy-pack authoring guidance so profiles can enable `advisory`, `mixed`, or `hard` enforcement without changing scanner implementations.
- **EXTEND**: Knowledge/evidence emission so GDPR findings can be promoted into reusable rules and exceptions later.

## Capabilities

### New Capabilities

- `security-gdpr-baseline`: Core GDPR/EU policy baseline and residency requirements for security/privacy review.

### Modified Capabilities

- `policy-engine`: Add a `security.gdpr` namespace contract for lawful-basis, residency, retention, and deletion enforcement inputs.

## Impact

- Depends on `security-01-unified-findings-model` for the canonical security finding surface.
- Supplies the baseline consumed by module-side privacy and license/security bundles in `specfact-cli-modules`.
- Affects policy resolution, privacy-related docs, and future enterprise rule push flows; no existing public CLI contract is removed.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #523
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/523>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open
- **Parent Feature**: #513
- **Parent Feature URL**: <https://github.com/nold-ai/specfact-cli/issues/513>
- **Sanitized**: false
