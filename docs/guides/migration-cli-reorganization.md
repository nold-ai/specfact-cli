# CLI Reorganization Migration Guide

**Date**: 2025-11-27  
**Version**: 0.9.3+

This guide helps you migrate from the old command structure to the new reorganized structure, including parameter standardization, slash command changes, and bundle parameter integration.

---

## Overview of Changes

The CLI reorganization includes:

1. **Parameter Standardization** - Consistent parameter names across all commands
2. **Parameter Grouping** - Logical organization (Target → Output → Behavior → Advanced)
3. **Slash Command Reorganization** - Reduced from 13 to 8 commands with numbered workflow ordering
4. **Bundle Parameter Integration** - All commands now use `--bundle` parameter

---

## Parameter Name Changes

### Standard Parameter Names

| Old Name | New Name | Commands Affected |
|----------|----------|-------------------|
| `--base-path` | `--repo` | `generate contracts` |
| `--output` | `--out` | `bridge constitution bootstrap` |
| `--format` | `--output-format` | `enforce sdd`, `plan compare` |
| `--non-interactive` | `--no-interactive` | All commands |
| `--name` (bundle name) | `--bundle` | All commands |

### Deprecation Policy

- **Transition Period**: 3 months from implementation date (2025-11-27)
- **Deprecation Warnings**: Commands using deprecated names will show warnings
- **Removal**: Deprecated names will be removed after transition period
- **Documentation**: All examples and docs updated immediately

### Examples

**Before**:

```bash
specfact generate contracts --base-path .
specfact plan compare --bundle legacy-api --format json --out report.json
specfact enforce sdd legacy-api --non-interactive
```

**After**:

```bash
specfact generate contracts --repo .
specfact plan compare --bundle legacy-api --output-format json --out report.json
specfact enforce sdd legacy-api --no-interactive
```

---

## Slash Command Changes

### Old Slash Commands (13 total) → New Slash Commands (8 total)

| Old Command | New Command | Notes |
|-------------|-------------|-------|
| `/specfact-import-from-code` | `/specfact.01-import` | Numbered for workflow ordering |
| `/specfact-plan-init` | `/specfact.02-plan` | Unified plan management |
| `/specfact-plan-add-feature` | `/specfact.02-plan` | Merged into plan command |
| `/specfact-plan-add-story` | `/specfact.02-plan` | Merged into plan command |
| `/specfact-plan-update-idea` | `/specfact.02-plan` | Merged into plan command |
| `/specfact-plan-update-feature` | `/specfact.02-plan` | Merged into plan command |
| `/specfact-plan-review` | `/specfact.03-review` | Numbered for workflow ordering |
| `/specfact-plan-promote` | `/specfact.03-review` | Merged into review command |
| `/specfact-plan-compare` | `/specfact.compare` | Advanced command (no numbering) |
| `/specfact-enforce` | `/specfact.05-enforce` | Numbered for workflow ordering |
| `/specfact-sync` | `/specfact.06-sync` | Numbered for workflow ordering |
| `/specfact-repro` | `/specfact.validate` | Advanced command (no numbering) |
| `/specfact-plan-select` | *(CLI-only)* | Removed (use CLI directly) |

### Workflow Ordering

The new numbered commands follow natural workflow progression:

1. **Import** (`/specfact.01-import`) - Start by importing existing code
2. **Plan** (`/specfact.02-plan`) - Manage your plan bundle
3. **Review** (`/specfact.03-review`) - Review and promote your plan
4. **SDD** (`/specfact.04-sdd`) - Create SDD manifest
5. **Enforce** (`/specfact.05-enforce`) - Validate SDD and contracts
6. **Sync** (`/specfact.06-sync`) - Sync with external tools

**Advanced Commands** (no numbering):

- `/specfact.compare` - Compare plans
- `/specfact.validate` - Validation suite

### Ordered Workflow Examples

**Before**:

```bash
/specfact-import-from-code --repo . --confidence 0.7
/specfact-plan-init my-project
/specfact-plan-add-feature --key FEATURE-001 --title "User Auth"
/specfact-plan-review my-project
```

**After**:

