# Change: Enhanced Module Manifest Security and Integrity Validation

## Why

`arch-05-bridge-registry` enables modular interoperability, but marketplace readiness still lacks trust guarantees for published modules. To prevent tampering and unsafe dependency drift, module manifests must carry integrity metadata and installation must verify checksums/signatures before enabling modules.

This change depends on `arch-05-bridge-registry` for stable lifecycle/protocol reporting behavior. Protocol false-legacy classification and duplicate lifecycle warning cleanup are owned by `arch-05`, not this change.

## What Changes

- **MODIFY**: Extend module manifest metadata (`ModulePackageMetadata`) with publisher identity, integrity fields, and versioned dependency entries.
- **NEW**: Add `src/specfact_cli/registry/crypto_validator.py` for checksum and optional signature verification.
- **MODIFY**: Extend module installation and registration flows to enforce integrity checks and reject invalid artifacts.
- **NEW**: Add signing automation script (`scripts/sign-module.sh`) and CI signing workflow for official module packages.
- **NEW**: Add unsigned-module safety controls requiring explicit allow-unsigned opt-in.
- **NEW**: Add documentation for module trust model and signature verification (`docs/reference/module-security.md`).

## Capabilities

### New Capabilities

- `module-security`: Cryptographic integrity and trust validation for module package installation and registration.

### Modified Capabilities

- `module-packages`: Manifest schema expanded with publisher/integrity metadata and versioned dependency contracts.
- `module-lifecycle-management`: Registration and installation behavior strengthened with integrity validation and unsigned-module controls.

## Impact

- **Affected specs**: New spec for `module-security`; delta specs for `module-packages` and `module-lifecycle-management`.
- **Affected code**:
  - `src/specfact_cli/models/module_package.py` (publisher/integrity/versioned deps)
  - `src/specfact_cli/registry/crypto_validator.py` (new)
  - `src/specfact_cli/registry/module_installer.py` (integrity checks)
  - `src/specfact_cli/registry/module_packages.py` (registration-time trust enforcement)
  - `scripts/sign-module.sh` (new)
  - `.github/workflows/sign-modules.yml` (new)
- **Affected documentation**:
  - `docs/reference/module-security.md` (new)
  - `docs/reference/architecture.md` (security/trust model updates)
  - `docs/_layouts/default.html` (navigation update)
- **Integration points**: module manifest parsing, module install/registration paths, CI packaging/signing pipeline.
- **Backward compatibility**: Backward compatible by default; unsigned modules remain possible only with explicit opt-in policy.
- **Rollback plan**: Disable signature enforcement and fallback to checksum-only or legacy manifest fields while preserving compatibility parsing.
- **Out of scope**: ModuleIOContract migration completion and protocol warning deduplication (addressed in `arch-05-bridge-registry`).

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #208
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/208>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
- **Sanitized**: false
