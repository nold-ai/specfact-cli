# Design: Enhanced Module Manifest Security and Integrity Validation

## Context

The marketplace decoupling roadmap identifies trust and integrity as the next critical step after bridge interoperability. Current module manifests provide compatibility/dependency metadata but do not provide cryptographic guarantees that a module artifact is authentic and untampered.

Current gaps:

- Manifest metadata has no publisher identity model and no integrity block.
- Installation paths do not enforce checksum/signature verification.
- Unsigned module acceptance is not explicitly policy-gated.

## Goals / Non-Goals

**Goals:**

- Add publisher and integrity metadata to module package manifests.
- Add checksum and optional signature verification primitives.
- Enforce trust checks in module install/registration pipeline.
- Provide explicit policy switch for unsigned modules.
- Provide signing automation for official modules.

**Non-Goals:**

- Full marketplace registry service APIs (marketplace-01).
- Runtime sandboxing/permission isolation for module execution.
- External key-management service integration.

## Decisions

### Decision 1: Additive manifest model extension

**Choice:** Extend `ModulePackageMetadata` with optional nested models: `PublisherInfo`, `IntegrityInfo`, and versioned dependency entries.

**Rationale:**

- Maintains backward compatibility for existing manifests.
- Creates clear typed contract for security metadata.
- Enables phased enforcement without breaking local/community modules.

### Decision 2: Integrity verification stages

**Choice:** Enforce verification in ordered stages: checksum first, signature second (if present and required by policy).

**Rationale:**

- Deterministic and fast tamper detection via checksum.
- Signature verification adds provenance guarantee when key material is available.
- Supports progressive rollout from checksum-only to strict signature enforcement.

### Decision 3: Explicit unsigned-module policy gate

**Choice:** Require explicit allow-unsigned configuration/flag to install unsigned modules in strict mode.

**Rationale:**

- Prevents accidental trust bypass.
- Keeps development ergonomics by allowing opt-in exceptions.

### Decision 4: CI-based signing for official modules

**Choice:** Introduce `scripts/sign-module.sh` and `.github/workflows/sign-modules.yml` for official module artifacts.

**Rationale:**

- Standardizes signature generation.
- Reduces manual operational drift.
- Improves traceability for release artifacts.

## Risks / Trade-offs

- **Risk:** Key distribution/rotation complexity.
  - **Mitigation:** Document trust model and key retrieval path; keep key URL in manifest.
- **Risk:** Signature verification dependencies may vary by environment.
  - **Mitigation:** Keep checksum as baseline and provide clear error/fallback messaging.
- **Risk:** Overly strict defaults could block local development.
  - **Mitigation:** Provide explicit `--allow-unsigned` flow with audit logging.
- **Trade-off:** Stronger security adds packaging and release complexity.
  - **Mitigation:** Automate in CI and keep policy explicit.

## Migration Plan

1. Introduce manifest model extensions with backward-compatible parsing.
2. Implement checksum verification in installer.
3. Add optional signature verification and policy controls.
4. Add signing automation script and CI workflow.
5. Update docs and rollout guidance.

Rollback strategy:

- Keep metadata parsing but disable strict signature enforcement.
- Use checksum-only trust checks temporarily.
- Preserve unsigned opt-in path for emergency recovery.

## Open Questions

- Should strict signature verification be default for all environments or only release pipelines?
- How should key rotation metadata be represented (single key URL vs key set)?
- Should unsigned-module opt-in be per-module, per-repo, or global policy?
