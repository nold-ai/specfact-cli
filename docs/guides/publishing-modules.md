---
layout: default
title: Publishing Modules
permalink: /guides/publishing-modules/
description: Package and publish SpecFact modules to a registry (tarball, checksum, optional signing).
---

# Publishing modules

This guide describes how to package a SpecFact module for registry publishing: validate structure, create a tarball and checksum, optionally sign the manifest, and automate via CI.

## Module structure

Your module must have:

- A directory containing `module-package.yaml` (the manifest).
- Manifest fields: `name`, `version`, `commands` (required). For marketplace distribution, use `namespace/name` (e.g. `acme-corp/backlog-pro`) and optional `publisher`, `tier`.

Recommended layout:

```text
<module-dir>/
  module-package.yaml
  src/
    __init__.py
    commands.py   # or app.py, etc.
```

Exclude from the package: `.git`, `__pycache__`, `tests`, `.pytest_cache`, `*.pyc`, `*.pyo`.

## Script: publish-module.py

Use `scripts/publish-module.py` to validate, package, and optionally sign a module.

```bash
# Basic: create tarball and SHA-256 checksum
python scripts/publish-module.py path/to/module -o dist

# Write a registry index fragment (for merging into your registry index)
python scripts/publish-module.py path/to/module -o dist \
  --index-fragment dist/entry.yaml \
  --download-base-url https://registry.example.com/packages/

# Sign the manifest after packaging (requires key)
python scripts/publish-module.py path/to/module -o dist --sign
python scripts/publish-module.py path/to/module -o dist --sign --key-file /path/to/private.pem
```

Options:

- `module_path`: Path to the module directory or to `module-package.yaml`.
- `-o` / `--output-dir`: Directory for `<name>-<version>.tar.gz` and `<name>-<version>.tar.gz.sha256`.
- `--sign`: Run `scripts/sign-modules.py` on the manifest (uses `SPECFACT_MODULE_PRIVATE_SIGN_KEY` or `--key-file`).
- `--key-file`: Path to PEM private key when using `--sign`.
- `--index-fragment`: Write a single-module index entry (id, latest_version, download_url, checksum_sha256) to the given path.
- `--download-base-url`: Base URL for `download_url` in the index fragment.

Namespace and marketplace: If the manifest has `publisher` or `tier`, the script requires `name` in `namespace/name` form and validates format (`^[a-z][a-z0-9-]*/[a-z][a-z0-9-]+$`).

## Signing (optional)

For runtime verification, sign the manifest so the tarball includes integrity metadata:

- **Environment**: Set `SPECFACT_MODULE_PRIVATE_SIGN_KEY` (inline PEM) and `SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE` if the key is encrypted. Or use `--key-file` and optionally `--passphrase` / `--passphrase-stdin`.
- **Re-sign after changes**: Run `scripts/sign-modules.py` on the manifest (and bump version if content changed). See [Module signing and key rotation](module-signing-and-key-rotation.md).

## GitHub Actions workflow

Repository workflow `.github/workflows/publish-modules.yml`:

- **Triggers**: Push to tags matching `*-v*` (e.g. `backlog-v0.29.0`) or manual `workflow_dispatch` with input `module_path`.
- **Steps**: Checkout → resolve module path from tag → optional **Sign module manifest** (when secrets are set) → run `publish-module.py` → upload `dist/*.tar.gz` and `dist/*.sha256` as artifacts.

Optional signing in CI: Add repository secrets `SPECFACT_MODULE_PRIVATE_SIGN_KEY` and `SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE`. The workflow signs the manifest before packaging when the key secret is present.

## Best practices

- Bump module `version` in `module-package.yaml` whenever payload or manifest content changes; keep versions immutable for published artifacts.
- Use `namespace/name` for any module you publish to a registry.
- Run `scripts/verify-modules-signature.py --require-signature` (or your registry’s policy) before releasing.
- Prefer `--download-base-url` and `--index-fragment` when integrating with a custom registry index.

## See also

- [Module marketplace](module-marketplace.md) – Discovery, trust, and security.
- [Module signing and key rotation](module-signing-and-key-rotation.md) – Keys, signing, and verification.
- [Custom registries](custom-registries.md) – Adding and configuring registries for install/search.
