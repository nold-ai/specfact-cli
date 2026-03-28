---
layout: default
title: specfact upgrade
permalink: /core-cli/upgrade/
description: Reference for the specfact upgrade command - check for and install SpecFact CLI updates.
keywords: [upgrade, updates, cli-version]
audience: [solo, team, enterprise]
expertise_level: [beginner, intermediate]
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
- [Command Reference](/reference/commands/) - current grouped command surface
