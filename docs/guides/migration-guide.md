---
layout: default
title: Migration Guide
permalink: /migration-guide/
---

# Migration Guide

> **Decision tree and workflow for migrating between SpecFact CLI versions and from other tools**

---

## Overview

This guide helps you decide when and how to migrate:

- **Between SpecFact CLI versions** - When upgrading to a new version
- **From other tools** - When migrating from Spec-Kit, OpenSpec, or other SDD tools
- **Between project structures** - When restructuring your project bundles

---

## Migration Decision Tree

```
Start: What do you need to migrate?

├─ Upgrading SpecFact CLI version?
│  ├─ Minor version (0.19 → 0.20)?
│  │  └─ → Usually automatic, check [Version-Specific Migration Guides](#version-specific-migrations)
│  ├─ Major version (0.x → 1.0)?
│  │  └─ → Check breaking changes, use [Version-Specific Migration Guides](#version-specific-migrations)
│  └─ CLI reorganization (pre-0.16 → 0.16+)?
│     └─ → See [CLI Reorganization Migration](migration-cli-reorganization.md)
│
├─ Migrating from Spec-Kit?
│  └─ → See [Spec-Kit Journey Guide](speckit-journey.md)
│
├─ Migrating from OpenSpec?
│  └─ → See [OpenSpec Journey Guide](openspec-journey.md)
│
└─ Restructuring project bundles?
   └─ → See [Project Bundle Management](../reference/commands.md#project---project-bundle-management)
```

---

## Version-Specific Migrations

### Migration from 0.16 to 0.19+

**Breaking Changes**: CLI command reorganization

**Migration Steps**:

1. Review [CLI Reorganization Migration Guide](migration-cli-reorganization.md)
2. Update scripts and CI/CD pipelines
3. Test commands in development environment
4. Update documentation references

**Related**: [Migration 0.16 to 0.19](migration-0.16-to-0.19.md)

---

### Migration from Pre-0.16 to 0.16+

**Breaking Changes**: Major CLI reorganization

**Migration Steps**:

1. Review [CLI Reorganization Migration Guide](migration-cli-reorganization.md)
2. Update all command references
3. Migrate plan bundles to new schema
4. Update CI/CD configurations

**Related**: [CLI Reorganization Migration](migration-cli-reorganization.md)

---

## Tool Migration Workflows

### Migrating from Spec-Kit

**Workflow**: Use External Tool Integration Chain

1. Import from Spec-Kit via bridge adapter
2. Review imported plan
3. Set up bidirectional sync (optional)
4. Enforce SDD compliance

**Detailed Guide**: [Spec-Kit Journey Guide](speckit-journey.md)

**Command Chain**: [External Tool Integration Chain](command-chains.md#3-external-tool-integration-chain)

---

### Migrating from OpenSpec

**Workflow**: Use External Tool Integration Chain

1. Import from OpenSpec via bridge adapter
2. Review imported change proposals
3. Set up DevOps sync (optional)
4. Enforce SDD compliance

**Detailed Guide**: [OpenSpec Journey Guide](openspec-journey.md)

**Command Chain**: [External Tool Integration Chain](command-chains.md#3-external-tool-integration-chain)

---

## Project Structure Migrations

### Migrating Between Project Bundles

**When to use**: Restructuring projects, splitting/merging bundles

**Commands**:

```bash
# Export from old bundle
specfact project export --bundle old-bundle --persona <persona>

# Create new bundle
specfact plan init new-bundle

# Import to new bundle (manual editing may be required)
specfact project import --bundle new-bundle --persona <persona> --source exported.md
```

**Related**: [Project Bundle Management](../reference/commands.md#project---project-bundle-management)

---

## Plan Schema Migrations

### Upgrading Plan Bundles

**When to use**: When plan bundles are on an older schema version

**Command**:

```bash
# Upgrade all bundles
specfact plan upgrade --all

# Upgrade specific bundle
specfact plan upgrade --bundle <bundle-name>
```

**Benefits**:

- Improved performance (44% faster `plan select`)
- New features and metadata
- Better compatibility

**Related**: [Plan Upgrade](../reference/commands.md#plan-upgrade)

---

## Migration Workflow Examples

### Example 1: Upgrading SpecFact CLI

```bash
# 1. Check current version
specfact --version

# 2. Review migration guide for target version
# See: guides/migration-*.md

# 3. Upgrade SpecFact CLI
pip install --upgrade specfact-cli

# 4. Upgrade plan bundles
specfact plan upgrade --all

# 5. Test commands
specfact plan select --last 5
```

---

### Example 2: Migrating from Spec-Kit

```bash
# 1. Import from Spec-Kit
specfact import from-bridge --repo . --adapter speckit --write

# 2. Review imported plan
specfact plan review <bundle-name>

# 3. Set up bidirectional sync (optional)
specfact sync bridge --adapter speckit --bundle <bundle-name> --bidirectional --watch

# 4. Enforce SDD compliance
specfact enforce sdd --bundle <bundle-name>
```

**Related**: [Spec-Kit Journey Guide](speckit-journey.md)

---

## Troubleshooting Migrations

### Common Issues

**Issue**: Plan bundles fail to upgrade

**Solution**:

```bash
# Check bundle schema version
specfact plan select --bundle <bundle-name> --json | jq '.schema_version'

# Manual upgrade if needed
specfact plan upgrade --bundle <bundle-name> --force
```

**Issue**: Imported plans have missing data

**Solution**:

1. Review import logs
2. Use `plan review` to identify gaps
3. Use `plan update-feature` to fill missing data
4. Re-import if needed

**Related**: [Troubleshooting Guide](troubleshooting.md)

---

## See Also

- [Command Chains Reference](command-chains.md) - Complete workflows
- [Common Tasks Index](common-tasks.md) - Quick reference
- [Spec-Kit Journey Guide](speckit-journey.md) - Spec-Kit migration
- [OpenSpec Journey Guide](openspec-journey.md) - OpenSpec migration
- [Troubleshooting Guide](troubleshooting.md) - Common issues
