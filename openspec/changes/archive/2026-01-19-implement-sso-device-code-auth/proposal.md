# Change: SSO Device Code Authentication for Azure DevOps & GitHub

## Why

### Current Limitation

SpecFact CLI currently supports only PAT (Personal Access Token) authentication, requiring users to manually create tokens in GitHub/Azure DevOps web interfaces. This creates friction during onboarding and adds secret management burden to users.

### Enterprise Problem

Organizations with SSO requirements (Entra ID, Okta, SAML) cannot adopt SpecFact CLI because:

- PATs bypass corporate SSO/MFA policies
- No centralized identity governance
- Creates compliance gaps in audit trails
- Users expect device code flow (matching `az cli`, `gh cli` UX)

### Business Value

- **Market Expansion**: Enables SSO-required organizations (enterprise segment)
- **UX Parity**: Matches developer expectations set by Azure CLI and GitHub CLI
- **Support Reduction**: Eliminates PAT-related onboarding questions
- **Compliance**: Enables audit trails via corporate identity systems
- **Zero-Config**: Device code is zero-configuration for users (no secrets to manage)

## What Changes

- **MODIFY**: Architecture Overview
  - This change adds device code authentication flows for both Azure DevOps and GitHub, with token storage and CLI integration.

- **MODIFY**: Azure DevOps Device Code
  - Uses `azure-identity` library's `DeviceCodeCredential`
  - Zero-configuration (Entra ID integration automatic)
  - Leverages corporate SSO/MFA automatically
  - Supported for all Azure DevOps organizations with Entra ID

- **MODIFY**: GitHub Device Code
  - Custom RFC 8628 device code flow implementation (no first-party GitHub SDK available)
  - Uses GitHub OAuth device authorization endpoint
  - Can use official SpecFact GitHub App (client_id embedded) or user-provided client_id via `--client-id` flag
  - Supports enterprise-grade GitHub instances

- **MODIFY**: Token Storage & Management
  - Location: `~/.specfact/tokens.json` (user home directory)
  - Format: JSON with provider-specific token metadata
  - Permissions: 0o600 (owner read/write only)

- **NEW**: CLI Integration
  - New command group: `specfact auth`
  - **Commands:**

    ```bash
    # Authenticate with Azure DevOps (zero-config)
    specfact auth azure-devops

    # Authenticate with GitHub
    specfact auth github

    # Override client_id for GitHub (custom app)
    specfact auth github --client-id YOUR_CLIENT_ID

    # Show authentication status
    specfact auth status

    # Clear stored tokens
    specfact auth clear [--provider azure-devops|github]
    ```

- **MODIFY**: Key Architectural Decisions
  - 1. **Separate implementations**: Azure uses `azure-identity` SDK; GitHub requires custom RFC 8628 implementation
  - 2. **File-based storage (Phase 1)**: Plaintext JSON storage for MVP. Encryption added Phase 2
  - 3. **Manual re-auth only (Phase 1)**: No token auto-refresh in MVP. Phase 2 adds background refresh
  - 4. **PAT fallback**: Users can still use `--pat` flag; existing workflows preserved
  - 5. **Provider detection**: Auto-detects configured provider; users can override with flags

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #111
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/111>
- **Last Synced Status**: proposed
- **Sanitized**: true
<!-- content_hash: bbe2b7cf74816250 -->