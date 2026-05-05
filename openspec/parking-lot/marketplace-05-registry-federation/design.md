# Design: Registry Federation and Trust Certificate Verification

## Context

marketplace-02 added `custom_registries.py` with a trust level per registry (always / prompt / never). This trust level is user-assigned at `add-registry` time with no verification — any registry can be set to `always`. marketplace-05 replaces user-assigned trust with NOLD AI-certified trust tiers.

**Current State (marketplace-02):**

- `add_registry(url, trust)`: stores url + user-specified trust level
- No certificate check
- Trust level is a user assertion, not a verified claim

**Target State (marketplace-05):**

- `add_registry(url)`: fetches registry certificate from `{url}/.specfact/registry-cert.json`
- Verifies certificate against NOLD AI root key (from `trust/key_store.py`)
- Derives effective trust tier from certificate
- `--trust-local` bypasses certificate check for air-gapped use

**Constraints:**

- Offline-first: certificate must be cacheable; fetching may fail for air-gapped registries
- Backward compatible: existing registries without certificate → `community` tier (soft downgrade)
- Certificate expiry must be enforced (do not silently serve expired certs)

## Goals / Non-Goals

**Goals:**

- Registry certificate schema + verification at add-registry and periodically
- Trust score propagation: effective tier = min(publisher_tier, registry_tier)
- `--trust-local` for air-gapped / enterprise-internal registries (no certificate required)
- `[local]` badge for local-trust modules in search output
- Certificate expiry enforcement with warning before expiry

**Non-Goals:**

- Registry certificate issuance (server-side; specfact.io-backend-phase2)
- Registry revocation index (future extension)
- Per-module trust score API (specfact.io-backend-phase2)

## Architecture

### Registry Certificate Schema

Stored at `{registry_url}/.specfact/registry-cert.json`:

```json
{
  "registry_id": "reg_xyz789",
  "name": "Acme Internal Registry",
  "url": "https://registry.acme.com/specfact",
  "tier": "verified",
  "certificate": "<Ed25519 cert signed by NOLD AI>",
  "issued_at": "2026-02-27T00:00:00Z",
  "expires_at": "2027-02-27T00:00:00Z"
}
```

### `trust/registry_cert.py`

```python
# Key public API
def fetch_registry_cert(registry_url: str) -> RegistryCert | None
def verify_registry_cert(cert: RegistryCert, root_key: Ed25519PublicKey) -> bool
def store_registry_cert(cert: RegistryCert, store_path: Path) -> None
def load_registry_store(store_path: Path) -> list[RegistryCert]
def get_effective_registry_tier(registry_url: str, store: list[RegistryCert]) -> str
```

### Trust Propagation

`trust/resolver.py` updated to include registry tier in effective tier calculation:

```python
TIER_RANK = {"official": 3, "verified": 2, "community": 1, "local": 0, "unregistered": -1}

def resolve_effective_tier(publisher_tier: str, registry_tier: str) -> str:
    return min(publisher_tier, registry_tier, key=lambda t: TIER_RANK[t])
```

Note: `local` tier is below `community`. A `verified` publisher module served from a `local` registry is effective `local` — it cannot be promoted to `community` or `verified` without central registration.

### add-registry Flow with Certificate

```text
specfact module add-registry https://registry.acme.com/specfact
  │
  ├─ Fetch {url}/.specfact/registry-cert.json
  │   └─ If fetch fails: warn "No certificate found; treating as community tier"
  ├─ trust/registry_cert.py: verify_registry_cert(cert, root_key)
  │   └─ If verification fails: raise RegistryCertVerificationError
  ├─ Check cert not expired: cert.expires_at > now
  │   └─ If expired: warn + use community tier
  ├─ Store cert in ~/.specfact/registries.json (effective_tier = cert.tier)
  └─ "Registry added: Acme Internal Registry [verified]"
```

### --trust-local Flow

```text
specfact module add-registry https://internal.corp/specfact --trust-local
  │
  ├─ Skip certificate fetch
  ├─ Store in ~/.specfact/registries.json (effective_tier = "local")
  └─ "Registry added: internal.corp [local] — modules from this registry are not NOLD AI certified"
```

## Decisions

### Decision 1: Backward Compatibility for Uncertified Registries

**Choice**: Uncertified registries (no `/.specfact/registry-cert.json`) receive `community` tier with a warning at add-registry time.

**Rationale**: Breaking existing custom registry users would be a poor upgrade experience. Community tier is the appropriate unverified-but-identity-confirmed tier.

### Decision 2: Certificate Expiry Enforcement

**Choice**: Warn 30 days before expiry; at expiry, downgrade to `community` tier with warning. No hard block.

**Rationale**: Hard blocking at expiry would break workflows for registry operators who are slow to renew. Community-tier downgrade is reversible once cert is renewed and re-verified.

### Decision 3: Local Trust Registries in Search Output

**Choice**: `[local]` badge in search output, always (not `[community]` or above). Modules cannot be promoted beyond `local` without central registration.

**Rationale**: Prevents local trust from being misread as a NOLD AI endorsement. Explicit `[local]` label is honest about the trust boundary.
