# registry-federation Specification

## Purpose

Defines the `specfact module add-registry` command's certificate-based verification flow, local registry store management, and the `--trust-local` flag for air-gapped registries.

## MODIFIED Requirements

### Requirement: Verify registry certificate at add-registry time

The CLI SHALL fetch and cryptographically verify the NOLD AI-signed registry certificate before storing a new registry.

#### Scenario: Add registry with valid certificate

- **GIVEN** `https://registry.acme.com/specfact/.specfact/registry-cert.json` exists and has a valid NOLD AI signature
- **WHEN** user runs `specfact module add-registry https://registry.acme.com/specfact`
- **THEN** CLI SHALL fetch the certificate
- **AND** SHALL verify the NOLD AI Ed25519 signature using the bundled root key
- **AND** SHALL store the registry in `~/.specfact/registries.json` with `effective_tier: verified` (from cert)
- **AND** SHALL display: `Registry added: Acme Internal Registry [verified]`

#### Scenario: Registry has no certificate — community tier

- **GIVEN** `{registry_url}/.specfact/registry-cert.json` returns 404
- **WHEN** user runs `specfact module add-registry {registry_url}`
- **THEN** CLI SHALL warn: `[WARN] No registry certificate found at {url}. Treating as community tier.`
- **AND** SHALL store registry with `effective_tier: community`
- **AND** SHALL NOT abort

#### Scenario: Certificate verification fails

- **GIVEN** the certificate JSON has an invalid or tampered NOLD AI signature
- **WHEN** user runs `specfact module add-registry {registry_url}`
- **THEN** CLI SHALL raise `RegistryCertVerificationError` with: `[ERROR] Registry certificate signature verification failed. Registry not added.`
- **AND** SHALL NOT store the registry

#### Scenario: Add registry with --trust-local (air-gapped)

- **GIVEN** user passes `--trust-local`
- **WHEN** user runs `specfact module add-registry https://internal.corp/specfact --trust-local`
- **THEN** CLI SHALL skip certificate fetch entirely
- **AND** SHALL store registry with `effective_tier: local`
- **AND** SHALL display: `Registry added: internal.corp [local] — modules from this registry are not NOLD AI certified`

### Requirement: Certificate expiry enforcement

The CLI SHALL detect expired registry certificates and downgrade the registry to community tier, warning the operator to renew.

#### Scenario: Registry certificate expires

- **GIVEN** a stored registry certificate whose `expires_at` is in the past
- **WHEN** CLI fetches from that registry
- **THEN** CLI SHALL downgrade effective tier to `community`
- **AND** SHALL warn: `[WARN] Registry certificate for {name} has expired. Treating as community tier. Renew at specfact.io/registries/register.`

#### Scenario: Certificate approaching expiry (30-day warning)

- **GIVEN** a stored certificate whose `expires_at` is within 30 days
- **WHEN** CLI fetches from that registry
- **THEN** CLI SHALL warn: `[WARN] Registry certificate for {name} expires in N days. Renew at specfact.io/registries/register.`
- **AND** SHALL continue with the certified tier

## Contract Requirements

- `fetch_registry_cert(registry_url: str) -> RegistryCert | None` — `@require` registry_url is HTTPS; `@beartype`
- `verify_registry_cert(cert: RegistryCert, root_key: Ed25519PublicKey) -> bool` — `@require` cert is non-None; `@beartype`
- `store_registry_cert(cert: RegistryCert, store_path: Path) -> None` — `@require` store_path.parent.exists(); `@beartype`
- `get_effective_registry_tier(registry_url: str, store: list[RegistryCert]) -> str` — `@ensure` result in {"official", "verified", "community", "local"}; `@beartype`
