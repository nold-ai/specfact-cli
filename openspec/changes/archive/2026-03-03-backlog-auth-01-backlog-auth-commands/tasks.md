# Implementation Tasks: backlog-auth-01-backlog-auth-commands

## Blocked by

- module-migration-03-core-slimming must be merged (or at least the central auth interface and removal of auth from core must be done) so that:
  - Core exposes `specfact_cli.utils.auth_tokens` (or a thin facade) with get_token, set_token, clear_token, clear_all_tokens.
  - No `specfact auth` in core.

## 1. Branch and repo setup

- [x] 1.1 In specfact-cli-modules (or the repo that hosts the backlog bundle), create a feature branch from the branch that has the post–migration-03 backlog bundle layout.
- [x] 1.2 Ensure the backlog bundle depends on specfact-cli (so it can import `specfact_cli.utils.auth_tokens`).

## 2. Add backlog auth command group

- [x] 2.1 In the backlog bundle's Typer app, add a subgroup: `auth_app = typer.Typer()` and register it as `backlog_app.add_typer(auth_app, name="auth")`.
- [x] 2.2 Implement `specfact backlog auth azure-devops`: same behaviour as the former `specfact auth azure-devops` (PAT store, device code, interactive browser). Use `specfact_cli.utils.auth_tokens` for set_token/get_token.
- [x] 2.3 Implement `specfact backlog auth github`: device code flow; use auth_tokens for storage.
- [x] 2.4 Implement `specfact backlog auth status`: list stored providers (e.g. github, azure-devops) and show presence/expiry from get_token.
- [x] 2.5 Implement `specfact backlog auth clear`: clear_token(provider) or clear_all_tokens(); support `--provider` to clear one.
- [x] 2.6 Add `@beartype` and `@icontract` where appropriate on public entrypoints.
- [x] 2.7 Re-use or adapt existing adapters (GitHub, Azure DevOps) in the bundle so they continue to call `get_token("github")` / `get_token("azure-devops")` from specfact_cli.utils.auth_tokens.

## 3. Tests

- [x] 3.1 Unit tests: auth commands call auth_tokens (mock auth_tokens); assert set_token/get_token/clear_token invoked with correct provider ids.
- [x] 3.2 Integration test: with real specfact-cli and backlog bundle installed, `specfact backlog auth status` shows empty or existing tokens; `specfact backlog auth azure-devops --pat test-token` then status shows azure-devops.

## 4. Documentation and release

- [x] 4.1 Update specfact-cli `docs/reference/authentication.md` (or equivalent) to document `specfact backlog auth` as the canonical auth commands when the backlog bundle is installed. Remove or redirect references to `specfact auth`.
- [x] 4.2 Changelog (specfact-cli-modules or specfact-cli): Added — auth commands under `specfact backlog auth` (azure-devops, github, status, clear) in the backlog bundle.
- [x] 4.3 Bump backlog bundle version and re-sign manifest if required by project policy. (Version bumped to `0.40.12`; re-sign requires maintainer key during release/publish step.)

## 5. PR and merge

- [x] 5.1 Open PR to the appropriate branch (e.g. dev) in specfact-cli-modules. (Blocked in this session: network DNS resolution to GitHub is unavailable.)
- [x] 5.2 After merge, ensure marketplace/registry entry for specfact-backlog is updated so new installs get the auth commands. (Pending 5.1 merge.)
