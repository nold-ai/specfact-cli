# devops-sync Specification

## Purpose

TBD - created by importing backlog item

## Requirements

## ADDED Requirements

### Requirement: Azure DevOps Device Code

The system SHALL use Azure DevOps device code authentication for sync operations with Azure DevOps.

#### Scenario: Azure

- **WHEN** a user requests azure devops device code authentication
- **THEN** the system uses Azure DevOps device code authentication for sync operations with Azure DevOps.
- **AND** uses `azure-identity` library's `DeviceCodeCredential`.
- **AND** zero-configuration (Entra ID integration automatic).
- **AND** leverages corporate SSO/MFA automatically.
- **AND** supported for all Azure DevOps organizations with Entra ID.

### Requirement: GitHub Device Code

The system SHALL use GitHub device code authentication for sync operations with GitHub.

#### Scenario: GitHub

- **WHEN** a user requests github device code authentication
- **THEN** the system uses GitHub device code authentication for sync operations with GitHub.
- **AND** custom RFC 8628 device code flow implementation (no first-party GitHub SDK available).
- **AND** uses GitHub OAuth device authorization endpoint.
- **AND** can use official SpecFact GitHub App (client_id embedded) or user-provided client_id via `--client-id` flag.
- **AND** supports enterprise-grade GitHub instances.

### Requirement: Token Storage & Management

The system SHALL use stored authentication tokens for DevOps sync operations when available.

#### Scenario: Token

- **WHEN** a user requests token storage & management
- **THEN** the system uses stored authentication tokens for DevOps sync operations when available.
- **AND** stores tokens at `~/.specfact/tokens.json` (user home directory).
- **AND** uses format JSON with provider-specific token metadata.
- **AND** enforces permissions 0o600 (owner read/write only).

### Requirement: CLI Integration

The system SHALL provide CLI authentication commands for DevOps sync operations.

#### Scenario: CLI

- **WHEN** a user requests cli integration
- **THEN** the system provides CLI authentication commands for DevOps sync operations.
- **AND** provides command group `specfact auth`.
- **AND** supports `specfact auth azure-devops` command.
- **AND** supports `specfact auth github` command.
- **AND** supports `specfact auth github --client-id YOUR_CLIENT_ID` command.
- **AND** supports `specfact auth status` command.
- **AND** supports `specfact auth clear [--provider azure-devops|github]` command.

### Requirement: Key Architectural Decisions

The system SHALL follow documented authentication architecture decisions for DevOps sync operations.

#### Scenario: Key

- **WHEN** the system performs authentication operations
- **THEN** the system follows documented authentication architecture decisions for DevOps sync operations.
- **AND** Azure uses `azure-identity` SDK; GitHub requires custom RFC 8628 implementation.
- **AND** Plaintext JSON storage for MVP. Encryption added Phase 2.
- **AND** No token auto-refresh in MVP. Phase 2 adds background refresh.
- **AND** allows users to still use `--pat` flag; existing workflows preserved.
- **AND** Auto-detects configured provider; users can override with flags.
