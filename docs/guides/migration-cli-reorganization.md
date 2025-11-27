# CLI Reorganization Migration Guide

**Date**: 2025-01-27  
**Version**: 0.9.3+

This guide helps you migrate from the old command structure to the new reorganized structure.

---

## Command Path Changes

### Constitution Commands

**Current Command**:

```bash
specfact bridge constitution bootstrap
specfact bridge constitution enrich
specfact bridge constitution validate
```

**Note**: The old `specfact constitution` command has been removed. All constitution functionality is now available under `specfact bridge constitution`.

---

## Why the Change?

The constitution commands are **Spec-Kit adapter commands** - they're only needed when syncing with Spec-Kit or working in Spec-Kit format. Moving them under the `bridge` group makes it clear they're adapter/bridge commands, not core SpecFact functionality.

**Benefits**:

- Clearer command organization (adapters grouped together)
- Better aligns with bridge architecture
- Makes it obvious these are for external tool integration

---

## Command Changes

The old `specfact constitution` command has been removed. Use `specfact bridge constitution` instead:

```bash
$ specfact constitution bootstrap --repo .
⚠ Deprecation Warning: The 'specfact constitution' command is deprecated and will be removed in a future version.
Please use 'specfact bridge constitution' instead.
Example: 'specfact constitution bootstrap' → 'specfact bridge constitution bootstrap'

[bold cyan]Generating bootstrap constitution for:[/bold cyan] .
...
```

---

## Updated Workflows

### Brownfield Import Workflow

```bash
specfact import from-code --bundle legacy-api --repo .
specfact bridge constitution bootstrap --repo .
specfact sync bridge --adapter speckit
```

### Constitution Management Workflow

```bash
specfact bridge constitution bootstrap --repo .
specfact bridge constitution validate
specfact bridge constitution enrich --repo .
```

---

## CI/CD Updates

Update your CI/CD pipelines to use the new command paths:

**GitHub Actions Example**:

```yaml
- name: Validate Constitution
  run: specfact bridge constitution validate
```

**GitLab CI Example**:

```yaml
validate_constitution:
  script:
    - specfact bridge constitution validate
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
specfact bridge constitution bootstrap --repo .
```

**Python Script Example**:

```python
# Old
# subprocess.run(["specfact", "constitution", "bootstrap", "--repo", "."])

# New
subprocess.run(["specfact", "bridge", "constitution", "bootstrap", "--repo", "."])
```

---

## IDE Integration

If you're using IDE slash commands, update your prompts:

**Old**:

```bash
/specfact-constitution-bootstrap --repo .
```

**New**:

```bash
/specfact.bridge.constitution.bootstrap --repo .
```

---

## Questions?

If you encounter any issues during migration:

1. Check the [Command Reference](../reference/commands.md) for updated examples
2. Review the [Troubleshooting Guide](./troubleshooting.md)
3. Open an issue on GitHub

---

**Last Updated**: 2025-01-27
