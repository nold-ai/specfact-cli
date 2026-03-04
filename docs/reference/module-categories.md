---
layout: default
title: Module Categories
nav_order: 35
permalink: /reference/module-categories/
---

# Module Categories

SpecFact groups feature modules into workflow-oriented command families.

Core commands remain top-level:

- `specfact init`
- `specfact backlog auth`
- `specfact module`
- `specfact upgrade`

Category command groups:

- `specfact project ...`
- `specfact backlog ...`
- `specfact code ...`
- `specfact spec ...`
- `specfact govern ...`

## Canonical Category Assignments

| Module | Category | Bundle | Group Command | Sub-command |
|---|---|---|---|---|
| `init` | `core` | — | — | `init` |
| `auth` | `core` | — | — | `auth` |
| `module_registry` | `core` | — | — | `module` |
| `upgrade` | `core` | — | — | `upgrade` |
| `project` | `project` | `specfact-project` | `project` | `project` |
| `plan` | `project` | `specfact-project` | `project` | `plan` |
| `import_cmd` | `project` | `specfact-project` | `project` | `import` |
| `sync` | `project` | `specfact-project` | `project` | `sync` |
| `migrate` | `project` | `specfact-project` | `project` | `migrate` |
| `backlog` | `backlog` | `specfact-backlog` | `backlog` | `backlog` |
| `policy_engine` | `backlog` | `specfact-backlog` | `backlog` | `policy` |
| `analyze` | `codebase` | `specfact-codebase` | `code` | `analyze` |
| `drift` | `codebase` | `specfact-codebase` | `code` | `drift` |
| `validate` | `codebase` | `specfact-codebase` | `code` | `validate` |
| `repro` | `codebase` | `specfact-codebase` | `code` | `repro` |
| `contract` | `spec` | `specfact-spec` | `spec` | `contract` |
| `spec` | `spec` | `specfact-spec` | `spec` | `api` |
| `sdd` | `spec` | `specfact-spec` | `spec` | `sdd` |
| `generate` | `spec` | `specfact-spec` | `spec` | `generate` |
| `enforce` | `govern` | `specfact-govern` | `govern` | `enforce` |
| `patch_mode` | `govern` | `specfact-govern` | `govern` | `patch` |

## Bundle Contents by Category

- `specfact-project`: `project`, `plan`, `import`, `sync`, `migrate`
- `specfact-backlog`: `backlog`, `policy`
- `specfact-codebase`: `analyze`, `drift`, `validate`, `repro`
- `specfact-spec`: `contract`, `api`, `sdd`, `generate`
- `specfact-govern`: `enforce`, `patch`

## Bundle Package Layout and Namespaces

Official bundle packages are published from the dedicated modules repository:

- Repository: `nold-ai/specfact-cli-modules`
- Package roots: `packages/specfact-project/`, `packages/specfact-backlog/`, `packages/specfact-codebase/`, `packages/specfact-spec/`, `packages/specfact-govern/`

Namespace mapping:

- `specfact-project` -> import namespace `specfact_project.*`
- `specfact-backlog` -> import namespace `specfact_backlog.*`
- `specfact-codebase` -> import namespace `specfact_codebase.*`
- `specfact-spec` -> import namespace `specfact_spec.*`
- `specfact-govern` -> import namespace `specfact_govern.*`

Compatibility note:

- Flat top-level command shims were removed. Use category groups (`project`, `backlog`, `code`, `spec`, `govern`).

## First-Run Profiles

`specfact init` supports profile presets and explicit bundle selection:

- `solo-developer` -> `specfact-codebase`
- `backlog-team` -> `specfact-backlog`, `specfact-project`, `specfact-codebase`
- `api-first-team` -> `specfact-spec`, `specfact-codebase` (and `specfact-project` is auto-installed as a dependency)
- `enterprise-full-stack` -> `specfact-project`, `specfact-backlog`, `specfact-codebase`, `specfact-spec`, `specfact-govern`

Examples:

```bash
specfact init --profile solo-developer
specfact init --install backlog,codebase
specfact init --install all
```

## Command Topology: Before and After

Before:

- Flat top-level command surface with many feature commands.

After:

- Core top-level commands plus grouped workflow families (`project`, `backlog`, `code`, `spec`, `govern`).
- No backward-compatibility flat shims.
