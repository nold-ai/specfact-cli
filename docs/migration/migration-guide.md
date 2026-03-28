---
layout: default
title: Migration Guide
permalink: /migration/migration-guide/
redirect_from:
  - /migration-guide/
  - /guides/migration-guide/
description: Current migration guidance for upgrading SpecFact CLI, moving to grouped commands, and importing from external workflows.
keywords: [migration, upgrade path, grouped commands, openspec, speckit]
audience: [team, enterprise]
expertise_level: [intermediate]
---

# Migration Guide

Use this guide when you are moving an existing repo or team workflow onto the current SpecFact CLI model.

This page is intentionally focused on the active `0.4x.y` line. It does not try to preserve every historical transition. If you are running a very old install, treat that as a staged migration: first get onto the modern grouped command surface, then validate your repo and bundle state.

## What this guide covers

- Upgrading the core CLI to the current release line
- Moving from removed flat commands to grouped commands
- Importing existing work from external toolchains such as Spec-Kit or OpenSpec
- Revalidating bundles, sync flows, and docs links after the migration

## Start here

Choose the path that matches your situation:

1. **You already use modern grouped commands** such as `specfact project`, `specfact backlog`, `specfact code`, `specfact spec`, and `specfact govern`.
   Upgrade the CLI, check installed modules, and run validation.
2. **Your scripts still use older flat commands** such as `specfact plan`, `specfact import`, `specfact sync`, `specfact validate`, or `specfact enforce`.
   Update those scripts to the grouped command surface before rolling the change out.
3. **You are moving from another structured workflow tool** such as Spec-Kit or OpenSpec.
   Import first, review the generated project state, then enable ongoing bridge sync only after the imported state looks correct.

## 1. Upgrade the active CLI

Check the current version first:

```bash
specfact --version
specfact upgrade --check-only
```

If an update is available:

```bash
specfact upgrade
```

After the upgrade:

```bash
specfact module list
specfact module search
```

Use those commands to confirm the CLI still sees the installed workflow modules and registries you expect.

## 2. Move to the grouped command surface

The current CLI is lean core plus mounted command groups. Core-owned commands stay at the root:

- `specfact init`
- `specfact module`
- `specfact upgrade`

Workflow capabilities are mounted under grouped families:

- `specfact project ...`
- `specfact backlog ...`
- `specfact code ...`
- `specfact spec ...`
- `specfact govern ...`

If your automation still uses older flat command paths, update them now.

### Common replacements

| Old pattern | Current replacement |
| --- | --- |
| `specfact plan ...` | `specfact project ...` |
| `specfact import ...` | `specfact code import ...` or `specfact project import ...` |
| `specfact sync ...` | `specfact project sync ...` |
| `specfact analyze ...` | `specfact code analyze ...` |
| `specfact drift ...` | `specfact code drift ...` |
| `specfact validate ...` | `specfact code validate ...` or `specfact spec validate ...` |
| `specfact repro ...` | `specfact code repro ...` |
| `specfact enforce ...` | `specfact govern enforce ...` |
| `specfact patch ...` | `specfact govern patch ...` |

Use the canonical mapping in the [Command Reference](../reference/commands.md) when updating shell scripts, CI jobs, IDE prompts, or internal docs.

## 3. Rebaseline the project after the upgrade

Once the command surface is current, refresh the repo state you depend on:

```bash
specfact project health-check
specfact project regenerate
```

If you operate specific bundles directly:

```bash
specfact project snapshot --bundle <bundle-name>
specfact project version --bundle <bundle-name>
```

This is the point where you should catch stale bundle metadata, missing generated assets, or drift between the project state and the current CLI expectations.

## 4. Migrate from external toolchains

### From Spec-Kit

If your repo still starts from Spec-Kit assets, import first and keep sync optional until you trust the imported state:

```bash
specfact code import from-bridge --adapter speckit --repo . --dry-run
specfact code import from-bridge --adapter speckit --repo . --write
specfact project devops-flow --stage develop --bundle <bundle-name>
```

Only enable ongoing sync after review:

```bash
specfact project sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional
```

For the fuller walkthrough, see [Spec-Kit Journey Guide](../guides/speckit-journey.md).

### From OpenSpec

If you are moving existing OpenSpec project context into SpecFact-backed workflows:

```bash
specfact project sync bridge --adapter openspec --mode read-only --bundle <bundle-name> --repo .
specfact project devops-flow --stage develop --bundle <bundle-name>
```

Keep the first pass read-only until the imported state is reviewed. Then enable the sync mode you actually want.

For OpenSpec-specific context changes, see [OpenSpec OPSX Migration](openspec-migration.md).

## 5. Validate the migrated state

After any migration, run the checks that prove the new setup is usable:

```bash
specfact module list
specfact project health-check
specfact govern enforce sdd --bundle <bundle-name>
specfact spec validate --bundle <bundle-name>
```

Pick the bundle that matters most first. Once one representative bundle passes, roll the same checks across the rest of the repo.

## 6. Update team-facing surfaces

Do not stop at the CLI invocation itself. Migration is incomplete if these still point to the old world:

- CI workflows
- local shell scripts
- AI IDE prompt packs
- onboarding docs
- internal runbooks

The most common failure mode is that the repo has already migrated, but prompts and automation still tell people to use removed flat commands.

## Historical note

Older version-specific migrations such as the `0.16 -> 0.19` transition are historical only. They should not be used as the primary upgrade path for teams already operating on the `0.4x.y` line.

If you discover a repo that still depends on those assumptions, first update its command surface to the grouped model, then follow this guide.

## See also

- [specfact upgrade](../core-cli/upgrade.md)
- [Command Reference](../reference/commands.md)
- [CLI Reorganization Migration](migration-cli-reorganization.md)
- [OpenSpec OPSX Migration](openspec-migration.md)
- [Spec-Kit Journey Guide](../guides/speckit-journey.md)
- [Troubleshooting Guide](../guides/troubleshooting.md)