```bash
/specfact.01-import legacy-api --repo . --confidence 0.7
/specfact.02-plan init legacy-api
/specfact.02-plan add-feature --bundle legacy-api --key FEATURE-001 --title "User Auth"
/specfact.03-review legacy-api
```

---

## Bundle Parameter Addition

### All Commands Now Require `--bundle`

**Before** (positional argument):

```bash
specfact plan init legacy-api
specfact plan review legacy-api
```

**After** (named parameter):

```bash
specfact plan init legacy-api
specfact plan review legacy-api
```

### Path Resolution Changes

- **Old**: Used positional argument or `--name` for bundle identification
- **New**: Uses `--bundle` parameter for bundle name
- **Path**: Bundle path is resolved from bundle name: `.specfact/projects/<bundle-name>/`

### Migration Steps

1. **Update all scripts** to use `--bundle` instead of positional arguments
2. **Update CI/CD pipelines** to use new parameter format
3. **Update IDE slash commands** to use new numbered format
4. **Test workflows** to ensure bundle resolution works correctly

---

## Command Path Changes

### Constitution Commands

**Current Command**:

```bash
specfact sdd constitution bootstrap
specfact sdd constitution enrich
specfact sdd constitution validate
```

**Note**: The old `specfact constitution` command has been removed. All constitution functionality is now available under `specfact sdd constitution`.

---

## Why the Change?

The constitution commands are **Spec-Kit adapter commands** - they're only needed when syncing with Spec-Kit or working in Spec-Kit format. They are now under the `sdd` (Spec-Driven Development) command group, as constitution management is part of the SDD workflow.

**Benefits**:

- Clearer command organization (adapters grouped together)
- Better aligns with bridge architecture
- Makes it obvious these are for external tool integration

---

## Command Changes

The old `specfact constitution` command has been removed. Use `specfact sdd constitution` instead:

```bash
$ specfact constitution bootstrap --repo .
⚠ Breaking Change: The 'specfact constitution' command has been removed.
Please use 'specfact sdd constitution' instead.
Example: 'specfact constitution bootstrap' → 'specfact sdd constitution bootstrap'

[bold cyan]Generating bootstrap constitution for:[/bold cyan] .
...
```

---

## Updated Workflows

### Brownfield Import Workflow

```bash
specfact import from-code legacy-api --repo .
specfact sdd constitution bootstrap --repo .
specfact sync bridge --adapter speckit
```

### Constitution Management Workflow

```bash
specfact sdd constitution bootstrap --repo .
specfact sdd constitution validate
specfact sdd constitution enrich --repo .
```

---

## CI/CD Updates

Update your CI/CD pipelines to use the new command paths:

**GitHub Actions Example**:

```yaml
- name: Validate Constitution
  run: specfact sdd constitution validate
```

**GitLab CI Example**:

```yaml
validate_constitution:
  script:
    - specfact sdd constitution validate
```

---

## Script Updates

Update any scripts that use the old commands:

**Bash Script Example**:

```bash
#!/bin/bash
# Old
# specfact constitution bootstrap --repo .

# New
specfact sdd constitution bootstrap --repo .
```

**Python Script Example**:

```python
# Old
# subprocess.run(["specfact", "constitution", "bootstrap", "--repo", "."])

# New
subprocess.run(["specfact", "sdd", "constitution", "bootstrap", "--repo", "."])
```

---

## IDE Integration

If you're using IDE slash commands, update your prompts:

**Old**:

```bash
/specfact-plan-init legacy-api
```

**New**:

```bash
/specfact.02-plan init legacy-api
```

---

## Module System Migration Note

This CLI reorganization aligns with the module-first architecture:

- Core runtime remains responsible for lifecycle, registry, and orchestration.
- Feature command implementations belong in `src/specfact_cli/modules/<module>/src/commands.py`.
- Legacy `src/specfact_cli/commands/*.py` files are compatibility shims only.

When updating internal tooling or extensions, prefer module-local imports over shim imports.

---

## Questions?

If you encounter any issues during migration:

1. Check the [Command Reference](../reference/commands.md) for updated examples
2. Review the [Troubleshooting Guide](./troubleshooting.md)
3. Open an issue on GitHub

---

**Last Updated**: 2025-01-27
