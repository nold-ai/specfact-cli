---
layout: default
title: Module Signing and Key Rotation
permalink: /guides/module-signing-and-key-rotation/
description: Runbook for signing official workflow bundles, placing public keys, rotating keys, and revoking compromised keys.
---

This runbook defines the repeatable process for signing official workflow bundles and verifying signatures in SpecFact CLI.

> Modules docs handoff: this page remains in the core docs set as release-line overview content.
> Canonical bundle-specific deep guidance now lives in the canonical modules docs site, currently
> published at `https://modules.specfact.io/`.

## Key Placement

Repository/public key path used by CLI verification:

- `resources/keys/module-signing-public.pem` (repository source path)

Runtime key resolution order:

1. Explicit key argument (internal verifier calls)
2. `SPECFACT_MODULE_PUBLIC_KEY_PEM`
3. Bundled key file at `resources/keys/module-signing-public.pem` (source) or `specfact_cli/resources/keys/module-signing-public.pem` (installed package)

Never store private signing keys in the repository.

## Generate Keys

Ed25519 (recommended):

```bash
openssl genpkey -algorithm ED25519 -out module-signing-private.pem
openssl pkey -in module-signing-private.pem -pubout -out module-signing-public.pem
```

RSA 4096 (supported):

```bash
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:4096 -out module-signing-private.pem
openssl pkey -in module-signing-private.pem -pubout -out module-signing-public.pem
```

## Sign Official Bundles

Preferred (strict, with private key):

- **Key file**: `--key-file <path>` or set `SPECFACT_MODULE_PRIVATE_SIGN_KEY_FILE` (or legacy `SPECFACT_MODULE_SIGNING_PRIVATE_KEY_FILE`).
- **Inline PEM**: Set `SPECFACT_MODULE_PRIVATE_SIGN_KEY` (or legacy `SPECFACT_MODULE_SIGNING_PRIVATE_KEY_PEM`) to the PEM string; no file needed. Useful in CI where the key is in a secret.

```bash
KEY_FILE="${SPECFACT_MODULE_PRIVATE_SIGN_KEY_FILE:-.specfact/sign-keys/module-signing-private.pem}"
python scripts/sign-modules.py --key-file "$KEY_FILE" src/specfact_cli/modules/*/module-package.yaml
python scripts/sign-modules.py --key-file "$KEY_FILE" packages/*/module-package.yaml
```

Encrypted private key options:

```bash
# Prompt interactively for passphrase (TTY)
python scripts/sign-modules.py --key-file "$KEY_FILE" packages/specfact-backlog/module-package.yaml

# Explicit passphrase flag (avoid shell history when possible)
python scripts/sign-modules.py --key-file "$KEY_FILE" --passphrase '***' packages/specfact-backlog/module-package.yaml

# Passphrase over stdin (CI-safe pattern)
  printf '%s' "$SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE" | \
  python scripts/sign-modules.py --key-file "$KEY_FILE" --passphrase-stdin packages/specfact-backlog/module-package.yaml
```

Versioning guard:

- The signer enforces module version increments for changed module contents.
- If module files changed and version is unchanged, signing fails until version is bumped.
- Override exists for exceptional local workflows: `--allow-same-version` (not recommended).
- Module versions are independent from CLI package version; bump only modules whose payload changed.

Changed-modules automation (recommended for release prep):

```bash
# Bump changed modules by patch and sign only those modules
hatch run python scripts/sign-modules.py \
  --key-file "$KEY_FILE" \
  --changed-only \
  --base-ref origin/dev \
  --bump-version patch

# Verify after signing (strict bundle; add --version-check-base when comparing to a branch)
hatch run verify-modules-signature --version-check-base origin/dev
```

Wrapper for single manifest:

```bash
bash scripts/sign-module.sh --key-file "$KEY_FILE" packages/specfact-backlog/module-package.yaml
# stdin passphrase:
printf '%s' "$SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE" | \
  bash scripts/sign-module.sh --key-file "$KEY_FILE" --passphrase-stdin packages/specfact-backlog/module-package.yaml
```

Local test-only unsigned mode:

```bash
python scripts/sign-modules.py --allow-unsigned packages/specfact-backlog/module-package.yaml
```

## Verify Signatures Locally

Strict verification (checksum + signature required):

```bash
python scripts/verify-modules-signature.py --require-signature
```

With explicit public key file:

```bash
python scripts/verify-modules-signature.py --require-signature --public-key-file resources/keys/module-signing-public.pem
```

PR / feature-branch parity with pre-commit omit (version bump vs base; defer checksum to CI):

```bash
hatch run verify-modules-signature-pr --version-check-base origin/dev
```

Development push-style checksum + version for the `dev` path (no `--require-signature`; matches
`VERIFY_MODULES_PUSH_ORCHESTRATOR`):

```bash
hatch run python scripts/verify-modules-signature.py --enforce-version-bump --payload-from-filesystem
```

Do not pass `--allow-unsigned` to `verify-modules-signature.py` — it is not a supported argument there.
Use `python scripts/sign-modules.py --allow-unsigned …` only when you intentionally want checksum-only
**signing** for local tests.

## Pre-commit (bundled modules in this repository)

If you use `pre-commit` or `scripts/setup-git-hooks.sh`, commits that stage changes under `modules/` or
`src/specfact_cli/modules/` run `scripts/pre-commit-verify-modules.sh`, which sources
`scripts/module-verify-policy.sh`. On **`main`** it runs **`VERIFY_MODULES_STRICT`** (checksum +
`--require-signature`); elsewhere it runs **`VERIFY_MODULES_PR`** (version bump only via
`--skip-checksum-verification`) so you are not forced to re-sign locally before CI.

## CI Enforcement

Canonical flag bundles live in **`scripts/module-verify-policy.sh`** and are sourced by:

- **`pr-orchestrator.yml`** job `verify-module-signatures`: pull requests targeting **`dev`** use
  **`VERIFY_MODULES_PR`** (same as pre-commit omit). Pull requests targeting **`main`** and pushes to
  **`main`** use **`VERIFY_MODULES_STRICT`** so unsigned or stale bundled manifests block before the
  release trust boundary. Pushes to **`dev`** use **`VERIFY_MODULES_PUSH_ORCHESTRATOR`** (payload
  checksum + version bump; no `--require-signature` in the `dev` push path).
- **`sign-modules.yml`** job `verify`: **push** to `dev` or `main` runs **`VERIFY_MODULES_STRICT`**
  after the auto-sign step. **Pull requests** and **`workflow_dispatch`** use **`VERIFY_MODULES_PR`**.

Strict signatures at the release boundary are enforced by **`pr-orchestrator.yml`**, **`sign-modules.yml`**,
and local **`main`** pre-commit.

## Rotation Procedure

1. Generate new keypair in secure environment.
2. Replace `resources/keys/module-signing-public.pem` with new public key.
3. Re-sign all official bundle manifests with the new private key.
4. Run verifier locally: `hatch run verify-modules-signature` (equivalent strict flags are in
   `scripts/module-verify-policy.sh` as `VERIFY_MODULES_STRICT`).
5. Commit public key + re-signed manifests in one change.
6. Merge to `dev`, then `main` after CI passes.

## Revocation Procedure

If a private key is compromised:

1. Treat all signatures from that key as untrusted.
2. Generate new keypair immediately.
3. Replace public key file in repo.
4. Re-sign all official bundles with new private key.
5. Merge emergency fix branch and invalidate prior release artifacts operationally.

Current limitation:

- Runtime key-revocation list support is not yet implemented.
- Revocation is currently handled by rotating the trusted public key and re-signing all bundled manifests.
