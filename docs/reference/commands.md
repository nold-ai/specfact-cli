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
| `nold-ai/specfact-project` | `project` | `project link-backlog`, `project health-check`, `project devops-flow`, `project snapshot`, `project regenerate`, `project export-roadmap`, `project import`, `project export`, `project sync` |
| `nold-ai/specfact-backlog` | `backlog` | `backlog ceremony`, `backlog refine`, `backlog daily`, `backlog sync`, `backlog auth`, `backlog analyze-deps`, `backlog verify-readiness`, `backlog delta`, `backlog add` |
| `nold-ai/specfact-codebase` | `code` | `code analyze`, `code drift`, `code validate`, `code repro`, `code import`, `code review` |
| `nold-ai/specfact-spec` | `spec` | `spec validate`, `spec backward-compat`, `spec generate-tests`, `spec mock` |
| `nold-ai/specfact-govern` | `govern` | `govern enforce`, `govern patch` |

## Migration: Removed Flat Commands

Flat compatibility shims were removed in `0.40.0`. Use grouped commands.

| Removed | Replacement |
|---|---|
| `specfact plan ...` | Removed — use `specfact project devops-flow` or `specfact project snapshot` |
| `specfact import ...` | `specfact code import ...` (codebase import) or `specfact project import ...` (persona Markdown) |
| `specfact sync ...` | `specfact project sync ...` |
| `specfact backlog ...` (flat module) | `specfact backlog ...` (bundle group) |
| `specfact analyze ...` | `specfact code analyze ...` |
| `specfact drift ...` | `specfact code drift ...` |
| `specfact validate ...` | `specfact code validate ...` |
| `specfact repro ...` | `specfact code repro ...` |
| `specfact contract ...` | Removed — use `specfact spec validate` |
| `specfact sdd ...` | Removed — use `specfact govern enforce sdd [BUNDLE]` |
| `specfact generate ...` | Removed — no direct replacement; use AI IDE skills for prompt generation |
| `specfact enforce ...` | `specfact govern enforce ...` |
| `specfact patch ...` | `specfact govern patch ...` |

## Common Flows

```bash
# First run (required)
specfact init --profile solo-developer

# Install specific workflow bundle
specfact module install nold-ai/specfact-backlog

# Project workflow examples
specfact code import legacy-api --repo .
specfact project snapshot --bundle legacy-api

# Code workflow examples
specfact code validate sidecar init legacy-api /path/to/repo
specfact code repro --verbose

# Backlog workflow examples
specfact backlog ceremony standup --help
specfact backlog ceremony refinement --help

# Spec validation examples
specfact spec validate --bundle my-api
specfact spec generate-tests --bundle my-api --output tests/
```

## See Also

- [Module Categories](module-categories.md)
- [Marketplace Bundles](../guides/marketplace.md)
- [Installing Modules](../guides/installing-modules.md)
- [Canonical modules docs site](https://modules.specfact.io/)

> Modules docs handoff: this command reference remains part of the core docs set because it
> explains the lean-core command topology. Bundle-specific command details live in the
> canonical modules docs site, currently published at
> `https://modules.specfact.io/`.
