# Change: CI-Driven Module Signing On PR Approval

## Why

Module signing requires the private key for strict verification. Non-`main` development must not be
blocked by stale checksums or missing signatures before CI re-signs. Canonical verify flag bundles live
in **`scripts/module-verify-policy.sh`** and are shared by pre-commit, **`pr-orchestrator.yml`**, and
**`sign-modules.yml`** so local hooks and GitHub Actions stay aligned. Approval-time signing still
closes the loop on same-repo PRs without fork push access.

## What Changes

- **NEW**: `sign-modules-on-approval.yml` GitHub Actions workflow — triggers on
  `pull_request_review` (state: `approved`), signs changed module manifests via CI secrets, and
  commits the signed manifests back to the PR branch.
- **MODIFY**: Pre-commit module verify — branch-aware policy via `scripts/pre-commit-verify-modules.sh`,
  `scripts/git-branch-module-signature-flag.sh`, and **`scripts/module-verify-policy.sh`**: `main` uses
  **`VERIFY_MODULES_STRICT`**; elsewhere **`VERIFY_MODULES_PR`**. The verifier has **no** `--allow-unsigned`
  flag (that option exists on **`sign-modules.py`** for local test signing only).
  `scripts/pre-commit-smart-checks.sh` remains a repo-root shim into `pre-commit-quality-checks.sh`
  (see modular `.pre-commit-config.yaml`).
- **MODIFY**: `.github/workflows/pr-orchestrator.yml` `verify-module-signatures` job — source
  **`module-verify-policy.sh`**; **pull_request** uses **`VERIFY_MODULES_PR`**; **push** uses
  **`VERIFY_MODULES_PUSH_ORCHESTRATOR`** (this job never passes `--require-signature`).
- **MODIFY**: `.github/workflows/sign-modules.yml` `verify` job — source **`module-verify-policy.sh`**;
  **push** to `dev`/`main` uses **`VERIFY_MODULES_STRICT`** after auto-sign; **pull_request** /
  **workflow_dispatch** uses **`VERIFY_MODULES_PR`**.
- **NO CHANGE**: Module install-time verification (always `--require-signature` from main registry),
  `publish-modules.yml`, `create-release` signing step (kept as safety net), and
  `resources/keys/module-signing-public.pem`.

## Capabilities

### New Capabilities

- `ci-module-signing-on-approval`: Automated CI workflow that signs changed module manifests using
  repository secrets when a PR targeting `dev` or `main` is approved, committing signed manifests
  back to the PR branch without requiring any local key material.

### Modified Capabilities

- `ci-integration`: Pre-commit and CI verification gates consume **`scripts/module-verify-policy.sh`**
  (`VERIFY_MODULES_STRICT`, `VERIFY_MODULES_PR`, `VERIFY_MODULES_PUSH_ORCHESTRATOR`) so hooks and
  workflows cannot drift.

## Impact

- **Affected scripts**: `scripts/module-verify-policy.sh`, `scripts/pre-commit-verify-modules.sh`,
  `scripts/git-branch-module-signature-flag.sh`, `scripts/pre-commit-quality-checks.sh`,
  `scripts/pre-commit-smart-checks.sh` (shim)
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
