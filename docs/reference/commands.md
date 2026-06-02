---
layout: default
title: Command Reference
permalink: /reference/commands/
keywords: [command reference, cli surface, command groups]
audience: [solo, team, enterprise]
expertise_level: [intermediate, advanced]
---

# Command Reference

SpecFact CLI ships a lean core. Workflow commands are installed from official or marketplace modules and mounted under grouped command families.
Flat root-level compatibility shims were removed in `0.40.0`; use category-group commands only.

## Top-Level Commands

The live root command surface includes:

- `specfact init`
- `specfact module`
- `specfact upgrade`
- `specfact backlog ...`
- `specfact code ...`
- `specfact govern ...`
- `specfact project ...`
- `specfact spec ...`

Use `specfact init --profile <name>` or `specfact init --install <comma-list>` to bootstrap the workflow bundles you need.

## Core-Owned Commands

### `specfact init`

Bootstrap SpecFact and manage first-run setup.

- `specfact init --profile <profile>`
- `specfact init --install <bundle-list>`
- `specfact init ide [--ide <cursor|vscode|copilot|...>]`

### `specfact module`

Manage installed modules and registries.

- `specfact module init`
- `specfact module install`
- `specfact module uninstall`
- `specfact module add-registry`
- `specfact module list-registries`
- `specfact module remove-registry`
- `specfact module enable`
- `specfact module disable`
- `specfact module search`
- `specfact module list`
- `specfact module show`
- `specfact module upgrade`
- `specfact module alias`

### `specfact upgrade`

Check for and install CLI updates.

## Installed Workflow Command Groups

After bundle install, workflow commands are mounted by category:

### `specfact project`

- `project link-backlog`
- `project health-check`
- `project devops-flow`
- `project snapshot`
- `project regenerate`
- `project export-roadmap`
- `project export`
- `project import`
- `project lock`
- `project unlock`
- `project locks`
- `project init-personas`
- `project merge`
- `project resolve-conflict`
- `project version`
- `project sync`

### `specfact backlog`

- `backlog ceremony`
- `backlog delta`
- `backlog auth`
- `backlog sync`
- `backlog verify-readiness`
- `backlog analyze-deps`
- `backlog diff`
- `backlog promote`
- `backlog refine`
- `backlog daily`
- `backlog init-config`
- `backlog map-fields`
- `backlog add`

Preferred ceremony paths:

- `specfact backlog ceremony standup ...`
- `specfact backlog ceremony refinement ...`

Compatibility note: `specfact backlog daily ...` and `specfact backlog refine ...` remain available.

### `specfact code`

- `code review`
- `code import`
- `code analyze`
- `code drift`
- `code validate`
- `code repro`

### `specfact spec`

- `spec validate`
- `spec backward-compat`
- `spec generate-tests`
- `spec mock`

### `specfact govern`

- `govern enforce`
- `govern patch`

## Bundle To Command Mapping

| Bundle ID | Group | Main command families |
|---|---|---|
| `nold-ai/specfact-project` | `project` | `project link-backlog`, `project health-check`, `project devops-flow`, `project snapshot`, `project regenerate`, `project export-roadmap`, `project import`, `project export`, `project sync`, `project version` |
| `nold-ai/specfact-backlog` | `backlog` | `backlog ceremony`, `backlog refine`, `backlog daily`, `backlog sync`, `backlog auth`, `backlog analyze-deps`, `backlog verify-readiness`, `backlog delta`, `backlog add`, `backlog map-fields` |
| `nold-ai/specfact-codebase` | `code` | `code analyze`, `code drift`, `code validate`, `code repro`, `code import`, `code review` |
| `nold-ai/specfact-spec` | `spec` | `spec validate`, `spec backward-compat`, `spec generate-tests`, `spec mock` |
| `nold-ai/specfact-govern` | `govern` | `govern enforce`, `govern patch` |

## Migration: Removed Flat Commands

Flat compatibility shims were removed in `0.40.0`. Use grouped commands.

| Removed | Replacement |
|---|---|
| `specfact plan ...` | Removed — use `specfact project devops-flow` or `specfact project snapshot` |
| `specfact import ...` | `specfact code import ...` (codebase import) or `specfact project import ...` (persona Markdown import) |
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
# First run
specfact init --profile solo-developer

# Install specific workflow bundle
specfact module install nold-ai/specfact-backlog

# Code + project flow
specfact code import --repo . legacy-api
specfact project snapshot --bundle legacy-api

# Backlog flow
specfact backlog ceremony standup --help
specfact backlog ceremony refinement --help
specfact backlog verify-readiness --bundle legacy-api

# Bridge synchronization
specfact project sync bridge --adapter github --bundle legacy-api --mode export-only

# Spec validation examples
specfact spec validate --bundle my-api
specfact spec generate-tests --bundle my-api --output tests/
```

## Handoff To Canonical Modules Docs

This command reference remains part of the core docs set because it explains the lean-core command topology and ownership boundary.
Bundle-specific command details, tutorials, and adapter runbooks live in the canonical modules docs site, currently published at `https://modules.specfact.io/`.

See also:

- [Reference Index](README.md)
- [Module Categories](module-categories.md)
- [Installing Modules](../module-system/installing-modules.md)
- [Canonical modules docs site](https://modules.specfact.io/)
