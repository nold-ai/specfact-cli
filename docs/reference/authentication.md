---
layout: default
title: Authentication
permalink: /reference/authentication/
---

# Authentication

SpecFact CLI supports device code authentication flows for GitHub and Azure DevOps to keep credentials out of scripts and CI logs.
When the backlog bundle is installed, authentication commands are available under `specfact backlog auth`.

## Quick Start

### GitHub (Device Code)

```bash
specfact backlog auth github
```

Use a custom OAuth client or GitHub Enterprise host:

```bash
specfact backlog auth github --client-id YOUR_CLIENT_ID
specfact backlog auth github --base-url https://github.example.com
```

**Note:** The default client ID ships with the CLI and is only valid for `https://github.com`. For GitHub Enterprise, you must supply your own client ID via `--client-id` or `SPECFACT_GITHUB_CLIENT_ID`.

### Azure DevOps (Device Code)

```bash
specfact backlog auth azure-devops
```

**Note:** OAuth tokens expire after approximately 1 hour. For longer-lived authentication, use a Personal Access Token (PAT) with up to 1 year expiration:

```bash
# Store PAT token (recommended for automation)
specfact backlog auth azure-devops --pat your_pat_token
```

### Azure DevOps Token Resolution Priority

When using Azure DevOps commands (e.g., `specfact backlog refine ado`, `specfact backlog map-fields`), tokens are resolved in this priority order:

1. **Explicit token parameter**: `--ado-token` CLI flag
2. **Environment variable**: `AZURE_DEVOPS_TOKEN`
3. **Stored token**: Token stored via `specfact backlog auth azure-devops` (checked automatically)
4. **Expired stored token**: If stored token is expired, a warning is shown with options to refresh

**Example:**

```bash
# Uses stored token automatically (no need to specify)
specfact backlog refine ado --ado-org myorg --ado-project myproject

# Override with explicit token
specfact backlog refine ado --ado-org myorg --ado-project myproject --ado-token your_token

# Use environment variable
export AZURE_DEVOPS_TOKEN=your_token
specfact backlog refine ado --ado-org myorg --ado-project myproject
```

**Token Types:**

- **OAuth Tokens**: Device code flow, expire after ~1 hour, automatically refreshed when possible
- **PAT Tokens**: Personal Access Tokens, can last up to 1 year, recommended for automation and CI/CD

## Check Status

```bash
specfact backlog auth status
```

## Clear Stored Tokens

```bash
# Clear one provider
specfact backlog auth clear --provider github

# Clear all providers
specfact backlog auth clear
```

## Token Storage

Tokens are stored locally in:

```
~/.specfact/tokens.json
```

On POSIX systems, SpecFact CLI sets restrictive permissions on the token directory and file.

## Adapter Token Precedence

Adapters resolve tokens in this order:

- Explicit token parameter (CLI flag or code)
- Environment variable (e.g., `GITHUB_TOKEN`, `AZURE_DEVOPS_TOKEN`)
- Stored auth token (`specfact backlog auth ...`)
- GitHub CLI (`gh auth token`) for GitHub if enabled

**Azure DevOps Specific:**

For Azure DevOps commands, stored tokens are automatically used by:
- `specfact backlog refine ado` - Automatically uses stored token if available
- `specfact backlog map-fields` - Automatically uses stored token if available

If a stored token is expired, you'll see a warning with options to:
1. Use a PAT token (recommended for longer expiration)
2. Re-authenticate via `specfact backlog auth azure-devops`
3. Use `--ado-token` option with a valid token

## Troubleshooting

### Token Resolution Issues

**Problem**: "Azure DevOps token required" error even after running `specfact backlog auth azure-devops`

**Solutions:**

1. **Check token expiration**: OAuth tokens expire after ~1 hour. Use a PAT token for longer expiration:
   ```bash
   specfact backlog auth azure-devops --pat your_pat_token
   ```

2. **Use explicit token**: Override with `--ado-token` flag:
   ```bash
   specfact backlog refine ado --ado-org myorg --ado-project myproject --ado-token your_token
   ```

3. **Set environment variable**: Use `AZURE_DEVOPS_TOKEN` environment variable:
   ```bash
   export AZURE_DEVOPS_TOKEN=your_token
   specfact backlog refine ado --ado-org myorg --ado-project myproject
   ```

4. **Re-authenticate**: Clear and re-authenticate:
   ```bash
   specfact backlog auth clear --provider azure-devops
   specfact backlog auth azure-devops
   ```

For full adapter configuration details, see:

- [GitHub Adapter](../adapters/github.md)
- [Azure DevOps Adapter](../adapters/azuredevops.md)
