# Change: Registry Federation and Trust Certificate Verification

## Why

marketplace-02 enables custom registries with a trust level, but any operator can claim any trust level. Without a certificate layer, the CLI cannot distinguish between a verified third-party registry (reviewed by NOLD AI) and an arbitrary self-hosted index. This change adds a CA-style registry certificate system: external registries obtain a signed certificate from NOLD AI, the CLI verifies it at add-registry time and on each fetch, and trust level is propagated as the minimum of the registry's tier and the publisher's tier.

The `--trust-local` flag for air-gapped enterprise registries bypasses certificate verification and marks modules `[local]` — they cannot be promoted to community/verified trust without central registration.

## What Changes

- **MODIFY**: `src/specfact_cli/registry/custom_registries.py` — extend `add_registry()` to fetch and verify registry certificate from `{registry_url}/.specfact/registry-cert.json` against the NOLD AI root key (from `trust/key_store.py`); store effective trust tier in `~/.specfact/registries.json`; add `--trust-local` flag for air-gapped registries
- **MODIFY**: `src/specfact_cli/trust/resolver.py` — integrate registry tier into effective tier calculation (min of publisher_tier and registry_tier)
- **NEW**: `src/specfact_cli/trust/registry_cert.py` — registry certificate fetcher, verifier, and local registry store manager
- **MODIFY**: `src/specfact_cli/modules/module_registry/src/` — add `[local]`, `[community]`, `[verified]`, `[official]` badges to search output accounting for registry tier; extend search to query all registered + verified registries
- **NEW**: `docs/guides/custom-registries.md` (update or supplement marketplace-02's guide) — registry certificate setup, air-gapped usage, trust score propagation
- **MODIFY**: `docs/_layouts/default.html` — update navigation if needed

**Backward compatibility**: Existing custom registries added via marketplace-02 without a certificate are treated as `community` tier by default (soft downgrade with a warning at `add-registry` time). `--trust-local` flag continues to allow air-gapped registries without central certificate.

**Rollback plan**: Remove registry certificate verification; restore flat custom registry trust level from marketplace-02.

## Capabilities

### New Capabilities

- `registry-federation`: add-registry certificate verification against NOLD AI root key; `~/.specfact/registries.json` local registry store with effective trust tier; `--trust-local` for air-gapped registries
- `registry-certificates`: registry certificate schema (`registries/index.json`); certificate fetch from `/.specfact/registry-cert.json`; certificate expiry enforcement
- `trust-propagation`: effective trust = min(publisher_tier, registry_tier); `[local]`, `[community]`, `[verified]`, `[official]` badges propagated to all search output

## Impact

- **Affected code**:
  - `src/specfact_cli/registry/custom_registries.py` (modify: certificate verification at add-registry)
  - `src/specfact_cli/trust/resolver.py` (modify: registry tier integration into effective tier)
  - `src/specfact_cli/trust/registry_cert.py` (new: certificate fetch + verify + store)
  - `src/specfact_cli/modules/module_registry/src/` (modify: registry-tier-aware badges in search)
- **Affected specs**: New specs for `registry-federation`, `registry-certificates`, `trust-propagation`
- **Affected documentation**:
  - `docs/guides/custom-registries.md` (update: certificate requirements, --trust-local, tier propagation)
  - `docs/_layouts/default.html` (navigation update if needed)
- **External dependencies**: None beyond existing `cryptography` library (already in requirements)
- **Hard dependency**: marketplace-03 (`trust/key_store.py`, `trust/resolver.py` base); marketplace-04 recommended but not hard-blocking

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #329
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/329>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
