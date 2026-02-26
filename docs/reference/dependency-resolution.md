---
layout: default
title: Dependency resolution
permalink: /reference/dependency-resolution/
description: How SpecFact resolves module and pip dependencies before install and how to bypass or override.
---

# Dependency resolution

SpecFact resolves dependencies for marketplace modules before installing. This reference describes how resolution works, conflict detection, and the flags that change behavior.

## Overview

When you run `specfact module install <module-id>` (without `--skip-deps`), the CLI:

1. Discovers all currently available modules (bundled + already installed) plus the module being installed.
2. Reads each module’s `module_dependencies` and `pip_dependencies` from their manifests.
3. Runs the dependency resolver to compute a consistent set of versions.
4. If conflicts are found, install fails unless you pass `--force`.

Resolution is used only for **marketplace** installs. Bundled and custom modules do not go through this resolution step for their dependencies.

## Resolver behavior

- **Preferred**: If `pip-tools` is available, the resolver uses it to resolve pip dependencies and align versions across modules.
- **Fallback**: If `pip-tools` is not available, a basic resolver aggregates `pip_dependencies` and `module_dependencies` without deep conflict detection.
- **Conflict detection**: Incompatible version constraints (e.g. two modules requiring different versions of the same pip package) are reported with clear errors. Install then fails unless `--force` is used.

## Install flags

| Flag          | Effect |
|---------------|--------|
| (none)        | Resolve dependencies; fail on conflicts. |
| `--skip-deps` | Do not resolve dependencies. Install only the requested module. Use when you manage dependencies yourself or want a minimal install. |
| `--force`     | If resolution reports conflicts, proceed anyway. Use with care (e.g. known-compatible versions or local overrides). |

`--force` does not disable integrity or trust checks; it only overrides dependency conflict failure.

## Bypass options

- **Skip resolution**: `specfact module install specfact/backlog --skip-deps` installs only `specfact/backlog` and does not pull or check its `pip_dependencies` / `module_dependencies`.
- **Override conflicts**: `specfact module install specfact/backlog --force` proceeds even when the resolver reports conflicts. Enable/disable and dependency-aware cascades may still use `--force` where applicable.

## See also

- [Installing modules](../guides/installing-modules.md) – Install behavior and dependency resolution section.
- [Module marketplace](../guides/module-marketplace.md) – Registry and security model.
