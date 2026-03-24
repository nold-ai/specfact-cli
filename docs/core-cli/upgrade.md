---
layout: default
title: specfact upgrade
permalink: /core-cli/upgrade/
description: Reference for the specfact upgrade command - check for and install SpecFact CLI updates.
---

# specfact upgrade

Check for and install SpecFact CLI updates.

## Usage

```bash
specfact upgrade [OPTIONS]
```

## Options

| Option | Type | Description |
|--------|------|-------------|
| `--check-only` | | Only check for updates, don't install |
| `--yes`, `-y` | | Skip confirmation prompt and install immediately |

## Examples

### Check for available updates

```bash
specfact upgrade --check-only
```

### Upgrade with confirmation

```bash
specfact upgrade
```

### Upgrade without confirmation

```bash
specfact upgrade -y
```

## Related

- [Migration Guide](/migration/migration-guide/) - version migration guidance
- [Migration 0.16 to 0.19](/migration/migration-0.16-to-0.19/) - specific version migration steps
