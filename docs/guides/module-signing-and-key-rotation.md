---
layout: default
title: Module Signing and Key Rotation
permalink: /guides/module-signing-and-key-rotation/
description: Runbook for signing bundled modules, placing public keys, rotating keys, and revoking compromised keys.
---

# Module Signing and Key Rotation

This runbook defines the repeatable process for signing bundled modules and verifying signatures in SpecFact CLI.

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

## Sign Bundled Modules

Preferred (strict, with private key):

```bash
python scripts/sign-modules.py --key-file /secure/path/module-signing-private.pem src/specfact_cli/modules/*/module-package.yaml
python scripts/sign-modules.py --key-file /secure/path/module-signing-private.pem modules/*/module-package.yaml
```

Encrypted private key options:

```bash
# Prompt interactively for passphrase (TTY)
python scripts/sign-modules.py --key-file /secure/path/module-signing-private.pem modules/backlog-core/module-package.yaml

# Explicit passphrase flag (avoid shell history when possible)
python scripts/sign-modules.py --key-file /secure/path/module-signing-private.pem --passphrase '***' modules/backlog-core/module-package.yaml

# Passphrase over stdin (CI-safe pattern)
printf '%s' "$SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE" | \
  python scripts/sign-modules.py --key-file /secure/path/module-signing-private.pem --passphrase-stdin modules/backlog-core/module-package.yaml
```

Versioning guard:

- The signer enforces module version increments for changed module contents.
- If module files changed and version is unchanged, signing fails until version is bumped.
- Override exists for exceptional local workflows: `--allow-same-version` (not recommended).

Wrapper for single manifest:

```bash
bash scripts/sign-module.sh --key-file /secure/path/module-signing-private.pem modules/backlog-core/module-package.yaml
# stdin passphrase:
printf '%s' "$SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE" | \
  bash scripts/sign-module.sh --key-file /secure/path/module-signing-private.pem --passphrase-stdin modules/backlog-core/module-package.yaml
```

Local test-only unsigned mode:

```bash
python scripts/sign-modules.py --allow-unsigned modules/backlog-core/module-package.yaml
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

## CI Enforcement

`pr-orchestrator.yml` contains a strict gate:

- Job: `verify-module-signatures`
- Command: `python scripts/verify-modules-signature.py --require-signature`

This runs on PR/push for `dev` and `main` and fails the pipeline if module signatures/checksums are missing or stale.

## Rotation Procedure

1. Generate new keypair in secure environment.
2. Replace `resources/keys/module-signing-public.pem` with new public key.
3. Re-sign all bundled module manifests with the new private key.
4. Run verifier locally: `python scripts/verify-modules-signature.py --require-signature`.
5. Commit public key + re-signed manifests in one change.
6. Merge to `dev`, then `main` after CI passes.

## Revocation Procedure

If a private key is compromised:

1. Treat all signatures from that key as untrusted.
2. Generate new keypair immediately.
3. Replace public key file in repo.
4. Re-sign all bundled modules with new private key.
5. Merge emergency fix branch and invalidate prior release artifacts operationally.

Current limitation:

- Runtime key-revocation list support is not yet implemented.
- Revocation is currently handled by rotating the trusted public key and re-signing all bundled manifests.
