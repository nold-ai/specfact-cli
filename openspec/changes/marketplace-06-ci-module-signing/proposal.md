# Change: CI-Driven Module Signing On PR Approval

## Why

Module signing currently requires the private key to be available in the local environment, which
blocks non-interactive development (AI agents, Cursor, headless CI) on any branch where modules are
changed. The pre-commit hook and CI `verify-module-signatures` job both enforce `--require-signature`
regardless of branch, so every commit to a feature or dev branch silently hangs or fails when no key
is present. Moving signing to a CI step triggered by PR approval eliminates the local key requirement
while preserving the integrity guarantee where it matters: at the trust boundary before code reaches
`dev` or `main`.

## What Changes

- **NEW**: `sign-modules-on-approval.yml` GitHub Actions workflow — triggers on
  `pull_request_review` (state: `approved`), signs changed module manifests via CI secrets, and
  commits the signed manifests back to the PR branch.
- **MODIFY**: `scripts/pre-commit-smart-checks.sh` — branch-aware signature policy: non-`main`
  branches use `--allow-unsigned` (checksum-only); `main` branch retains `--require-signature`.
- **MODIFY**: `.github/workflows/pr-orchestrator.yml` `verify-module-signatures` job — drop
  `--require-signature` for PRs and pushes targeting `dev`; keep it for PRs and pushes targeting
  `main`.
- **MODIFY**: `.github/workflows/sign-modules.yml` `verify` job — scope `--require-signature` to
  `main` branch only; remove it from `dev` triggers.
- **NO CHANGE**: Module install-time verification (always `--require-signature` from main registry),
  `publish-modules.yml`, `create-release` signing step (kept as safety net), and
  `resources/keys/module-signing-public.pem`.

## Capabilities

### New Capabilities

- `ci-module-signing-on-approval`: Automated CI workflow that signs changed module manifests using
  repository secrets when a PR targeting `dev` or `main` is approved, committing signed manifests
  back to the PR branch without requiring any local key material.

### Modified Capabilities

- `ci-integration`: Pre-commit and CI verification gates now apply a branch-aware policy —
  `--allow-unsigned` (checksum-only) on non-`main` branches and in feature/dev PRs; full
  `--require-signature` enforcement only on `main`-targeting PRs and `main` branch pushes.

## Impact

- **Affected scripts**: `scripts/pre-commit-smart-checks.sh`
- **Affected workflows**: `.github/workflows/pr-orchestrator.yml`,
  `.github/workflows/sign-modules.yml`
- **New workflow**: `.github/workflows/sign-modules-on-approval.yml`
- **GitHub secrets used** (already configured): `SPECFACT_MODULE_PRIVATE_SIGN_KEY`,
  `SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE`
- **Permissions added**: `contents: write` on the new signing workflow (to push signed manifests
  back to the PR branch)
- **No Python source changes**: all modifications are to shell scripts and YAML workflows
- **No API surface changes**: module install-time verification behavior is unchanged for end users
- **Paired change**: `specfact-cli-modules/marketplace-06-ci-module-signing` — adds the private-key
  signing step that repo currently lacks (its PR orchestrator only verifies, never signs) using the
  same PR-approval trigger
- **Source Tracking**:
  - GitHub Issue: [#500](https://github.com/nold-ai/specfact-cli/issues/500)
  - Parent Feature: [#353 Marketplace Module Distribution](https://github.com/nold-ai/specfact-cli/issues/353)
  - Parent Epic: [#194 Architecture (CLI structure, modularity, performance)](https://github.com/nold-ai/specfact-cli/issues/194)
  - Paired Modules Change: [specfact-cli-modules#185](https://github.com/nold-ai/specfact-cli-modules/issues/185)
