## ADDED Requirements

### Requirement: Flagged dependency exceptions are reviewed and expiring

The repository SHALL keep a version-specific review record for every flagged frozen dependency that remains required after investigation.

#### Scenario: Required parser dependency has current review evidence

- **GIVEN** `pycparser` is present in the frozen Python resolution through `cryptography` and `cffi`
- **WHEN** CI evaluates dependency trust policy
- **THEN** a repository-owned record SHALL name its exact version, source artifact, artifact SHA-256, source-provenance classification, review date, expiry, and transitive path
- **AND** the policy SHALL fail closed when the record is absent, stale, version-mismatched, or does not match the frozen artifact.

#### Scenario: A release has an obfuscation alert

- **GIVEN** an exact frozen package release has been identified by security review or Socket as obfuscated or malicious
- **WHEN** a developer adds a review record or the frozen lock contains that release
- **THEN** the native dependency-trust policy SHALL reject the release rather than treating the record as an approval
- **AND** the pre-commit hook and the `Dependency Trust Gate` CI status SHALL run the same policy.

#### Scenario: Unofficial executable wheel is proposed

- **WHEN** a frozen Python dependency contains an unofficial executable runtime distribution
- **THEN** dependency policy tests SHALL reject it
- **AND** CI SHALL use a pinned upstream runtime bootstrap or a reviewed equivalent instead.

### Requirement: License classification is conservative and evidence-based

The license gate SHALL reject explicit GPL/AGPL declarations while requiring an explicit reviewed classification for mixed metadata strings.

#### Scenario: Explicit GPL package is found

- **WHEN** installed-package metadata declares an explicit GPL or AGPL SPDX expression
- **THEN** the gate SHALL fail unless a matching, documented dev-only exception exists.

#### Scenario: Mixed license metadata is found

- **WHEN** installed-package metadata includes both permissive and GPL terms
- **THEN** the gate SHALL not infer a distributable GPL obligation solely from the mixed string
- **AND** SHALL fail until a reviewed package/version classification record is present.
