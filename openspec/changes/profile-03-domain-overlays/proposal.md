# Change: Domain Overlays & Org-Level Requirements Schema

## Why




Different business units within an enterprise have different requirements — the payments team needs regulatory references and risk owners on every requirement, the platform team doesn't. A single enterprise profile can't cover this variance without becoming unwieldy. Domain-specific overlays that extend the base profile with additional required fields, constraints, and policies let organizations enforce domain-specific governance without forking the entire profile system.

## What Changes




- **NEW**: Domain overlay definitions at `.specfact/profiles/{domain}.yaml`:
  ```yaml
  inherit: enterprise  # Base profile to extend
  requirements_schema:
    additional_required_fields:
      - regulatory_reference
      - risk_owner
      - data_classification
  architectural_constraints:
    - "All services must use org-shared payment-gateway adapter"
    - "PII fields must be encrypted at rest"
  policy_overrides:
    require-data-classification: hard  # Override from mixed to hard for this domain
  ```
- **NEW**: `specfact profile overlays list` — show available domain overlays
- **NEW**: `specfact profile overlays apply <domain>` — apply a domain overlay to the current repo
- **NEW**: Profile-aware requirements validation — when a domain overlay defines additional required fields, `specfact requirements validate` checks those fields
- **NEW**: Overlay inheritance: domain overlay inherits all settings from the base profile, only overriding specified fields
- **NEW**: Central distribution: domain overlays can be distributed via central config sources (profile-02) or marketplace (marketplace-01)
- **EXTEND**: Requirements data model (requirements-01) supports dynamic field requirements based on active domain overlay via arch-07 schema extensions
- **EXTEND**: Profile resolution order becomes: profile defaults → central baselines → domain overlay → local overlay

## Capabilities
### New Capabilities

- `domain-overlays`: Domain-specific profile overlays that extend base profiles with additional required fields, architectural constraints, and policy overrides. Distributed via central config sources or marketplace.

### Modified Capabilities

- `profile-config-layering`: Extended with domain overlay in resolution order
- `requirements-data-model`: Requirements validation respects domain-specific required fields


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #250
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/250>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: 6ff3705a63adfb8c -->