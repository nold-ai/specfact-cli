---
layout: default
title: Module Marketplace
permalink: /guides/module-marketplace/
description: Registry model, discovery priority, trust semantics, and security checks for SpecFact modules.
---

# Module Marketplace

SpecFact supports centralized marketplace distribution with local multi-source discovery.

## Registry Overview

- Registry repository: <https://github.com/nold-ai/specfact-cli-modules>
- Index document: `registry/index.json`
- Marketplace module id format: `namespace/name` (for example `specfact/backlog`)

## Discovery and Priority

Local module discovery scans these roots in priority order:

1. `built-in` modules (`src/specfact_cli/modules`)
2. `project` modules (`<repo>/.specfact/modules`)
3. `user` modules (`~/.specfact/modules`)
4. legacy/custom roots (`~/.specfact/marketplace-modules`, `~/.specfact/custom-modules`, `SPECFACT_MODULES_ROOTS`)

If module names collide, higher-priority sources win and lower-priority entries are shadowed.

## Trust vs Origin

SpecFact shows both trust semantics and origin details:

- `Trust` column (default): `official`, `community`, `local-dev`
- `Origin` column (`--show-origin`): `built-in`, `marketplace`, `custom`

Use:

```bash
specfact module list --show-origin
```

## Security Model

Install workflow enforces integrity and compatibility checks:

1. Fetch registry index
2. Download module archive
3. Validate SHA-256 checksum
4. Validate module `core_compatibility` against current CLI version
5. Install into selected scope root (`~/.specfact/modules` or `<repo>/.specfact/modules`)

Checksum mismatch blocks installation.

Additional local hardening:

- Denylist enforcement via `~/.specfact/module-denylist.txt` (or `SPECFACT_MODULE_DENYLIST_FILE`)
- One-time trust gate for non-official publishers (`--trust-non-official` for non-interactive automation)
- Bundled bootstrap/install verifies bundled integrity metadata before copy

Release signing automation:

- `scripts/sign-modules.py` updates manifest integrity metadata (checksum and optional signature)
- Use `KEY_FILE="${SPECFACT_MODULE_PRIVATE_SIGN_KEY_FILE:-.specfact/sign-keys/module-signing-private.pem}"` and run `python scripts/sign-modules.py --key-file "$KEY_FILE" <manifest...>` for local/manual signing
- Use changed-only automation to avoid re-signing all modules:
  - `hatch run python scripts/sign-modules.py --key-file "$KEY_FILE" --changed-only --base-ref origin/dev --bump-version patch`
  - this bumps/signs only changed modules and keeps module versioning decoupled from CLI package version
- Wrapper alternative: `bash scripts/sign-module.sh --key-file "$KEY_FILE" <manifest>`
- Without key material, the script fails by default and recommends `--key-file`; checksum-only mode is explicit via `--allow-unsigned` (local testing only)
- Encrypted keys are supported with passphrase via `--passphrase`, `--passphrase-stdin`, or `SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE`
- CI workflows inject private key material via `SPECFACT_MODULE_PRIVATE_SIGN_KEY` and passphrase via `SPECFACT_MODULE_PRIVATE_SIGN_KEY_PASSPHRASE`
- Private signing keys must stay in CI secrets and never in repository history

Public key for runtime verification:

- Preferred bundled location (repo source): `resources/keys/module-signing-public.pem`
- Installed package location: `specfact_cli/resources/keys/module-signing-public.pem`
- Runtime checks key in this order: explicit arg -> `SPECFACT_MODULE_PUBLIC_KEY_PEM` -> bundled key file

Scope boundary:

- This change set hardens local and bundled module safety.
- The online multi-registry ecosystem and production marketplace rollout remain tracked in `marketplace-02`.

## Marketplace vs Local Modules

- `specfact module install` supports source selection:
  - `--source auto` (default): bundled-first, then marketplace fallback
  - `--source bundled`: bundled sources only
  - `--source marketplace`: marketplace only
- If a requested module already exists locally (`built-in`/`custom`), install reports that no marketplace install is needed.
- `specfact module uninstall` supports `--scope user|project` and prevents ambiguous removals when same module id exists in both scopes.

## Module Introspection

`specfact module show <name>` includes:

- Module metadata (publisher, license, trust, origin, compatibility)
- Full command tree, including subcommands
- Short command descriptions derived from Typer command registration
