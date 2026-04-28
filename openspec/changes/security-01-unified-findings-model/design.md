# Design: security-01-unified-findings-model

## Architecture

```text
bundle runners: Semgrep, Grype, Syft, Gitleaks, Presidio, license scanners
        │
        ▼ normalise → SecurityFinding (this change owns the schema)
        │
[SecurityScorer] — CVSS → severity enum, policy-pack filters
        │
        ▼
[SecurityReport] (shared review-report envelope, `security` section)
        │
        ├── stdout / markdown / json
        ├── exit code (profile enforcement mode)
        └── evidence append (knowledge-01)
```

## Model

```python
class SecurityFinding(BaseModel):
    rule_id: str
    category: Literal["sast", "sca", "secret", "license", "pii", "gdpr", "sbom"]
    severity: Literal["blocker", "high", "medium", "low", "info"]
    location: CodeLocation | None
    message: str
    remediation: str | None
    fingerprint: str
    first_seen: datetime
    evidence_ref: str | None

    # category-specific optional fields
    cwe: str | None = None
    cve: str | None = None
    cvss_score: float | None = None
    spdx_license: str | None = None
    pii_type: Literal["email", "phone", "ssn", "credit_card", "passport", "custom"] | None = None
    gdpr_article: str | None = None
    data_residency: Literal["eu", "us", "uk", "other"] | None = None
```

## CVSS → severity mapping

| CVSS v3.1 band | Severity |
|---|---|
| 9.0–10.0 | blocker |
| 7.0–8.9  | high |
| 4.0–6.9  | medium |
| 0.1–3.9  | low |
| 0.0      | info |

Mapping is immutable in core; profile overrides can down-rate but not up-rate without explicit policy.

## Policy-pack namespace

`security/` packs under `policy-engine` with YAML schema:

```yaml
security:
  cve:
    deny_severity: [blocker, high]
    allow_list: [CVE-2024-12345]
  license:
    deny_spdx: [GPL-3.0, AGPL-3.0]
  pii:
    deny_types: [ssn, credit_card]
  gdpr:
    required_lawful_bases: [consent, legitimate_interest]
    data_residency_allowlist: [eu]
```

## CLI contract

```text
specfact review security [PATHS...]
  --category {sast,sca,secret,license,pii,gdpr,all}
  --report {json,markdown}
  --evidence / --no-evidence
```

## Non-goals

- Actual scanner toolchain integration (lives in module bundles).
- Vulnerability database management — we consume NVD / OSV via bundle runners.
- Runtime secret rotation — out of scope.

## Alternatives considered

1. **Per-category finding models**: rejected. Cross-cutting reports and policy packs would be combinatorial.
2. **Adopt existing SARIF format directly**: considered but rejected for primary storage — SARIF is export target, not authoring surface; our model is SARIF-compatible via a renderer.

## Risks

- Model bloat from category-specific fields. Mitigated by making category-specific fields optional and validating their presence per category at write-time.
- CVSS mapping disagreement across tools. Mitigated by canonical mapping table + per-bundle normalisation tests.
