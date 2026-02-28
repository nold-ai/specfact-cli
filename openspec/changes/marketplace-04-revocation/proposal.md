# Change: Publisher and Module Revocation Infrastructure

## Why

marketplace-03 introduces publisher attestation and trust tiers but provides no mechanism to revoke a compromised publisher or a vulnerable module. Revocation infrastructure must exist **before any external publisher is onboarded** — otherwise a compromised key or malicious module cannot be removed from circulation once installed.

The revocation system follows a CA model: NOLD AI signs revocation entries in `publishers/revoked.json` and per-module revocation records in `registry/modules/revoked.json`. The CLI checks these on every install and surfaces warnings for already-installed revoked modules.

## What Changes

- **NEW**: `src/specfact_cli/trust/revocation.py` — revocation checker: fetch and cache `publishers/revoked.json` and module revocation records; enforce grace window policy by reason type
- **MODIFY**: `src/specfact_cli/modules/module_registry/src/` — pre-install revocation check; post-install revocation warning on `specfact module` invocation if installed module is revoked
- **NEW**: `.github/workflows/scan-bundles.yml` — CI AST scan for obfuscated code, shell=True subprocess calls, suspicious network-on-import patterns; blocks publication on failure
- **NEW**: `scripts/revoke-publisher.py` — signs revocation entry in `publishers/revoked.json` with NOLD AI key
- **NEW**: `scripts/revoke-module.py` — signs per-module revocation record with NOLD AI key
- **NEW**: `docs/trust/grace-window-policy.md` — user-facing policy document; ToS-linked
- **MODIFY**: `docs/reference/module-commands.md` — document revocation warning messages and grace window behaviour

**Backward compatibility**: Additive. Non-revoked modules see no change in install behaviour.

**Rollback plan**: Disable revocation check flag (`--skip-revocation-check`, internal-only CLI flag for emergency bypass); all install flows unchanged without the revocation pre-flight.

## Capabilities

### New Capabilities

- `publisher-revocation`: fetch, cache, and verify `publishers/revoked.json`; enforce hard block or grace window per reason type; warn on installed modules from revoked publishers
- `module-revocation`: per-module revocation records in `registry/modules/revoked.json`; grace window enforcement by reason; prominent warning on invocation of already-installed revoked modules
- `grace-window-policy`: by-reason grace windows (immediate / 30d / 14d / 7d); hard block after expiry; CLI behaviour during window per reason code
- `automated-scan`: CI GitHub Actions workflow scanning published bundles for obfuscated code, shell=True subprocess + URL combos, network-on-import patterns, known-bad eval/exec patterns

## Impact

- **Affected code**:
  - `src/specfact_cli/trust/revocation.py` (new: revocation checker + cache)
  - `src/specfact_cli/modules/module_registry/src/` (modify: pre-install check + invocation warning)
  - `.github/workflows/scan-bundles.yml` (new: AST scan CI)
  - `scripts/revoke-publisher.py` (new: signing script)
  - `scripts/revoke-module.py` (new: signing script)
- **Affected specs**: New specs for `publisher-revocation`, `module-revocation`, `grace-window-policy`, `automated-scan`
- **Affected documentation**:
  - `docs/trust/grace-window-policy.md` (new)
  - `docs/reference/module-commands.md` (update: revocation warning messages)
  - `docs/_layouts/default.html` (navigation update: add trust/ section)
- **External dependencies**: `ast` (stdlib, already available); no new external libraries
- **Hard dependency**: marketplace-03 (`publisher-identity`, `trust-resolution`) must land first — revocation builds on the trust layer and publisher index

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #328
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/328>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
