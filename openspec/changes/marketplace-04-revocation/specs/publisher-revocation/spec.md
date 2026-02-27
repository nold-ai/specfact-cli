# publisher-revocation Specification

## Purpose

Defines the CLI's publisher revocation check: fetching, caching, and verifying `publishers/revoked.json`, and enforcing revocation policy at install time.

## ADDED Requirements

### Requirement: Fetch and cache publisher revocation index

The CLI SHALL fetch `publishers/revoked.json` from the trust index and cache with 1-hour TTL.

#### Scenario: Fetch publisher revocation index on install

- **WHEN** user installs any module
- **THEN** CLI SHALL fetch `{trust_index_url}/publishers/revoked.json`
- **AND** SHALL verify NOLD AI signature over the index
- **AND** SHALL cache the result in `~/.specfact/cache/publishers-revoked.json` with 1h TTL

#### Scenario: Cache hit within TTL

- **GIVEN** a valid cached `publishers-revoked.json` (age < 1h)
- **WHEN** user installs a module
- **THEN** CLI SHALL use the cached index without HTTP fetch

#### Scenario: Stale revocation cache when offline

- **GIVEN** cached `publishers-revoked.json` is older than 1h and CDN is unreachable
- **WHEN** user installs a module
- **THEN** CLI SHALL serve stale revocation index with `[WARN] Revocation index is stale; revocation check may be outdated`
- **AND** SHALL proceed with install

### Requirement: Block installation from revoked publishers

The CLI SHALL enforce revocation policy at install time, blocking or warning based on the revocation reason and grace window.

#### Scenario: Publisher revoked with security_incident — hard block

- **GIVEN** a publisher with `reason: security_incident` in `publishers/revoked.json`
- **WHEN** user installs any module from that publisher
- **THEN** CLI SHALL display `[ERROR] Publisher <handle> has been revoked (security_incident). Installation blocked.`
- **AND** SHALL exit with non-zero status
- **AND** SHALL NOT allow any flag to override this block

#### Scenario: Publisher revoked with policy_violation — warn during grace window

- **GIVEN** a publisher with `reason: policy_violation` and `revoked_at` within 30 days
- **WHEN** user installs a module from that publisher
- **THEN** CLI SHALL display `[WARN] Publisher <handle> is under revocation review (policy_violation). Grace window expires in N days.`
- **AND** SHALL prompt user to confirm install
- **AND** SHALL log to audit log on confirmation

#### Scenario: Publisher revoked with policy_violation — hard block after grace window expiry

- **GIVEN** a publisher with `reason: policy_violation` and `revoked_at` more than 30 days ago
- **WHEN** user installs a module from that publisher
- **THEN** CLI SHALL hard-block with `[ERROR] Publisher <handle> revocation grace window expired. Installation blocked.`

#### Scenario: Publisher revoked with publisher_request — warn within 7d grace

- **GIVEN** a publisher with `reason: publisher_request` within 7 days
- **WHEN** user installs a module from that publisher
- **THEN** CLI SHALL warn: `[WARN] Publisher <handle> has requested removal (publisher_request). Modules may be discontinued.`
- **AND** SHALL install with prompt confirmation

## Contract Requirements

- `check_publisher_revocation(publisher_id: str, index: PublisherRevocationIndex) -> RevocationStatus` — `@require` publisher_id is non-empty; `@ensure` result.is_revoked is bool; `@beartype`
- `fetch_revocation_indexes(trust_index_url: str, cache_dir: Path) -> tuple[PublisherRevocationIndex, ModuleRevocationIndex]` — `@require` trust_index_url is HTTPS; `@beartype`
