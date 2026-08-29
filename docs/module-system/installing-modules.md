---
layout: default
title: Installing Modules
permalink: /module-system/installing-modules/
redirect_from:
  - /guides/installing-modules/
description: Install, list, show, enable, disable, uninstall, and upgrade SpecFact modules.
keywords: [install modules, module command, marketplace, registries]
audience: [solo, team, enterprise]
expertise_level: [beginner, intermediate]
---

Use the `specfact module` command group to manage marketplace and locally discovered modules.
Use plain `specfact ...` commands in this guide (not `hatch run specfact ...`) so steps work across pipx, pip, uv tool installs, and packaged runtimes.

## Install Behavior

```bash
# Marketplace id format
specfact module install nold-ai/specfact-backlog

# Bare names are accepted and resolved through the configured source policy
specfact module install backlog

# Install into project scope instead of user scope
specfact module install backlog --scope project --repo /path/to/repo

# Force bundled-only or marketplace-only source resolution
specfact module install backlog --source bundled
specfact module install backlog --source marketplace
specfact module install backlog --source marketplace --trust-non-official

# Install a specific version
specfact module install nold-ai/specfact-backlog --version 0.40.0
```

Notes:

- Install defaults to user scope (`~/.specfact/modules`); use `--scope project` for `<repo>/.specfact/modules`.
- Install source defaults to `auto` (bundled first, then marketplace fallback).
- Use `--source bundled` or `--source marketplace` for explicit source selection.
- Use `--trust-non-official` when running non-interactive installs for community/non-official publishers.
- If a module is already available locally (`built-in`, project, user, or `custom`), install is skipped with a clear message.
- If the requested module is already installed but disabled in `modules.json`, install repairs the lifecycle state by enabling the manifest module id and reports that action.
- Missing command guidance distinguishes truly absent modules from installed-but-disabled or installed-but-skipped modules and suggests the matching recovery command.
- Invalid ids show an explicit error (`name` or `namespace/name` only).
- Use `specfact module doctor [module-id]` to inspect the effective module copy, shadowed duplicates, and configured development source roots.

## Dependency resolution

Before installing a marketplace module, SpecFact resolves its dependencies (other modules and optional pip packages) from manifest `pip_dependencies`, `module_dependencies`, and versioned bundle dependency declarations. If conflicts are detected (e.g. incompatible versions), install fails unless you override.

```bash
# Install with dependency resolution (default)
specfact module install nold-ai/specfact-backlog

# Skip dependency resolution (install only the requested module)
specfact module install nold-ai/specfact-backlog --skip-deps

# Force install despite dependency conflicts (use with care)
specfact module install nold-ai/specfact-backlog --force
```

- Use `--skip-deps` when you want to install a single module without pulling its dependencies or when you manage dependencies yourself.
- Use `--force` to proceed when resolution reports conflicts (e.g. for local overrides or known-compatible versions). Enable/disable and dependency-aware cascades still respect `--force` where applicable.
- If a dependency already exists in the selected install scope but its version does not satisfy a declared bundle dependency range, reinstall or upgrade that dependency in the same scope before retrying.

See [Dependency resolution](../reference/dependency-resolution.md) for how resolution works and conflict detection.

## Command aliases

You can alias a command name to a module-provided command so that a shorter or custom name invokes the same logic.

```bash
# Create an alias (e.g. "bp" for backlog’s "plan" command)
specfact module alias create bp backlog plan

# List all aliases
specfact module alias list

# Remove an alias
specfact module alias remove bp
```

Aliases are stored under `~/.specfact/registry/aliases.json`. **Aliases do not create or resolve top-level CLI commands**—the CLI surface stays the same; aliases are for reference and organization only. When you run a command, the registry resolves aliases first; if an alias would shadow a built-in command, a warning is shown. Use `--force` on create to override the shadow warning.

## Security and Trust Controls

- Denylist file: `~/.specfact/module-denylist.txt`
- Override path: `SPECFACT_MODULE_DENYLIST_FILE=/path/to/denylist.txt`
- Denylisted module ids are blocked in both `specfact module install` and `specfact module init`.

Publisher trust:

- Official publisher (`nold-ai`) proceeds without prompt.
- Non-official publishers require one-time trust acknowledgement.
- In non-interactive mode, pass `--trust-non-official` (or set `SPECFACT_TRUST_NON_OFFICIAL=1`).

Bundled integrity:

- `specfact module init` and bundled installs verify bundled module integrity metadata before copying.
- For developer workflows, unsigned bundles can be temporarily allowed with `SPECFACT_ALLOW_UNSIGNED=1`.

## List Modules

```bash
specfact module list
specfact module list --show-origin
specfact module list --source marketplace
specfact module list --show-bundled-available
specfact module doctor nold-ai/specfact-codebase
```

Default columns:

- `Module`
- `Version`
- `State`
- `Trust` (`official`, `community`, `local-dev`)
- `Publisher`

With `--show-origin`, an additional `Origin` column is shown (`built-in`, `project`, `user`, `marketplace`, `custom`).

`module doctor` keeps discovery metadata-only and reports effective vs shadowed duplicate copies, exact manifest versions, paths, enabled state, configured development source roots, and non-destructive scope guidance. Normal shadowing does not require uninstalling the lower-priority copy. Use it when project-scoped modules under `<repo>/.specfact/modules` and user-scoped modules under `~/.specfact/modules` disagree.

## Show Detailed Module Info

```bash
specfact module show module-registry
```

This prints detailed metadata:

- Name, description, version, state
- Trust, publisher, publisher URL, license
- Origin, tier, core compatibility
- Full command tree (including subcommands) with short command descriptions

## Search Modules

```bash
specfact module search bundle-mapper
```

Search queries **all configured registries** (official first, then custom in priority order) plus locally discovered modules. Results show a **Registry** column when multiple registries are configured.

Search includes both:

- Marketplace registry entries (`scope=marketplace`) from every registry
- Locally discovered modules (`scope=installed`)

Results are sorted alphabetically by module id.

## Enable and Disable Modules

```bash
specfact module enable backlog
specfact module disable backlog
specfact module disable plan --force
```

Use `--force` to allow dependency-aware cascades when required.

Running `specfact init --profile <profile>` or `specfact init --install <bundles>` directly enables the selected marketplace module ids. Rediscovered modules keep their previous enabled or disabled state unless they were selected by the profile/install request.

## Uninstall Behavior

```bash
specfact module uninstall backlog
specfact module uninstall nold-ai/specfact-backlog
specfact module uninstall backlog --scope project --repo /path/to/repo
```

Uninstall supports user and project scope roots.

Clear guidance is provided for:

- `built-in` modules (disable instead of uninstall)
- collisions where a module exists in both user and project roots (explicit `--scope` required)
- unknown/untracked modules (`module list --show-origin`)

## Upgrade Behavior

```bash
# Upgrade a single marketplace module
specfact module upgrade backlog

# Upgrade all marketplace modules
specfact module upgrade
specfact module upgrade --all
```

Upgrade applies only to modules with origin `marketplace`.

> Modules docs handoff: this page remains in the core docs set as release-line overview content.
> Canonical bundle-specific deep guidance now lives in the canonical modules docs site, currently
> published at `https://modules.specfact.io/` and is planned to migrate from `specfact-cli-modules`.
