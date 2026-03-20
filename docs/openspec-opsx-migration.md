---
layout: default
title: Openspec Opsx Migration
permalink: /openspec-opsx-migration/
---

# OpenSpec OPSX Migration

SpecFact CLI has migrated to **OpenSpec OPSX** (fluid, action-based workflow). Project context and configuration now use `openspec/config.yaml` as the primary source; `openspec/project.md` is supported as a legacy fallback so existing repos keep working.

## What Changed

| Before (Legacy)              | After (OPSX)                                      |
|-----------------------------|---------------------------------------------------|
| `openspec/project.md` only  | `openspec/config.yaml` (primary); `project.md` (fallback) |
| Phase-locked workflow       | Fluid actions: new, continue, apply, archive      |
| `openspec/AGENTS.md`        | Obsolete; use `openspec/config.yaml` and OPSX commands |

## SpecFact CLI Integration

- **Project context import**: When syncing OpenSpec project context, the bridge resolves `openspec/config.yaml` first; if absent, it uses `openspec/project.md`. No code changes required in repos that still have `project.md`.
- **Detection**: OpenSpec is detected if `openspec/config.yaml`, `openspec/project.md`, or `openspec/specs/` exists.
- **Config format**: See [openspec/config.yaml](../openspec/config.yaml) in this repo for an example. The `context:` block is injected into planning; `rules:` apply per-artifact.

## References

- [OPSX Workflow](https://github.com/Fission-AI/OpenSpec/blob/main/docs/opsx.md) – fluid workflow, config, commands
- [Migrating to OPSX](https://github.com/Fission-AI/OpenSpec/blob/main/docs/migration-guide.md) – moving from project.md to config.yaml

## For Contributors

- Use **openspec/config.yaml** for project context and per-artifact rules.
- Existing **openspec/project.md** continues to work; migrate when convenient by moving content into `config.yaml` and removing `project.md`.
