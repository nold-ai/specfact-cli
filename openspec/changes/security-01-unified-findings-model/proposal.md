# Change: Unified Security Findings Model

## Why

Security review spans SAST, SCA, secret-scanning, license compliance, PII detection, GDPR compliance, and SBOM generation. Without a unified finding surface, each tool would invent its own schema, severity scale, and reporting format — making downstream evidence collection, policy gating, and distillation impossible. A single canonical finding model across all security categories means one evidence schema, one policy pack format, one report envelope, and one gate integration.

## What Changes

- **NEW**: `SecurityFinding` model with fields `rule_id`, `category` enum (`sast|sca|secret|license|pii|gdpr|sbom`), `severity`, `cwe?`, `cve?`, `spdx_license?`, `pii_type?`, `gdpr_article?`, `data_residency?`, `evidence_ref`, `first_seen`, `fingerprint`, `location`.
- **NEW**: `security` namespace in `policy-engine` packs — declarative allow/deny lists for CVE severity, SPDX license IDs, PII field types, GDPR lawful bases; honours `advisory | mixed | hard` modes from `policy-02-packs-and-modes`.
- **NEW**: `specfact review security` CLI contract delegating to bundle runners, aggregating findings into the shared review-report envelope under a `security` top-level section.
- **NEW**: Canonical severity mapping from CVSS v3.1 score bands to the review severity enum (`blocker|high|medium|low|info`).
- **EXTEND**: Evidence emission — findings append to knowledge-01 evidence schema when present.

## Capabilities

### New Capability: `security-findings`

`SecurityFinding` model, severity mapping, policy-pack namespace, CLI contract.

## Impact

- Depends on: existing `review-finding-model`, `review-report-model`, `policy-engine`, `policy-02-packs-and-modes`.
- Consumed by: security-02-eu-gdpr-baseline (rule pack), and three module-side bundles (SAST/SCA/secret, license, PII/GDPR) — out of scope here.
- **Compatibility:** tolerant JSON/`ReviewReport` consumers that ignore unknown top-level sections remain compatible when the
  new **`security`** object appears. Strict schema validators must either **pin `schema_version`**, **treat unknown keys
  as warnings**, or adopt an **explicit extension-key policy** before failing builds. Breaking changes for strict consumers
  require a **schema version bump** and published migration notes alongside emitters.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #522
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/522>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open
- **Parent Feature**: #513
- **Parent Feature URL**: <https://github.com/nold-ai/specfact-cli/issues/513>
- **Sanitized**: false
