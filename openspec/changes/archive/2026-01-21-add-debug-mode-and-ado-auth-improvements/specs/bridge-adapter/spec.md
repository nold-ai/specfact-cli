# Bridge Adapter Capability - Spec Delta

## MODIFIED Requirements

### Requirement: Azure DevOps Backlog Adapter

The Azure DevOps adapter SHALL use centralized authentication helper methods and SHALL support automatic token refresh. All ADO API requests SHALL use `_auth_headers()` helper method for consistent authentication. The ADO adapter SHALL attempt automatic token refresh when OAuth tokens expire. The ADO adapter SHALL support both PAT (Basic auth) and OAuth (Bearer auth) tokens. Error messages SHALL provide helpful guidance for authentication issues.

The ADO adapter SHALL ensure organization is always included before project in API URL paths for project-based permissions. URL construction SHALL always include `{org}/{project}` in path before `_apis/` endpoint. This ensures project-based permissions work correctly in larger organizations. This requirement SHALL apply to both cloud (Azure DevOps Services) and on-premise (Azure DevOps Server) configurations.

#### Scenario: Consistent Authentication Headers

**Given** an ADO adapter instance with a valid API token  
**When** the adapter makes any API request (WIQL query, work items batch GET, work item PATCH)  
**Then** the Authorization header must be constructed using `_auth_headers()` helper method  
**And** PAT tokens must be base64-encoded for Basic authentication  
**And** OAuth tokens must use Bearer authentication

#### Scenario: Automatic Token Refresh

**Given** an ADO adapter with an expired OAuth token stored  
**When** the adapter attempts to use the expired token  
**Then** the adapter must attempt to refresh the token using persistent token cache  
**And** if refresh succeeds, the adapter must update the stored token  
**And** if refresh fails, the adapter must provide helpful error messages with guidance

#### Scenario: PAT Token Support

**Given** an ADO adapter initialized with a PAT token (via `--pat` option or environment variable)  
**When** the adapter makes API requests  
**Then** the adapter must use Basic authentication with base64-encoded PAT  
**And** the adapter must not track PAT expiration (expiration managed by Azure DevOps)

#### Scenario: Project-Based Permissions URL Format

**Given** an ADO adapter configured with org and project  
**When** the adapter constructs API URLs  
**Then** the URL must follow format: `{base_url}/{org}/{project}/_apis/...`  
**And** org must always appear before project in the URL path  
**And** this applies even when collection is already in base_url (on-premise)

**Example URLs**:
- Cloud: `https://dev.azure.com/myorg/myproject/_apis/wit/wiql?api-version=7.1`
- On-premise: `https://server/myorg/myproject/_apis/wit/wiql?api-version=7.1`

## ADDED Requirements

### Requirement: Token Refresh with Persistent Cache

The ADO adapter SHALL support automatic OAuth token refresh using persistent token cache, similar to Azure CLI behavior. OAuth tokens expire after ~1 hour, and automatic refresh using persistent cache allows seamless operation without frequent re-authentication, improving user experience.

#### Scenario: Automatic Token Refresh on Expiration

**Given** an ADO adapter with an expired OAuth token  
**And** a valid refresh token exists in persistent cache  
**When** the adapter detects the token is expired  
**Then** the adapter must automatically refresh the token using the cached refresh token  
**And** the adapter must update the stored access token  
**And** the operation must continue without user interaction  
**And** debug output should indicate token refresh occurred

#### Scenario: Token Refresh Failure Handling

**Given** an ADO adapter with an expired OAuth token  
**And** no valid refresh token exists in persistent cache (or refresh token expired)  
**When** the adapter attempts to refresh the token  
**Then** the adapter must provide helpful error messages  
**And** the error message must suggest using PAT for longer-lived tokens  
**And** the error message must suggest re-authentication via `specfact auth azure-devops`
