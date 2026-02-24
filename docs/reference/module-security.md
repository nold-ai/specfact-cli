---
layout: default
title: Module Security
permalink: /reference/module-security/
description: Trust model, checksum and signature verification, and integrity lifecycle for module packages.
---

# Module Security

Module packages carry **publisher** and **integrity** metadata so installation, bootstrap, and runtime discovery verify trust before enabling a module.

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
- **Verification command**:
  - `scripts/verify-modules-signature.py --require-signature --enforce-version-bump`
  - `--version-check-base <git-ref>` can be used in CI PR comparisons.

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
