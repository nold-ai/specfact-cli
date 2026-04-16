---
layout: default
title: Module Security
permalink: /reference/module-security/
description: Trust model, checksum and signature verification, and integrity lifecycle for module packages.
---

Module packages carry **publisher** and **integrity** metadata so installation, bootstrap, and runtime discovery verify trust before enabling a module.

> Modules docs handoff: this page remains in the core docs set as release-line overview content.
> Canonical bundle-specific deep guidance now lives in the canonical modules docs site, currently
> published at `https://modules.specfact.io/`.

## Trust model

- **Manifest metadata**: `module-package.yaml` may include `publisher` (name, email, attributes) and `integrity` (checksum, optional signature).
- **Checksum verification**: Verification computes a deterministic hash of the full module payload (all module files, with manifest canonicalization that excludes `integrity` itself). Supported algorithms: `sha256`, `sha384`, `sha512` in `algo:hex` format.
- **Signature verification**: If `integrity.signature` is present and a public key is configured, signature validation proves provenance over the same full payload.
- **Publisher trust gate**: Non-official publishers require one-time explicit trust (interactive confirmation or `--trust-non-official` / `SPECFACT_TRUST_NON_OFFICIAL`).
- **Denylist gate**: Modules listed in denylist are blocked before install/bootstrap regardless of source.

## Integrity flow

1. Discovery reads `module-package.yaml` and parses `integrity.checksum`.
2. At install/bootstrap/verification time, the tool hashes the full module payload and compares it to `integrity.checksum`.
3. On mismatch, the module is skipped and a security warning is logged.
4. Other modules continue to register; one failing trust does not block the rest.

## Signing automation

- **Script**: `scripts/sign-module.sh` signs one or more `module-package.yaml` manifests.
- **Payload scope**: Signing covers all files under the module directory (not only the manifest).
- **Encrypted key support**: Passphrase can be provided with:
  - `--passphrase` (local only; avoid shell history in CI)
  - `--passphrase-stdin` (recommended for secure piping)
  - `SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE`
- **Key sources**:
  - `--key-file`
  - `SPECFACT_MODULE_PRIVATE_SIGN_KEY` (PEM content)
  - `SPECFACT_MODULE_PRIVATE_SIGN_KEY_FILE`
- **Version guard**: Changed module contents must have a bumped module version before signing. Override exists only for controlled local cases via `--allow-same-version`.
- **Changed-only release mode**: `scripts/sign-modules.py --changed-only --base-ref <git-ref> --bump-version <patch|minor|major>` auto-selects modules with payload changes, bumps versions when unchanged, and signs only those modules.
- **Version decoupling**: module versions are semver-managed per module payload and do not need to track CLI package version.
- **CI secrets**:
  - `SPECFACT_MODULE_PRIVATE_SIGN_KEY`
  - `SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE`
- **Verification command** (`verify-modules-signature.py`): canonical flag bundles live in
  **`scripts/module-verify-policy.sh`** (`VERIFY_MODULES_STRICT`, `VERIFY_MODULES_PR`,
  `VERIFY_MODULES_PUSH_ORCHESTRATOR`).
  - **Strict** (`VERIFY_MODULES_STRICT`): `--require-signature --enforce-version-bump --payload-from-filesystem`
    — local **`main`** pre-commit, **`sign-modules.yml`** verify on **push** to `dev`/`main` (after auto-sign).
  - **PR / feature relaxed** (`VERIFY_MODULES_PR`): `--enforce-version-bump --skip-checksum-verification`
    — pre-commit on non-`main`, **`pr-orchestrator.yml`** verify job on **pull_request**, **`sign-modules.yml`**
    verify on **pull_request** / **workflow_dispatch** (version discipline vs base; checksum refresh in CI).
  - **Orchestrator push** (`VERIFY_MODULES_PUSH_ORCHESTRATOR`): `--enforce-version-bump --payload-from-filesystem`
    — **`pr-orchestrator.yml`** verify job on **push** to `dev`/`main` (payload checksum + version; no
    `--require-signature` in that job).
  - **Approval-time signing** (`sign-modules-on-approval.yml`): on **approved** reviews for same-repo PRs
    targeting **`dev` or `main`**, CI runs `pull_request.base.sha`’s **`scripts/sign-modules.py`**
    (trusted revision) against the **PR head** working tree, then pushes updated `module-package.yaml`
    files to the PR branch — branch content cannot replace the signer before secrets are used. Fork PRs
    are skipped (no push permission). **`pull_request_review` uses the workflow definition from the repo’s
    default branch** (often `main`); until this file exists on `main`, use **Actions → Sign modules on PR
    approval → Run workflow**, select **`dev`** (or your branch), and pick **`base_branch`** / **`version_bump`**
    — that run uses the workflow file from the branch you choose and signs with **`MERGE_BASE`** vs
    `origin/<base_branch>` like the manual path above. If the workflow or secrets are unavailable, sign
    bundled manifests before merging into `main` or the post-merge push verify job will still fail.
  - **Manual signing** (`sign-modules.yml` → **Run workflow**): choose the branch to update, then pick
    **base branch** (`dev` or `main` — the workflow fetches `origin/<branch>`). The **verify** step passes
    `--version-check-base origin/<branch>` so `workflow_dispatch` is not stuck on `HEAD~1` before the
    repair job runs. For **`--changed-only`** signing (default), the **sign** step sets
    `MERGE_BASE="$(git merge-base HEAD "origin/<branch>")"` and runs
    `scripts/sign-modules.py --changed-only --base-ref "$MERGE_BASE"` so change detection uses the
    **merge-base** commit between your branch and that remote branch, not the moving tip of
    `origin/<branch>` alone. Locally you can mirror that with
    `MERGE_BASE=$(git merge-base HEAD origin/main)` (or `origin/dev`) then
    `python scripts/sign-modules.py --changed-only --base-ref "$MERGE_BASE" --bump-version patch --payload-from-filesystem`.
    Enable **resign all manifests** when trees match the base but signatures are still missing (unsigned
    file identical on both sides).
    **Reproducibility** (re-sign, assert no diff) runs on **push to `main` only** (not `dev`, not
    `pull_request`).
  - There is **no** `--allow-unsigned` on this verifier; that flag exists on **`sign-modules.py`**
    for explicit test-only signing without a key.
- **Pre-commit** (this repo): when staged paths exist under `modules/` or `src/specfact_cli/modules/`,
  `scripts/pre-commit-verify-modules.sh` sources **`module-verify-policy.sh`** and chooses
  **`VERIFY_MODULES_STRICT`** on **`main`** or **`VERIFY_MODULES_PR`** elsewhere (see
  `scripts/git-branch-module-signature-flag.sh`).

## Public key and key rotation

- Store trusted public key in:
  - `resources/keys/module-signing-public.pem`
- Optional fallback path:
  - `src/specfact_cli/resources/keys/module-signing-public.pem`
- Rotate keys by:
  1. generating a new key pair,
  2. updating trusted public key in repository,
  3. re-signing affected modules with incremented versions,
  4. running signature verification and version-bump checks in CI.

## Versioned dependencies

Manifest may declare versioned module and pip dependencies via `module_dependencies_versioned` and `pip_dependencies_versioned` (each entry: `name`, `version_specifier`). These are parsed and stored for installation-time resolution while keeping legacy `module_dependencies` / `pip_dependencies` lists backward compatible.
