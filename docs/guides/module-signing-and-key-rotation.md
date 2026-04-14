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

# Verify after signing
hatch run python scripts/verify-modules-signature.py --require-signature --enforce-version-bump --version-check-base origin/dev
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

Checksum and version discipline without requiring signatures (same tool; omit the flag):

```bash
hatch run python scripts/verify-modules-signature.py --enforce-version-bump --payload-from-filesystem
```

Do not pass `--allow-unsigned` to `verify-modules-signature.py` — it is not a supported argument there.
Use `python scripts/sign-modules.py --allow-unsigned …` only when you intentionally want checksum-only
**signing** for local tests.

## Pre-commit (bundled modules in this repository)

If you use `pre-commit` or `scripts/setup-git-hooks.sh`, commits that stage changes under `modules/` or
`src/specfact_cli/modules/` run `scripts/pre-commit-verify-modules.sh`. That script adds
`--require-signature` only when the current branch is `main`; on other branches (including detached
`HEAD`) it runs checksum-only verification so commits do not require a local private key.

## CI Enforcement

`pr-orchestrator.yml` runs job `verify-module-signatures` with a **branch-aware** policy:

- PRs and pushes targeting **`main`**: `verify-modules-signature.py` is invoked **with**
  `--require-signature` (plus `--enforce-version-bump --payload-from-filesystem` and PR base comparison
  as configured in the workflow).
- PRs and pushes targeting **`dev`**: the same script runs **without** `--require-signature`
  (checksum-only), matching local feature-branch development.

The pipeline fails if checksums or version-bump rules are violated, or if `main`-targeting events lack
valid signatures when required.

## Rotation Procedure

1. Generate new keypair in secure environment.
2. Replace `resources/keys/module-signing-public.pem` with new public key.
3. Re-sign all official bundle manifests with the new private key.
4. Run verifier locally: `python scripts/verify-modules-signature.py --require-signature`.
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
