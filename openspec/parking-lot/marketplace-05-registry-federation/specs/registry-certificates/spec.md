# registry-certificates Specification

## Purpose

Defines the registry certificate schema, the canonical location (`/.specfact/registry-cert.json`), and the CLI's certificate store (`~/.specfact/registries.json`).

## ADDED Requirements

### Requirement: Registry certificate schema

The registry certificate served at `{registry_url}/.specfact/registry-cert.json` SHALL conform to the following schema.

#### Scenario: Valid certificate structure

- **GIVEN** a registry certificate JSON at `/.specfact/registry-cert.json`
- **WHEN** CLI fetches and parses it
- **THEN** it SHALL contain:
  - `registry_id` (string, non-empty)
  - `name` (string, human-readable registry name)
  - `url` (string, HTTPS URL matching the registry URL)
  - `tier` (string, one of: `official`, `verified`, `community`)
  - `certificate` (string, base64-encoded Ed25519 signature by NOLD AI over canonical cert JSON)
  - `issued_at` (string, ISO 8601 UTC)
  - `expires_at` (string, ISO 8601 UTC, must be after `issued_at`)

#### Scenario: Certificate URL field mismatch

- **GIVEN** a certificate whose `url` field does not match the registry URL it was fetched from
- **WHEN** CLI verifies the certificate
- **THEN** CLI SHALL raise `RegistryCertUrlMismatchError`: `[ERROR] Certificate URL mismatch: cert says {cert.url}, fetched from {registry_url}`
- **AND** SHALL NOT store the registry

### Requirement: CLI local registry store

The CLI SHALL maintain `~/.specfact/registries.json` with all registered registries.

#### Scenario: Store structure after adding a certified registry

- **GIVEN** a registry with a verified certificate is added
- **WHEN** CLI stores the registry
- **THEN** `~/.specfact/registries.json` SHALL contain an entry with:
  - `registry_id`, `name`, `url`, `effective_tier`
  - `trust_local: false`
  - `cert_issued_at`, `cert_expires_at`
  - `added_at` (timestamp of CLI add-registry call)

#### Scenario: Store structure for --trust-local registry

- **GIVEN** a registry added with `--trust-local`
- **WHEN** CLI stores the registry
- **THEN** `~/.specfact/registries.json` entry SHALL have:
  - `effective_tier: local`
  - `trust_local: true`
  - No `cert_*` fields (no certificate was fetched)

### Requirement: list-registries shows effective tier

The `specfact module list-registries` command SHALL display effective tier and certificate metadata for each registered registry.

#### Scenario: List shows all registries with tier and cert status

- **WHEN** user runs `specfact module list-registries`
- **THEN** CLI SHALL display all stored registries with: name, url, effective_tier badge, cert expiry date (if applicable)

## Contract Requirements

- `RegistryCert` Pydantic model: all fields required, `url` validated as HTTPS, `expires_at` validated as after `issued_at`
- `RegistryStoreEntry` Pydantic model: includes both cert metadata and effective_tier
- `@beartype` on all public functions in `trust/registry_cert.py`
