---
layout: default
title: Module Security
permalink: /reference/module-security/
description: Trust model, checksum and signature verification, and integrity lifecycle for module packages.
---

# Module Security

Module packages can carry **publisher** and **integrity** metadata so that installation and registration verify artifact trust before enabling a module.

## Trust model

- **Manifest metadata**: `module-package.yaml` may include `publisher` (name, email, attributes) and `integrity` (checksum, optional signature).
- **Checksum verification**: Before registration or install, the system verifies the manifest (or artifact) checksum when `integrity.checksum` is present. Supported algorithms: `sha256`, `sha384`, `sha512` in `algo:hex` format.
- **Signature verification**: If `integrity.signature` is set and trusted key material is configured, signature verification validates provenance. Without key material, only checksum is enforced and a warning is logged.
- **Unsigned modules**: Modules without `integrity` metadata are allowed (backward compatible). Set `SPECFACT_ALLOW_UNSIGNED=1` to document explicit opt-in when using strict policies.

## Checksum flow

1. Discovery reads `module-package.yaml` and parses `integrity.checksum`.
2. At registration time, the installer hashes the manifest content and compares it to the expected checksum.
3. On mismatch, the module is skipped and a security warning is logged.
4. Other modules continue to register; one failing trust does not block the rest.

## Signing automation

- **Script**: `scripts/sign-module.sh <path-to-module-package.yaml>` outputs a `sha256:` checksum suitable for the manifest `integrity.checksum` field.
- **CI**: `.github/workflows/sign-modules.yml` can run on demand or on push to `main` when module manifests change, to produce or validate checksums.

## Versioned dependencies

Manifest may declare versioned module and pip dependencies via `module_dependencies_versioned` and `pip_dependencies_versioned` (each entry: `name`, `version_specifier`). These are parsed and stored for installation-time resolution while keeping legacy `module_dependencies` / `pip_dependencies` lists backward compatible.
