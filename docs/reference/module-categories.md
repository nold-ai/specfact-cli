---
layout: default
title: Module Categories
nav_order: 35
permalink: /reference/module-categories/
doc_owner: specfact-cli
tracks: [src/specfact_cli/registry/**, ../specfact-cli-modules/packages/**]
last_reviewed: 2026-07-10
exempt: false
exempt_reason: ""
---

# Module Categories

SpecFact groups feature modules into workflow-oriented command families.

Core commands remain top-level:

- `specfact init`
- `specfact module`
- `specfact upgrade`

Category command groups:

- `specfact project ...`
- `specfact backlog ...`
- `specfact code ...`
- `specfact spec ...`
- `specfact govern ...`
- `specfact requirements ...`

## Canonical Category Assignments

| Module | Category | Bundle | Group Command | Sub-command |
|---|---|---|---|---|
| `init` | `core` | — | — | `init` |
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
| `code_review` | `codebase` | `specfact-code-review` | `code` | `review` |
| `contract` | `spec` | `specfact-spec` | `spec` | `contract` |
| `spec` | `spec` | `specfact-spec` | `spec` | `api` |
| `sdd` | `spec` | `specfact-spec` | `spec` | `sdd` |
| `generate` | `spec` | `specfact-spec` | `spec` | `generate` |
| `enforce` | `govern` | `specfact-govern` | `govern` | `enforce` |
| `patch_mode` | `govern` | `specfact-govern` | `govern` | `patch` |
| `requirements` | `requirements` | `specfact-requirements` | `requirements` | `requirements` |

Official marketplace package IDs are `nold-ai/specfact-project`,
`nold-ai/specfact-backlog`, `nold-ai/specfact-codebase`,
`nold-ai/specfact-code-review`, `nold-ai/specfact-spec`,
`nold-ai/specfact-govern`, and `nold-ai/specfact-requirements`.

## Bundle Contents by Category

- `specfact-project`: `project`, `plan`, `import`, `sync`, `migrate`
- `specfact-backlog`: `backlog`, `policy`
- `specfact-codebase`: `analyze`, `drift`, `validate`, `repro`
- `specfact-code-review`: `code review`
- `specfact-spec`: `contract`, `api`, `sdd`, `generate`
- `specfact-govern`: `enforce`, `patch`
- `specfact-requirements`: `requirements`

## Bundle Package Layout and Namespaces

Official bundle packages are published from the dedicated modules repository:

- Repository: `nold-ai/specfact-cli-modules`
- Package roots: `packages/specfact-project/`, `packages/specfact-backlog/`, `packages/specfact-codebase/`, `packages/specfact-code-review/`, `packages/specfact-spec/`, `packages/specfact-govern/`, `packages/specfact-requirements/`

Namespace mapping:

- `specfact-project` -> import namespace `specfact_project.*`
- `specfact-backlog` -> import namespace `specfact_backlog.*`
- `specfact-codebase` -> import namespace `specfact_codebase.*`
- `specfact-code-review` -> import namespace `specfact_code_review.*`
- `specfact-spec` -> import namespace `specfact_spec.*`
- `specfact-govern` -> import namespace `specfact_govern.*`
- `specfact-requirements` -> import namespace `specfact_requirements.*`

Compatibility note:

- Flat top-level command shims were removed. Use category groups (`project`, `backlog`, `code`, `spec`, `govern`, `requirements`).
- `specfact backlog auth ...` is provided by the backlog bundle, not by the permanent core command surface.
- Prerelease `specfact-requirements` manifests that still declare category
  `project` with `bundle_group_command: requirements` are normalized to the
  canonical `requirements` group during core discovery.

> Modules docs handoff: this page remains in the core docs set as release-line overview content.
> Canonical bundle-specific deep guidance now lives in the canonical modules docs site, currently
> published at `https://modules.specfact.io/`.

## First-Run Profiles

`specfact init` supports validation tiers, legacy profile presets, and explicit bundle selection.
Validation tiers (`solo`, `startup`, `mid_size`, `enterprise`) write layered validation config with
source annotations. Tier-based profiles install the current bundle sets below:

- `solo` -> `specfact-codebase`, `specfact-code-review`
- `startup` -> `specfact-project`, `specfact-backlog`, `specfact-codebase`, `specfact-code-review`
- `mid_size` -> `specfact-project`, `specfact-backlog`, `specfact-codebase`, `specfact-spec`, `specfact-code-review`
- `enterprise` -> `specfact-project`, `specfact-backlog`, `specfact-codebase`, `specfact-spec`, `specfact-govern`, `specfact-code-review`

Legacy workflow presets remain accepted for compatibility. They map to the corresponding validation
tier for config defaults while preserving their historical install selections:

- `solo-developer` -> `solo`
- `backlog-team` -> `startup`
- `api-first-team` -> `mid_size`
- `enterprise-full-stack` -> `enterprise`

`specfact-requirements` is an official, explicitly installable evidence module.
It remains outside the current named profile presets; install it with
`specfact init --install requirements` when requirements evidence is needed.

Examples:

```bash
specfact init --profile startup
specfact init --install backlog,code-review
specfact init --install requirements
specfact init --install all
```

## Command Topology: Before and After

Before:

- Flat top-level command surface with many feature commands.

After:

- Core top-level commands plus grouped workflow families (`project`, `backlog`, `code`, `spec`, `govern`, `requirements`).
- No backward-compatibility flat shims.
