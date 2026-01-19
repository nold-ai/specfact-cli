---
layout: default
title: Authentication
permalink: /reference/authentication/
---

# Authentication

SpecFact CLI supports device code authentication flows for GitHub and Azure DevOps to keep credentials out of scripts and CI logs.

## Quick Start

### GitHub (Device Code)

```bash
specfact auth github
```

Use a custom OAuth client or GitHub Enterprise host:

```bash
specfact auth github --client-id YOUR_CLIENT_ID
specfact auth github --base-url https://github.example.com
```

**Note:** The default client ID ships with the CLI and is only valid for `https://github.com`. For GitHub Enterprise, you must supply your own client ID via `--client-id` or `SPECFACT_GITHUB_CLIENT_ID`.

### Azure DevOps (Device Code)

```bash
specfact auth azure-devops
```

## Check Status

```bash
specfact auth status
```

## Clear Stored Tokens

```bash
# Clear one provider
specfact auth clear --provider github

# Clear all providers
specfact auth clear
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
- Stored auth token (`specfact auth ...`)
- GitHub CLI (`gh auth token`) for GitHub if enabled

For full adapter configuration details, see:

- [GitHub Adapter](../adapters/github.md)
- [Azure DevOps Adapter](../adapters/azuredevops.md)
