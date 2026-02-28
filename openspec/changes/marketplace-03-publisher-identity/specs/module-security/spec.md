# module-security Specification Delta

## Purpose

Delta spec extending the existing `module-security` capability (established by marketplace-01 and arch-06) to support `verified` and `community` tier branches in `validate_module()`. The `official` path defined in module-migration-02 is preserved and unchanged.

## MODIFIED Requirements

### Requirement: validate_module() dispatches by publisher tier

`validate_module()` in `crypto_validator.py` SHALL dispatch validation logic based on publisher tier, adding `verified` and `community` branches without replacing the existing `official` branch.

#### Scenario: Official module validation (existing — unchanged)

- **GIVEN** a module with `publisher: nold-ai` (legacy string) or `tier: official`
- **WHEN** `validate_module()` is called
- **THEN** SHALL execute the existing official validation path unchanged
- **AND** SHALL NOT call publisher registry lookup

#### Scenario: Verified module validation (new)

- **GIVEN** a module with `tier: verified` and a structured `publisher:` block
- **WHEN** `validate_module()` is called
- **THEN** SHALL call `trust/publisher_registry.resolve_publisher(publisher_id, index)` to fetch publisher record
- **AND** SHALL verify `publisher_signature` against the resolved public key
- **AND** SHALL verify `registry_signature` (NOLD AI countersig) against the bundled root key
- **AND** SHALL raise `PublisherSignatureMismatchError` if either check fails

#### Scenario: Community module validation (new)

- **GIVEN** a module with `tier: community` and a structured `publisher:` block
- **WHEN** `validate_module()` is called
- **THEN** SHALL call `trust/publisher_registry.resolve_publisher(publisher_id, index)`
- **AND** SHALL verify `publisher_signature` (publisher key from index)
- **AND** `registry_signature` check is optional for `community` tier (countersig may not be present)
- **AND** SHALL raise `PublisherSignatureMismatchError` if publisher signature fails

#### Scenario: Unknown tier

- **GIVEN** a module with an unrecognised `tier` value
- **WHEN** `validate_module()` is called
- **THEN** SHALL raise `UnknownTierError(tier)` with a clear message

## Contract Requirements

- `validate_module(module: ModuleManifest, tier: str, publisher_index: PublisherIndex | None) -> ValidationResult` — `@require` tier in `{"official", "verified", "community"}`; `@ensure` result.valid is bool; `@beartype`
- Existing contract on `official` path MUST remain satisfied — no regressions allowed
