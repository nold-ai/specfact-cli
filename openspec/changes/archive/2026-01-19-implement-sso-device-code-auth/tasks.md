# Tasks: SSO Device Code Authentication for Azure DevOps & GitHub

## 1. Implementation

### 1.1 Architecture Overview

- [x] 1.1.1 This change adds device code authentication flows for both Azure DevOps and GitHub, with token storage and CLI integration.

### 1.2 Azure DevOps Device Code

- [x] 1.2.1 Uses `azure-identity` library's `DeviceCodeCredential`
- [x] 1.2.2 Zero-configuration (Entra ID integration automatic)
- [x] 1.2.3 Leverages corporate SSO/MFA automatically
- [x] 1.2.4 Supported for all Azure DevOps organizations with Entra ID

### 1.3 GitHub Device Code

- [x] 1.3.1 Custom RFC 8628 device code flow implementation (no first-party GitHub SDK available)
- [x] 1.3.2 Uses GitHub OAuth device authorization endpoint
- [x] 1.3.3 Can use official SpecFact GitHub App (client_id embedded) or user-provided client_id via `--client-id` flag
- [x] 1.3.4 Supports enterprise-grade GitHub instances (requires explicit client_id)
  - [x] Added guard to require `--client-id` or `SPECFACT_GITHUB_CLIENT_ID` for non-github.com hosts
  - [x] Added integration test for enterprise client_id requirement

### 1.4 Token Storage & Management

- [x] 1.4.1 Location: `~/.specfact/tokens.json` (user home directory)
- [x] 1.4.2 Format: JSON with provider-specific token metadata
- [x] 1.4.3 Permissions: 0o600 (owner read/write only)

### 1.5 CLI Integration

- [x] 1.5.1 New command group: `specfact auth`
- [x] 1.5.2 Support `specfact auth azure-devops` command
- [x] 1.5.3 Support `specfact auth github` command
- [x] 1.5.4 Support `specfact auth github --client-id YOUR_CLIENT_ID` command
- [x] 1.5.5 Support `specfact auth status` command
- [x] 1.5.6 Support `specfact auth clear [--provider azure-devops|github]` command
- [x] 1.5.7 Documented `auth` commands and added auth reference page to docs

### 1.6 Key Architectural Decisions

- [x] 1.6.1 **Separate implementations**: Azure uses `azure-identity` SDK; GitHub requires custom RFC 8628 implementation
- [x] 1.6.2 **File-based storage (Phase 1)**: Plaintext JSON storage for MVP. Encryption added Phase 2
- [x] 1.6.3 **Manual re-auth only (Phase 1)**: No token auto-refresh in MVP. Phase 2 adds background refresh
- [x] 1.6.4 **PAT fallback**: Users can still use `--pat` flag; existing workflows preserved
- [x] 1.6.5 **Provider detection**: Auto-detects configured provider; users can override with flags
