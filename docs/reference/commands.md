---
layout: default
title: Command Reference
permalink: /reference/commands/
---

# Command Reference

SpecFact CLI now ships a lean core. Workflow commands are installed from marketplace bundles.
Flat root-level compatibility shims were removed in `0.40.0`; use category-group commands only.

## Top-Level Commands

Root command surface includes core commands and installed category groups only:

- `specfact init`
- `specfact auth`
- `specfact module`
- `specfact upgrade`
- `specfact code ...`
- `specfact backlog ...`
- `specfact project ...`
- `specfact spec ...`
- `specfact govern ...`

Use `specfact init --profile <name>` (or `--install <list>`) to install workflow bundles.

## Workflow Command Groups

After bundle install, command groups are mounted by category:

- `specfact project ...`
- `specfact backlog ...`
- `specfact code ...`
- `specfact spec ...`
- `specfact govern ...`

## Bundle to Command Mapping

| Bundle ID | Group | Main command families |
|---|---|---|
| `nold-ai/specfact-project` | `project` | `project`, `plan`, `import`, `sync`, `migrate` |
| `nold-ai/specfact-backlog` | `backlog` | `backlog`, `policy` |
| `nold-ai/specfact-codebase` | `code` | `analyze`, `drift`, `validate`, `repro` |
| `nold-ai/specfact-spec` | `spec` | `contract`, `api`, `sdd`, `generate` |
| `nold-ai/specfact-govern` | `govern` | `enforce`, `patch` |

## Migration: Removed Flat Commands

Flat compatibility shims were removed in this change. Use grouped commands.

| Removed | Replacement |
|---|---|
| `specfact plan ...` | `specfact project plan ...` |
| `specfact import ...` | `specfact project import ...` |
| `specfact sync ...` | `specfact project sync ...` |
| `specfact migrate ...` | `specfact project migrate ...` |
| `specfact backlog ...` (flat module) | `specfact backlog ...` (bundle group) |
| `specfact analyze ...` | `specfact code analyze ...` |
| `specfact drift ...` | `specfact code drift ...` |
| `specfact validate ...` | `specfact code validate ...` |
| `specfact repro ...` | `specfact code repro ...` |
| `specfact contract ...` | `specfact spec contract ...` |
| `specfact spec ...` (flat module) | `specfact spec api ...` |
| `specfact sdd ...` | `specfact spec sdd ...` |
| `specfact generate ...` | `specfact spec generate ...` |
| `specfact enforce ...` | `specfact govern enforce ...` |
| `specfact patch ...` | `specfact govern patch ...` |

## Common Flows

```bash
# First run (required)
specfact init --profile solo-developer

# Install specific workflow bundle
specfact module install nold-ai/specfact-backlog

# Project workflow examples
specfact project import from-code legacy-api --repo .
specfact project plan review legacy-api

# Code workflow examples
specfact code validate sidecar init legacy-api /path/to/repo
specfact code repro --verbose

# Backlog workflow examples
specfact backlog ceremony standup --help
specfact backlog ceremony refinement --help
```

## See Also

- [Module Categories](module-categories.md)
- [Marketplace Bundles](../guides/marketplace.md)
- [Installing Modules](../guides/installing-modules.md)
