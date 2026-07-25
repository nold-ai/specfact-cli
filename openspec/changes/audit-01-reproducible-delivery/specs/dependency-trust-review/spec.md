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

#### Scenario: Trust policy runs before frozen dependencies are installed

- **WHEN** a CI job prepares a Python environment from the committed lock
- **THEN** the native dependency-trust policy SHALL run after checkout and before any
  `uv sync`, `uv build`, or other dependency-installing command
- **AND** a rejected lock SHALL prevent dependency build or installation in that job.

#### Scenario: Reviewed artifact evidence binds to one lock package record

- **GIVEN** a dependency exception identifies a normalized package name and exact version
- **WHEN** the native policy evaluates its source URL and SHA-256
- **THEN** both values SHALL occur in the same matching `[[package]]` record in `uv.lock`
- **AND** evidence belonging to another package record SHALL not satisfy the exception.

#### Scenario: Prohibited package identities are canonicalized

- **WHEN** a dependency exception or lock entry names a prohibited executable package with
  case, underscore, dot, or hyphen variations
- **THEN** the native policy SHALL compare the PEP 503 canonical package identity
- **AND** SHALL reject the prohibited package before accepting any exception record.

#### Scenario: Alerted release family uses an equivalent PEP 440 spelling

- **WHEN** a dependency exception or lock entry names `pycparser` in the blocked
  `3.0` release family using a post, local, or patch spelling
- **THEN** the native policy SHALL reject it before installation.

### Requirement: Security-tool floors preserve patched scanner versions

The repository SHALL keep reviewed minimum patched versions for security tools
in a checked-in policy file. Dependency trust validation SHALL reject a frozen
lock below a declared floor before installation.

#### Scenario: Semgrep lock downgrade is rejected

- **WHEN** the frozen lock resolves Semgrep below the reviewed patched floor
- **THEN** dependency trust validation SHALL fail before `uv sync` executes.

#### Scenario: Offline pre-commit does not resolve a moving latest version

- **WHEN** a contributor runs the dependency-trust hook without network access
- **THEN** it SHALL validate the committed floor locally
- **AND** SHALL NOT attempt to resolve a moving latest package version.

### Requirement: Frozen dependency advisories are audited and time-bounded

The repository SHALL audit the exact hash-protected requirements export against
the vulnerability advisory service. Any advisory SHALL fail the local and CI
gate unless a repository-owned record matches its exact package, version, and
advisory ID and remains within its review expiry.

#### Scenario: A known advisory has no reviewed exception

- **WHEN** the advisory scan reports a vulnerability in the frozen export
- **THEN** the security gate SHALL fail regardless of whether CVSS metadata is present
- **AND** SHALL report the package, version, and advisory identifier.

#### Scenario: An upstream-pinned transitive advisory is temporarily excepted

- **WHEN** an upstream package exactly pins a vulnerable transitive release and no
  compatible fixed release can resolve
- **THEN** an exception SHALL state the exact package/version/advisory IDs,
  review/expiry dates, rationale, and runtime mitigation
- **AND** the gate SHALL fail once the exception expires or a package, version,
  or advisory ID no longer matches.

#### Scenario: Security updates are proposed automatically

- **WHEN** Dependabot discovers a compatible patch or minor Python dependency update
- **THEN** it SHALL open a reviewable pull request on the weekly schedule
- **AND** the frozen delivery, advisory, and compatibility gates SHALL validate the
  resulting lock before it can merge.

### Requirement: License classification is conservative and evidence-based

The license gate SHALL reject explicit GPL/AGPL declarations while requiring an explicit reviewed classification for mixed metadata strings.

#### Scenario: Explicit GPL package is found

- **WHEN** installed-package metadata declares an explicit GPL or AGPL SPDX expression
- **THEN** the gate SHALL fail unless a matching, documented dev-only exception exists.

#### Scenario: Mixed license metadata is found

- **WHEN** installed-package metadata includes both permissive and GPL terms
- **THEN** the gate SHALL not infer a distributable GPL obligation solely from the mixed string
- **AND** SHALL fail until a reviewed package/version classification record is present.
