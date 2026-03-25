---
layout: default
title: specfact module
permalink: /core-cli/module/
description: Reference for the specfact module command group - install, manage, search, and configure marketplace modules.
---

# specfact module

Manage marketplace modules: install, uninstall, search, upgrade, and configure registries.

Use `specfact module init --scope user|project` to seed bundled module trees and `specfact module install --scope user|project` to add or refresh modules. After modules are present, `specfact init ide` discovers their prompt resources from those roots and exports IDE-facing files; it does not download modules itself.

## Usage

```bash
specfact module <subcommand> [OPTIONS]
```

## Subcommands

### Module Lifecycle

| Command | Description |
|---------|-------------|
| `init` | Bootstrap shipped module artifacts into user or project module root |
| `install` | Install a module from bundled artifacts or marketplace registry |
| `uninstall` | Uninstall a marketplace module |
| `upgrade` | Upgrade marketplace module(s) to latest available versions |
| `enable` | Enable modules in lifecycle state registry |
| `disable` | Disable modules in lifecycle state registry |

### Discovery

| Command | Description |
|---------|-------------|
| `list` | List installed modules with trust labels and optional origin details |
| `show` | Show detailed metadata for an installed module |
| `search` | Search marketplace and installed modules by id/description/tags |

### Registry Management

| Command | Description |
|---------|-------------|
| `add-registry` | Add a custom registry to the config |
| `list-registries` | List all configured registries (official + custom) |
| `remove-registry` | Remove a custom registry from the config |

### Configuration

| Command | Description |
|---------|-------------|
| `alias` | Manage command aliases (map name to namespaced module) |

## Common Workflows

### Install a module from the marketplace

```bash
specfact module install backlog
specfact module install code-review
```

### List installed modules

```bash
specfact module list
```

### Search the marketplace

```bash
specfact module search "backlog"
specfact module search --tags governance
```

### Upgrade all modules

```bash
specfact module upgrade --all
```

### Add a private registry

```bash
specfact module add-registry my-company \
  --url https://registry.example.com \
  --trust-level verified
```

### Show module details

```bash
specfact module show backlog
```

## Related

- [Installing Modules](/module-system/installing-modules/) - step-by-step install guide
- [Module Marketplace](/module-system/module-marketplace/) - registry model and discovery priority
- [Custom Registries](/module-system/custom-registries/) - managing multiple registries
- [Bootstrap Checklist](/module-system/bootstrap-checklist/) - verify modules after install
