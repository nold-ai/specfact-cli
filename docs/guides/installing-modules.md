---
layout: default
title: Installing Modules
permalink: /guides/installing-modules/
description: Install, list, show, enable, disable, uninstall, and upgrade SpecFact modules.
---

# Installing Modules

Use the `specfact module` command group to manage marketplace and locally discovered modules.

## Install Behavior

```bash
# Marketplace id format
specfact module install specfact/backlog

# Bare names are accepted and normalized to specfact/<name>
specfact module install backlog

# Install a specific version
specfact module install specfact/backlog --version 0.35.0
```

Notes:

- If a module is already available locally (`built-in` or `custom`), install is skipped with a clear message.
- Invalid ids show an explicit error (`name` or `namespace/name` only).

## List Modules

```bash
specfact module list
specfact module list --show-origin
specfact module list --source marketplace
```

Default columns:

- `Module`
- `Version`
- `State`
- `Trust` (`official`, `community`, `local-dev`)
- `Publisher`

With `--show-origin`, an additional `Origin` column is shown (`built-in`, `marketplace`, `custom`).

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

Search includes both:

- Marketplace registry entries (`scope=marketplace`)
- Locally discovered modules (`scope=installed`)

Results are sorted alphabetically by module id.

## Enable and Disable Modules

```bash
specfact module enable backlog
specfact module disable backlog
specfact module disable plan --force
```

Use `--force` to allow dependency-aware cascades when required.

## Uninstall Behavior

```bash
specfact module uninstall backlog
specfact module uninstall specfact/backlog
```

Uninstall only removes marketplace-installed modules.

Clear guidance is provided for:

- `built-in` modules (disable instead of uninstall)
- `custom` modules (remove from local module roots)
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
