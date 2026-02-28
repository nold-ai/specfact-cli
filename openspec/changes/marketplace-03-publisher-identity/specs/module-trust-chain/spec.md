# module-trust-chain Specification

## Purpose

Defines the three-level trust chain for published modules: package integrity (Level 1, existing), publisher attestation via structured `publisher:` block (Level 2, new), and NOLD AI registry endorsement countersignature (Level 3, new).

## ADDED Requirements

### Requirement: Verify publisher attestation (Level 2)

The CLI SHALL verify the publisher's Ed25519 signature over the bundle at install time.

#### Scenario: Valid publisher attestation

- **GIVEN** a module bundle with a structured `publisher:` block containing a `publisher_signature`
- **AND** the publisher record is found in `publishers/index.json`
- **WHEN** CLI installs the module
- **THEN** CLI SHALL verify `publisher_signature` against the publisher's `public_key` from the index
- **AND** the signature covers `name + version + sha256` (canonical concatenation)
- **AND** SHALL proceed with install if signature is valid

#### Scenario: Publisher signature mismatch

- **GIVEN** a module bundle where `publisher_signature` does not verify against the publisher's public key
- **WHEN** CLI attempts install
- **THEN** CLI SHALL raise `PublisherSignatureMismatchError` and abort install
- **AND** SHALL NOT install the bundle under any flag combination

#### Scenario: Missing publisher_signature in structured block

- **GIVEN** a module with a structured `publisher:` block that lacks `publisher_signature`
- **WHEN** CLI attempts install
- **THEN** CLI SHALL treat the module as `unregistered` and apply unregistered install policy

### Requirement: Verify NOLD AI registry endorsement countersignature (Level 3)

The CLI SHALL verify the `registry_signature` (NOLD AI countersig) on each registry index entry before install.

#### Scenario: Valid registry endorsement

- **GIVEN** a registry `index.json` entry contains both `signature_ed25519` (publisher) and `registry_signature` (NOLD AI)
- **WHEN** CLI resolves a module from the registry
- **THEN** CLI SHALL verify `registry_signature` against the NOLD AI root public key
- **AND** the countersig covers `name + version + publisher_id + checksum_sha256` (canonical)
- **AND** SHALL proceed if valid

#### Scenario: Missing registry_signature (pre-marketplace-03 entries)

- **GIVEN** a registry entry that pre-dates marketplace-03 and has no `registry_signature` field
- **WHEN** CLI resolves the entry
- **THEN** CLI SHALL treat it as `official` tier if publisher is `nold-ai` (backward compatibility)
- **AND** SHALL surface `[WARN] No registry endorsement found; treating as official (legacy entry)`

#### Scenario: registry_signature verification failure

- **GIVEN** a registry entry where `registry_signature` does not verify against the NOLD AI root key
- **WHEN** CLI resolves the entry
- **THEN** CLI SHALL reject the entry and raise `RegistryEndorsementTamperError`
- **AND** SHALL NOT proceed with install

### Requirement: NOLD AI root public key bundled at build time

The CLI build process SHALL embed the NOLD AI Ed25519 root public key in `trust/key_store.py`.

#### Scenario: Root key loaded from bundle

- **GIVEN** the CLI is installed offline (no network)
- **WHEN** CLI loads the trust layer
- **THEN** CLI SHALL successfully load the NOLD AI root public key from the bundled `key_store.py`
- **AND** SHALL NOT require any network call to load the root key

#### Scenario: Overridable trust index URL

- **GIVEN** user has set `trust_index_url: https://internal.corp/trust/` in `~/.specfact/config.yaml`
- **WHEN** CLI fetches the publisher index
- **THEN** CLI SHALL use the configured URL instead of the default `https://specfact.io/trust/`
- **AND** SHALL still verify the NOLD AI signature using the bundled root key

## Contract Requirements

- `key_store.get_root_public_key() -> Ed25519PublicKey` — `@ensure` returns non-None; no network call
- `crypto_validator.validate_registry_endorsement(entry: RegistryEntry, root_key: Ed25519PublicKey) -> bool` — `@require` entry has checksum_sha256; `@beartype`
- `crypto_validator.validate_publisher_attestation(bundle_sha256: str, publisher_record: PublisherRecord, publisher_signature: str) -> bool` — `@require` all inputs non-empty; `@beartype`
