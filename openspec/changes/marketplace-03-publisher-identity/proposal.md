# Change: Publisher Identity and Module Trust Chain

## Why

marketplace-02 provides multi-registry support and dependency resolution, but modules carry no publisher attestation beyond a simple `publisher: nold-ai` string (introduced by module-migration-02). To enable a verified third-party module ecosystem, the CLI needs a CA-style publisher identity system: NOLD AI vouches for publisher identity and module integrity, but not for module content or behaviour. Publishers host their own artifacts; NOLD AI hosts only the trust index.

Without publisher attestation and registry endorsement countersignatures, the CLI cannot distinguish between official, verified-community, and unregistered modules — making safe third-party module installation impossible.

## What Changes

- **NEW**: `src/specfact_cli/trust/` — trust orchestration layer with three modules:
  - `resolver.py` — trust tier resolution order (`official > verified > community > unregistered`)
  - `publisher_registry.py` — fetch, cache, and verify `publishers/index.json` from trust index
  - `key_store.py` — NOLD AI root public key bundle (Ed25519) embedded at CLI build time
- **MODIFY**: `src/specfact_cli/registry/crypto_validator.py` — extend `validate_module()` to add `verified` and `community` tier branches alongside the existing `official` branch from module-migration-02; add publisher record lookup from trust layer; do NOT replace the `official` path
- **MODIFY**: `src/specfact_cli/modules/module_registry/src/` — trust verification at install time (call trust layer before download); trust tier display in `specfact module search` and `specfact module info` output; `--trust-community` and `--trust-unregistered` flags with audit logging to `~/.specfact/module-audit.log`
- **MODIFY**: `scripts/publish-module.py` — add NOLD AI registry endorsement countersignature step after existing publisher signing step
- **NEW**: `scripts/sign-publishers.py` — signs `publishers/index.json` with NOLD AI root key (run by CI on merge to specfact-cli-modules)
- **NEW**: `docs/guides/publisher-trust.md` — user-facing guide on trust tiers, verification, install flags
- **MODIFY**: `docs/reference/module-commands.md` — document trust tier output, new flags
- **MODIFY**: `docs/_layouts/default.html` — add publisher-trust guide to sidebar navigation

**Backward compatibility**: Fully additive. The existing `official` tier path in `crypto_validator.py` is preserved unchanged. The transition from `publisher: nold-ai` (string, migration-02) to the structured `publisher:` block is handled by a format-detection branch in the parser — the CLI accepts both during a transition window.

**Rollback plan**: Revert trust/ module import, restore pre-marketplace-03 `crypto_validator.py` — all existing install flows remain unchanged.

## Capabilities

### New Capabilities

- `publisher-identity`: `publishers/index.json` schema definition, JSON Schema validation, structured publisher records (publisher_id, handle, tier, github_org, domain, public_key)
- `module-trust-chain`: structured `publisher:` block in `module-package.yaml` (Level 2 publisher attestation); `registry_signature` NOLD AI countersig in `registry/index.json` entries (Level 3 registry endorsement); NOLD AI root key bundle in CLI build
- `trust-resolution`: tier resolution order enforcement (`official > verified > community > unregistered`) at install time; `--trust-community` / `--trust-unregistered` flags; audit logging; tier badges in search/info output

### Modified Capabilities

- `module-security`: extend `validate_module()` in `crypto_validator.py` to add `verified` and `community` tier branches (spec delta only — extends existing capability from marketplace-01/migration-02)

## Impact

- **Affected code**:
  - `src/specfact_cli/trust/` (new: resolver.py, publisher_registry.py, key_store.py)
  - `src/specfact_cli/registry/crypto_validator.py` (modify: extend tier branches)
  - `src/specfact_cli/modules/module_registry/src/` (modify: trust verification + display)
  - `scripts/publish-module.py` (modify: add registry endorsement countersig step)
  - `scripts/sign-publishers.py` (new: CI signing script)
- **Affected specs**: New specs for `publisher-identity`, `module-trust-chain`, `trust-resolution`; delta spec for `module-security`
- **Affected documentation**:
  - `docs/guides/publisher-trust.md` (new)
  - `docs/reference/module-commands.md` (update: flags, trust display)
  - `docs/_layouts/default.html` (navigation update)
- **External dependencies**: None beyond existing `cryptography` library (already in requirements via arch-06)
- **Integration points**: Trust layer integrates with `crypto_validator.py` (signature checks), `module_installer.py` (pre-install gate), `custom_registries.py` (registry trust level)
- **Backward compatibility**: Fully additive; official tier path unchanged; dual-format publisher string handled
- **Hard blocker**: marketplace-02 (#215) must land first (provides `custom_registries.py` trust level infrastructure that `trust/resolver.py` extends)

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #327
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/327>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
