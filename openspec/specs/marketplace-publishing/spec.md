# marketplace-publishing Specification

## Purpose

TBD - created by archiving change module-migration-02-bundle-extraction. Update Purpose after archive.

## Requirements

### Requirement: publish-module.py packages each bundle as a signed tarball

The `scripts/publish-module.py` script SHALL package each bundle directory into a compressed tarball, compute its SHA-256 checksum, sign it with the project Ed25519 key, and deposit the artifact and signature into `specfact-cli-modules/registry/modules/` and `specfact-cli-modules/registry/signatures/`.

#### Scenario: Bundle tarball is created with correct content

- **GIVEN** a bundle package directory (e.g., `specfact-cli-modules/packages/specfact-codebase/`)
- **WHEN** `python scripts/publish-module.py --bundle specfact-codebase` is executed
- **THEN** a tarball `specfact-codebase-<version>.tar.gz` SHALL be created in `specfact-cli-modules/registry/modules/`
- **AND** the tarball SHALL contain all files under `specfact-cli-modules/packages/specfact-codebase/` preserving relative paths
- **AND** SHALL NOT contain absolute paths or path-traversal entries (`..`)

#### Scenario: Tarball checksum matches manifest field

- **GIVEN** a published bundle tarball
- **WHEN** the SHA-256 of the tarball file is computed
- **THEN** it SHALL match the `checksum_sha256` field in the corresponding `index.json` bundle entry
- **AND** SHALL match the `integrity_sha256` in the bundle's `module-package.yaml`

#### Scenario: Tarball is signed with Ed25519

- **GIVEN** the project Ed25519 private key (referenced via `--key-file`)
- **WHEN** `publish-module.py` produces a bundle tarball
- **THEN** it SHALL generate a detached Ed25519 signature file at `specfact-cli-modules/registry/signatures/<bundle-id>-<version>.sig`
- **AND** the signature SHALL be verifiable with the corresponding Ed25519 public key
- **AND** `hatch run ./scripts/verify-modules-signature.py --require-signature` SHALL pass for the new entry

#### Scenario: Path-traversal content in bundle directory is rejected

- **GIVEN** a bundle package directory that contains a symlink or file resolving outside the bundle root
- **WHEN** `publish-module.py` attempts to package the bundle
- **THEN** it SHALL raise a `PackagingError` identifying the offending path
- **AND** SHALL NOT produce a tarball

### Requirement: Registry index.json is populated with bundle entries

The `specfact-cli-modules/registry/index.json` SHALL contain one entry per official bundle after publishing, following the existing schema (`schema_version`, `modules` array).

#### Scenario: Index contains all current official bundle entries

- **GIVEN** that all official bundles have been published via `publish-module.py`
- **WHEN** `index.json` is parsed
- **THEN** the `modules` array SHALL contain entries with `id` values: `nold-ai/specfact-project`, `nold-ai/specfact-backlog`, `nold-ai/specfact-codebase`, `nold-ai/specfact-spec`, `nold-ai/specfact-govern`, `nold-ai/specfact-requirements`

#### Scenario: Each index entry carries required metadata fields

- **GIVEN** a bundle entry in `index.json`
- **WHEN** the entry is inspected
- **THEN** it SHALL contain all required fields: `id`, `namespace`, `name`, `description`, `latest_version`, `core_compatibility`, `download_url`, `checksum_sha256`, `signature_url`, `tier`, `publisher`, `bundle_dependencies`
- **AND** `namespace` SHALL be `nold-ai`
- **AND** `tier` SHALL be `official`
- **AND** `publisher` SHALL be `nold-ai`
- **AND** `latest_version` SHALL match the semantic version in the bundle's `module-package.yaml`
- **AND** `core_compatibility` SHALL use PEP 440 specifier format (e.g., `>=0.29.0,<1.0.0`)

#### Scenario: Bundle-level dependency graph is declared in index entries

- **GIVEN** the `nold-ai/specfact-spec` entry in `index.json`
- **WHEN** the entry's `bundle_dependencies` field is inspected
- **THEN** it SHALL contain `["nold-ai/specfact-project"]`

- **GIVEN** the `nold-ai/specfact-govern` entry in `index.json`
- **WHEN** the entry's `bundle_dependencies` field is inspected
- **THEN** it SHALL contain `["nold-ai/specfact-project"]`

- **GIVEN** the `nold-ai/specfact-project`, `nold-ai/specfact-backlog`, or `nold-ai/specfact-codebase` entries
- **WHEN** the entries' `bundle_dependencies` fields are inspected
- **THEN** each SHALL be an empty array `[]`

#### Scenario: Publish script updates index atomically

- **GIVEN** an existing `index.json` and a new bundle being published
- **WHEN** `publish-module.py` writes the updated index
- **THEN** it SHALL write to a temporary file first and atomically rename to `index.json`
- **AND** the resulting `index.json` SHALL be valid JSON parseable without error
- **AND** the `schema_version` field SHALL be preserved unchanged

### Requirement: Offline verification gate must pass before index entry is written

No bundle entry SHALL be written to `index.json` until the bundle's tarball and signature pass offline integrity verification.

#### Scenario: Publish script runs verification before writing index

- **GIVEN** a bundle tarball and signature that have been produced
- **WHEN** `publish-module.py` prepares to write the index entry
- **THEN** it SHALL invoke `verify-modules-signature.py` (or equivalent inline verification logic) on the new tarball
- **AND** SHALL abort and raise `PublishAbortedError` if verification fails
- **AND** SHALL NOT write or modify `index.json` when verification fails

#### Scenario: Verification passes for correctly signed bundle

- **GIVEN** a bundle tarball signed with the valid Ed25519 project key
- **WHEN** offline verification runs
- **THEN** it SHALL return success with the verified checksum and publisher metadata
- **AND** `publish-module.py` SHALL proceed to write the index entry

#### Scenario: Verification fails for tampered tarball

- **GIVEN** a bundle tarball whose bytes have been modified after signing
- **WHEN** offline verification runs
- **THEN** it SHALL fail with a checksum mismatch error
- **AND** `publish-module.py` SHALL abort without modifying `index.json`

### Requirement: Bundle semantic versioning follows specfact-cli version convention

Each bundle's version SHALL be set at publish time and SHALL follow semantic versioning.

#### Scenario: Initial bundle version matches core version at extraction time

- **GIVEN** the first publish of each official bundle
- **WHEN** the bundle's `module-package.yaml` version field is set
- **THEN** it SHALL match the specfact-cli minor version at the time of extraction (e.g., if core is `0.29.0`, bundles start at `0.29.0`)

#### Scenario: Bundle version bump follows semver rules for subsequent publishes

- **GIVEN** a subsequent publish of a bundle after module source changes
- **WHEN** the publish script is run
- **THEN** a patch increment (e.g., `0.29.0 → 0.29.1`) SHALL be applied for fixes
- **AND** a minor increment SHALL be applied when new sub-commands are added to the bundle
- **AND** `publish-module.py` SHALL reject a publish if the version in `module-package.yaml` is not greater than the current `latest_version` in `index.json`
