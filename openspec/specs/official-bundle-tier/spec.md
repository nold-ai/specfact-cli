# official-bundle-tier Specification

## Purpose
TBD - created by archiving change module-migration-02-bundle-extraction. Update Purpose after archive.
## Requirements
### Requirement: Official-tier bundles declare tier and publisher in module-package.yaml and index.json

Every official bundle manifest SHALL declare `tier: official` and `publisher: nold-ai`.

#### Scenario: Official bundle manifest contains tier and publisher fields

- **GIVEN** any bundle in `specfact-cli-modules/packages/specfact-<name>/module-package.yaml`
- **WHEN** the manifest is parsed
- **THEN** it SHALL contain `tier: official`
- **AND** SHALL contain `publisher: nold-ai`
- **AND** SHALL contain a non-empty `signature_ed25519` field referencing the detached signature file

#### Scenario: Registry index entry carries tier and publisher metadata

- **GIVEN** any official bundle entry in `specfact-cli-modules/registry/index.json`
- **WHEN** the `tier` and `publisher` fields are read
- **THEN** `tier` SHALL be `official`
- **AND** `publisher` SHALL be `nold-ai`

### Requirement: crypto_validator validates official-tier bundles with stricter publisher check

The `crypto_validator.py` module SHALL enforce that `official`-tier bundles come from the `nold-ai` publisher allowlist.

#### Scenario: Official-tier bundle from nold-ai passes validation

- **GIVEN** a bundle with `tier: official` and `publisher: nold-ai`
- **AND** a valid Ed25519 signature verifiable with the project public key
- **WHEN** `crypto_validator.validate_module(bundle_path, manifest)` is called
- **THEN** validation SHALL succeed
- **AND** SHALL return a `ValidationResult` with `tier: official`, `publisher: nold-ai`, `signature_valid: True`

#### Scenario: Official-tier bundle from unknown publisher is rejected

- **GIVEN** a bundle with `tier: official` but `publisher: unknown-org`
- **WHEN** `crypto_validator.validate_module(bundle_path, manifest)` is called
- **THEN** validation SHALL fail with a `SecurityError` indicating the publisher is not in the official allowlist
- **AND** the bundle SHALL NOT be installed

#### Scenario: Official-tier bundle with invalid signature is rejected

- **GIVEN** a bundle with `tier: official` and `publisher: nold-ai`
- **AND** a tampered or missing Ed25519 signature
- **WHEN** `crypto_validator.validate_module(bundle_path, manifest)` is called
- **THEN** validation SHALL fail with a `SignatureVerificationError`
- **AND** the error message SHALL include the bundle name and expected key fingerprint
- **AND** the bundle SHALL NOT be installed

#### Scenario: Community-tier module is not elevated to official by manifest edit

- **GIVEN** a third-party module that declares `tier: official` and `publisher: nold-ai` in its manifest
- **AND** whose signature does not verify against the nold-ai public key
- **WHEN** `crypto_validator.validate_module()` is called
- **THEN** validation SHALL fail at signature verification
- **AND** SHALL NOT grant official-tier trust to the module

### Requirement: Module installer auto-installs bundle dependencies for official-tier bundles

When an official bundle with declared `bundle_dependencies` is installed, the installer SHALL automatically install all listed dependencies.

#### Scenario: Installing specfact-spec automatically installs specfact-project

- **GIVEN** the `nold-ai/specfact-spec` bundle with `bundle_dependencies: ["nold-ai/specfact-project"]`
- **AND** `specfact-project` is not currently installed
- **WHEN** `specfact module install nold-ai/specfact-spec` is executed
- **THEN** the installer SHALL first install `nold-ai/specfact-project` (with full integrity verification)
- **AND** SHALL then install `nold-ai/specfact-spec`
- **AND** SHALL display progress for both installs
- **AND** SHALL NOT install `specfact-spec` if `specfact-project` installation fails

#### Scenario: Installing specfact-govern automatically installs specfact-project

- **GIVEN** the `nold-ai/specfact-govern` bundle with `bundle_dependencies: ["nold-ai/specfact-project"]`
- **AND** `specfact-project` is not currently installed
- **WHEN** `specfact module install nold-ai/specfact-govern` is executed
- **THEN** the installer SHALL first install `nold-ai/specfact-project`
- **AND** SHALL then install `nold-ai/specfact-govern`

#### Scenario: Dependency already installed is not reinstalled

- **GIVEN** the `nold-ai/specfact-spec` bundle
- **AND** `specfact-project` is already installed at a compatible version
- **WHEN** `specfact module install nold-ai/specfact-spec` is executed
- **THEN** the installer SHALL skip reinstalling `specfact-project`
- **AND** SHALL log "Dependency nold-ai/specfact-project already satisfied (version X.Y.Z)"

#### Scenario: Dependency resolution is offline-capable when registry is unavailable

- **GIVEN** the `nold-ai/specfact-spec` bundle being installed while the registry network is unavailable
- **AND** `specfact-project` bundle tarball is locally cached
- **WHEN** the installer attempts to resolve and install the `specfact-project` dependency
- **THEN** it SHALL use the locally cached tarball
- **AND** SHALL verify its integrity before installation
- **AND** SHALL NOT fail due to registry unavailability when the dependency is cached

### Requirement: Official-tier trust is visible in module list and install output

Users SHALL be able to distinguish official-tier bundles from community-tier modules at a glance.

#### Scenario: specfact module list shows official tier badge

- **GIVEN** one or more official bundles are installed
- **WHEN** the user runs `specfact module list`
- **THEN** official-tier bundles SHALL display a distinguishing marker (e.g., `[official]` or equivalent rich-formatted badge)
- **AND** community-tier modules SHALL display a different or no marker

#### Scenario: Install output confirms official-tier verification

- **GIVEN** a user installs an official bundle
- **WHEN** installation completes successfully
- **THEN** the CLI output SHALL include a confirmation line indicating official-tier verification passed (e.g., "Verified: official (nold-ai) — SHA-256 and Ed25519 signature OK")

