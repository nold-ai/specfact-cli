# module-marketplace-registry Specification

## Purpose

TBD - created by archiving change marketplace-01-central-module-registry. Update Purpose after archive.

## Requirements

### Requirement: Registry index schema with module metadata

The system SHALL define an index.json schema for the central registry containing module metadata including ID, namespace, version, download URLs, and checksums.

#### Scenario: Index includes module with full metadata

- **WHEN** registry index.json is parsed
- **THEN** it SHALL include schema_version field
- **AND** SHALL include modules array with module entries
- **AND** each module SHALL have: id, namespace, name, description, latest_version, core_compatibility, download_url, checksum_sha256

#### Scenario: Module ID uses namespace format

- **WHEN** module is listed in registry
- **THEN** id SHALL use format "namespace/name" (e.g., "specfact/backlog")
- **AND** namespace SHALL match separate namespace field

#### Scenario: Core compatibility uses PEP 440 specifier

- **WHEN** module declares core_compatibility
- **THEN** it SHALL use PEP 440 specifier format (e.g., ">=0.28.0,<1.0.0")
- **AND** SHALL be validated during module installation

### Requirement: Registry client fetches index from GitHub

The system SHALL implement a registry client that fetches index.json from the GitHub repository.

#### Scenario: Client fetches registry index

- **WHEN** client calls fetch_registry_index()
- **THEN** it SHALL request index.json from GitHub raw content URL
- **AND** SHALL parse JSON response
- **AND** SHALL return dict with schema_version and modules

#### Scenario: Network unavailable during fetch

- **WHEN** client attempts to fetch index but network is unavailable
- **THEN** it SHALL log warning "Registry unavailable, using offline mode"
- **AND** SHALL NOT raise exception
- **AND** SHALL return None or empty index

#### Scenario: Invalid JSON in registry index

- **WHEN** registry index contains invalid JSON
- **THEN** client SHALL log error with parse details
- **AND** SHALL raise ValueError with message "Invalid registry index format"

### Requirement: Module download with checksum verification

The system SHALL download module tarballs from registry URLs and verify checksums before extraction.

#### Scenario: Download module tarball

- **WHEN** download_module() is called with module_id and version
- **THEN** system SHALL look up module in registry index
- **AND** SHALL download tarball from download_url to temp directory
- **AND** SHALL verify checksum matches checksum_sha256 from index

#### Scenario: Checksum mismatch detected

- **WHEN** downloaded tarball checksum does not match index
- **THEN** system SHALL delete downloaded file
- **AND** SHALL raise SecurityError with message "Checksum mismatch for module X"
- **AND** SHALL NOT proceed with installation

#### Scenario: Module not found in registry

- **WHEN** download_module() is called with non-existent module_id
- **THEN** system SHALL raise ValueError with message "Module 'X' not found in registry"
- **AND** SHALL suggest using `specfact module search` to find available modules

### Requirement: Offline-first registry access

The system SHALL support offline operation with graceful degradation when registry is unavailable.

#### Scenario: Registry fetch fails gracefully

- **WHEN** registry fetch fails due to network issues
- **THEN** system SHALL log warning
- **AND** SHALL continue with built-in modules only
- **AND** SHALL NOT block CLI functionality

#### Scenario: Install command fails offline

- **WHEN** user runs install command but registry unavailable
- **THEN** system SHALL display error "Cannot install from marketplace (offline)"
- **AND** SHALL suggest installing from local tarball (future feature)
