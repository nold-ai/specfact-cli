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
- **Verification command** (`verify-modules-signature.py`):
  - **Strict** (signatures required): `--require-signature --enforce-version-bump` (and optional
    `--payload-from-filesystem`, `--version-check-base <git-ref>` in CI).
  - **Checksum-only** (default when `--require-signature` is omitted): still enforces payload
    checksums and, with `--enforce-version-bump`, version discipline — useful on feature branches and
    for dev-targeting CI without local signing keys.
  - **GitHub Actions** (`pr-orchestrator.yml`, `sign-modules.yml`): pull-request jobs use
    checksum-only verification (no `--require-signature`) so unsigned manifests can be reviewed before
    merge; **pushes to `main`** run strict verification with `--require-signature`.
  - **Approval-time signing** (`sign-modules-on-approval.yml`): on **approved** reviews for same-repo PRs
    targeting **`dev` or `main`**, CI runs `scripts/sign-modules.py --changed-only` with repository secrets
    (`SPECFACT_MODULE_PRIVATE_SIGN_KEY`, optional passphrase) and pushes updated `module-package.yaml`
    files to the PR branch. That removes the need for a local signing key for routine agent/Copilot flows
    as long as secrets are configured; fork PRs are skipped (push permission). If the workflow or
    secrets are unavailable, sign bundled manifests before merging into `main` or the post-merge push
    verify job will still fail.
  - **Manual signing** (`sign-modules.yml` → **Run workflow**): choose the branch to update, then pick
    **comparison base** (`dev` or `main`, i.e. `origin/<branch>` for `--changed-only`) and **version bump**
    (`patch` / `minor` / `major`). The job runs the same verifier as other events (on `main`, strict
    `--require-signature` is skipped only for `workflow_dispatch` so you can recover unsigned `main`),
    then signs changed modules, commits, and pushes to that branch. Reproducibility assert is skipped
    on manual runs because signing replaces that check.
  - There is **no** `--allow-unsigned` on this verifier; that flag exists on **`sign-modules.py`**
    for explicit test-only signing without a key.
- **Pre-commit** (this repo): when staged paths exist under `modules/` or `src/specfact_cli/modules/`,
  `scripts/pre-commit-verify-modules.sh` runs the verifier with `--enforce-version-bump` and
  `--payload-from-filesystem`, adding `--require-signature` only on `main` (see
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
