# Design: Publisher Identity and Module Trust Chain

## Context

marketplace-01 established Ed25519 publisher signing infrastructure. marketplace-02 adds multi-registry support and a trust level per registry. What is missing is a publisher identity layer: who is a publisher, what tier are they, and how does the CLI verify their identity at install time without a live accounts database.

**Current State:**

- `crypto_validator.py`: `validate_module()` has an `official` tier branch; publisher = `nold-ai` (string comparison)
- No structured publisher record; no publisher key lookup from a signed index
- No `community` or `verified` tier handling
- `custom_registries.py`: registry trust level exists (from marketplace-02) but not linked to publisher tier

**Constraints:**

- NOLD AI root key must be bundled at build time (offline-first; no runtime CA lookup)
- Trust index fetch must cache gracefully (7-day TTL fallback for CDN failures)
- Backward compatible: existing `official` tier install path must not be touched
- `specfact-cli-modules/` repo is separate — CLI reads from its deployed trust index URL, not from local files
- Must not introduce a server-side accounts database in Phase 1

## Goals / Non-Goals

**Goals:**

- Structured publisher identity with three tiers (official, verified, community)
- CLI verifies publisher attestation + registry endorsement at install time
- Trust tier displayed in search/info output
- Trust override flags with audit logging (offline-safe)

**Non-Goals:**

- Publisher self-registration UI (specfact.io-backend-phase1 — separate change, separate repo)
- Registry federation / external registry certificates (marketplace-05)
- Revocation infrastructure (marketplace-04)
- Paid module gating (marketplace-06, requires legal entity)

## Architecture

### Trust Layer (`src/specfact_cli/trust/`)

Three modules with clear separation of concerns:

```text
trust/
  key_store.py          — NOLD AI root public key (Ed25519), bundled at build time
  publisher_registry.py — fetch + cache publishers/index.json; verify NOLD AI signature
  resolver.py           — tier resolution order; install gate logic; audit logging
```

`resolver.py` calls `crypto_validator.py` for low-level Ed25519 operations — does NOT duplicate crypto.

### Trust Resolution Sequence

```text
specfact module install @mycompany/specfact-jira-sync
  │
  ├─ trust/publisher_registry.py: fetch publishers/index.json (cache 7d)
  ├─ key_store.py: verify NOLD AI signature over publishers/index.json
  ├─ Resolve publisher_id from module's module-package.yaml publisher block
  ├─ Fetch publisher record from index (publisher_id → tier + public_key)
  ├─ crypto_validator.py: verify publisher Ed25519 signature on bundle
  ├─ trust/resolver.py: resolve effective tier (publisher tier ∩ registry tier)
  │
  ├─ official  → install without prompt
  ├─ verified  → install without prompt
  ├─ community → prompt unless --trust-community (log to audit)
  └─ unregistered → block unless --trust-unregistered (log to audit)
```

### crypto_validator.py Extension Strategy

The existing `official` branch is preserved unchanged. New branches added alongside:

```python
# BEFORE (migration-02): single official check
if publisher == "nold-ai":
    validate_official(bundle, signature)

# AFTER (marketplace-03): tier dispatch, official path unchanged
match tier:
    case "official":
        validate_official(bundle, signature)      # unchanged
    case "verified":
        validate_verified(bundle, publisher_record, signature)   # new
    case "community":
        validate_community(bundle, publisher_record, signature)  # new
    case _:
        raise UnregisteredPublisherError(publisher)
```

### Publisher Record Format

`module-package.yaml` structured `publisher:` block (marketplace-03 format):

```yaml
publisher:
  publisher_id: pub_abc123
  handle: mycompany
  tier: verified
  public_key_fingerprint: sha256:abcdef...
  publisher_signature: "<Ed25519 sig over name+version+sha256>"
```

CLI accepts both the legacy `publisher: nold-ai` string (migration-02) and the structured block during the transition window. Format detected at parse time.

### Registry Endorsement Countersignature

`registry/index.json` entry gains a `registry_signature` field (NOLD AI countersig over `name+version+publisher_id+checksum_sha256`). This is **distinct** from the publisher's `signature_ed25519`. Both coexist:

```json
{
  "name": "specfact-jira-sync",
  "version": "1.0.0",
  "publisher_id": "pub_abc123",
  "tier": "verified",
  "checksum_sha256": "abcdef...",
  "signature_ed25519": "<publisher sig — from migration-02>",
  "registry_signature": "<NOLD AI countersig — new in marketplace-03>"
}
```

`scripts/publish-module.py` adds the countersig step after existing publisher signing.

## Decisions

### Decision 1: Trust Index Caching Strategy

**Options:**

- A: Always fetch from CDN, fail hard if unavailable
- B: Cache with TTL, serve stale with warning
- C: Cache only, no online refresh

Choice: B (7-day TTL cache, serve stale with staleness warning)

**Rationale:**

- Offline-first constraint: CLI must work without internet during runs
- 7-day staleness acceptable for publisher index (revocation handled by marketplace-04)
- Warning informs user when cache is stale without blocking install

### Decision 2: Root Key Bundling

**Options:**

- A: Fetch root key from well-known URL at runtime
- B: Bundle root key in CLI package at build time
- C: Store in user config (~/.specfact/)

Choice: B (bundled at build time)

**Rationale:**

- Offline-first: no network required for key verification
- Tamper-evident: key changes require a CLI release (auditable)
- Acceptable key rotation cadence: quarterly, requires CLI update

### Decision 3: Audit Log Location

**Choice**: `~/.specfact/module-audit.log` — append-only, human-readable, line-per-install

Captures: timestamp, module, tier, action (installed/blocked/prompted/accepted), flag used.

## Sequence Diagrams

### Install with Publisher Attestation

```text
User                CLI                  trust/           crypto_validator   CDN
 │                   │                    │                    │              │
 │ install @org/mod  │                    │                    │              │
 │──────────────────>│                    │                    │              │
 │                   │ fetch publishers/  │                    │              │
 │                   │─────────────────> │                    │              │
 │                   │                   │ GET /trust/publishers/index.json  │
 │                   │                   │──────────────────────────────────>│
 │                   │                   │<──────────────────────────────────│
 │                   │                   │ verify NOLD AI sig                │
 │                   │                   │────────────────────>              │
 │                   │                   │<────────────────────              │
 │                   │ resolve publisher │                    │              │
 │                   │<────────────────- │                    │              │
 │                   │ verify bundle sig │                    │              │
 │                   │────────────────────────────────────────>              │
 │                   │<────────────────────────────────────────              │
 │                   │ resolve tier      │                    │              │
 │                   │─────────────────> │                    │              │
 │                   │ tier=verified     │                    │              │
 │                   │<─────────────────│                    │              │
 │ install proceeds  │                   │                    │              │
 │<──────────────────│                   │                    │              │
```
