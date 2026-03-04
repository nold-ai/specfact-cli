# Change: Backlog auth commands (specfact backlog auth)

## Why


Module-migration-03 removes the auth module from core and keeps only a central auth interface (token storage by provider_id). Auth for DevOps providers (GitHub, Azure DevOps) belongs with the backlog domain: users who install the backlog bundle need `specfact backlog auth azure-devops` and `specfact backlog auth github`, not a global `specfact auth`. This change implements those commands in the specfact-cli-modules backlog bundle so that after migration-03, backlog users get auth under `specfact backlog auth`.

## What Changes


- **specfact-cli-modules (backlog bundle)**: Add a `backlog auth` subgroup to the backlog Typer app with subcommands:
  - `specfact backlog auth azure-devops` (options: `--pat`, `--use-device-code`; same behaviour as former `specfact auth azure-devops`)
  - `specfact backlog auth github` (device code flow; same as former `specfact auth github`)
  - `specfact backlog auth status` — show stored tokens for github / azure-devops
  - `specfact backlog auth clear` — clear stored tokens (optionally by provider)
- **Implementation**: Auth command implementations use the **central auth interface** from specfact-cli core (`specfact_cli.utils.auth_tokens`: `get_token`, `set_token`, `clear_token`, `clear_all_tokens`) to store and retrieve tokens. No duplicate token storage logic; the backlog bundle depends on specfact-cli and calls the same interface that adapters (GitHub, Azure DevOps) in the bundle use.
- **specfact-cli**: No code changes in this repo; migration-03 already provides the central auth interface and removes the auth module.

## Capabilities
- `backlog-auth-commands`: When the specfact-backlog bundle is installed, the CLI exposes `specfact backlog auth` with subcommands azure-devops, github, status, clear. Each subcommand uses the core auth interface for persistence. Existing tokens stored by a previous `specfact auth` (pre–migration-03) continue to work because the storage path and provider_ids are unchanged.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #340
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/340>
- **Last Synced Status**: proposed
- **Sanitized**: false
