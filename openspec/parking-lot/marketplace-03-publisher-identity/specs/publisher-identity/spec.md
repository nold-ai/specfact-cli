# publisher-identity Specification

## Purpose

Defines the structured publisher record format, `publishers/index.json` schema validation, and the CLI's ability to resolve publisher metadata at install time.

## ADDED Requirements

### Requirement: Resolve publisher record from trust index

The CLI SHALL fetch and cache `publishers/index.json` from the configured trust index URL.

#### Scenario: Fetch publishers index on first install

- **GIVEN** the trust index URL is `https://specfact.io/trust/`
- **WHEN** user installs a module with a structured `publisher:` block
- **THEN** CLI SHALL fetch `publishers/index.json` from the trust index
- **AND** SHALL verify the NOLD AI signature over the index using the bundled root public key
- **AND** SHALL cache the index in `~/.specfact/cache/publishers-index.json` with a 7-day TTL

#### Scenario: Serve from cache when CDN is unavailable

- **GIVEN** a valid cached `publishers/index.json` exists (age < 7 days)
- **WHEN** the CDN is unreachable
- **THEN** CLI SHALL serve the cached index without error
- **AND** SHALL proceed with install using cached publisher data

#### Scenario: Stale cache warning

- **GIVEN** the cached `publishers/index.json` is older than 7 days
- **WHEN** the CDN is unreachable
- **THEN** CLI SHALL surface a `[WARN] Publisher index is stale (>7 days); verification may be outdated` warning
- **AND** SHALL proceed with install using stale cache rather than hard-failing

#### Scenario: Signature verification failure on fetched index

- **GIVEN** a fetched `publishers/index.json` fails NOLD AI signature verification
- **WHEN** user installs a module
- **THEN** CLI SHALL reject the index and raise `PublisherIndexTamperError`
- **AND** SHALL NOT fall back to the tampered index even if a valid cache exists

### Requirement: Resolve publisher_id to public key

The CLI SHALL look up a publisher's public key from the cached/fetched index.

#### Scenario: Publisher found in index

- **GIVEN** `module-package.yaml` contains a structured `publisher:` block with `publisher_id: pub_abc123`
- **WHEN** CLI processes the publisher block
- **THEN** CLI SHALL resolve `publisher_id` to the publisher's `public_key` in the index
- **AND** SHALL use that key for Ed25519 signature verification

#### Scenario: Publisher not found in index

- **GIVEN** `module-package.yaml` contains a `publisher_id` not present in the index
- **WHEN** CLI processes the publisher block
- **THEN** CLI SHALL treat the module as `unregistered`
- **AND** SHALL apply unregistered install policy (block unless `--trust-unregistered`)

### Requirement: Backward-compatible dual-format publisher field

The CLI SHALL accept both the legacy `publisher: nold-ai` string format and the structured `publisher:` block.

#### Scenario: Legacy string format

- **GIVEN** `module-package.yaml` contains `publisher: nold-ai` (string, from module-migration-02)
- **WHEN** CLI processes the publisher field
- **THEN** CLI SHALL infer `tier: official` and proceed through the official validation path
- **AND** SHALL NOT raise an error or warning about the legacy format

#### Scenario: Structured block format

- **GIVEN** `module-package.yaml` contains a structured `publisher:` block
- **WHEN** CLI processes the publisher field
- **THEN** CLI SHALL resolve publisher_id from the trust index and perform full attestation verification

## Contract Requirements

- `publisher_registry.fetch_publisher_index(trust_index_url: str) -> PublisherIndex` — `@require` trust_index_url is a non-empty HTTPS URL; `@ensure` result.nold_ai_signature is verified
- `publisher_registry.resolve_publisher(publisher_id: str, index: PublisherIndex) -> PublisherRecord | None` — `@require` publisher_id is non-empty; `@ensure` None returned (not raised) when publisher not found
- `@beartype` on all public functions in `trust/publisher_registry.py`
