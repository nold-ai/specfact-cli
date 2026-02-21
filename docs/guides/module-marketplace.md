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
2. `marketplace` modules (`~/.specfact/marketplace-modules`)
3. `custom` modules (`~/.specfact/custom-modules`)
4. extra custom roots (workspace `modules/` and `SPECFACT_MODULES_ROOTS`)

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
5. Install into `~/.specfact/marketplace-modules/`

Checksum mismatch blocks installation.

## Marketplace vs Local Modules

- `specfact module install` targets marketplace modules.
- If a requested module already exists locally (`built-in`/`custom`), install reports that no marketplace install is needed.
- `specfact module uninstall` removes only marketplace-installed modules and provides actionable guidance for built-in/custom modules.

## Module Introspection

`specfact module show <name>` includes:

- Module metadata (publisher, license, trust, origin, compatibility)
- Full command tree, including subcommands
- Short command descriptions derived from Typer command registration
