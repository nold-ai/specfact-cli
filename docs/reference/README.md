---
layout: default
title: Reference Documentation
permalink: /reference/
---

# Reference Documentation

Complete technical reference for the **core SpecFact CLI platform**.

This section documents the stable runtime, command topology, contracts, registry model, and ownership boundaries that `specfact-cli` owns directly.
For bundle-specific deep command guides and runbooks, use the canonical modules docs site at `https://modules.specfact.io/`.

## Core Reference Topics

- **[Commands](commands.md)** - Exact grouped command topology and migration mapping
- **[Command Syntax Policy](command-syntax-policy.md)** - Source-of-truth argument syntax conventions for docs
- **[Architecture](architecture.md)** - Technical design, module structure, and internals
- **[Authentication](authentication.md)** - Device code auth flows and token storage
- **[Debug Logging](debug-logging.md)** - Where and what is logged when using `--debug`
- **[Operational Modes](modes.md)** - CI/CD vs CoPilot modes
- **[Module Categories](module-categories.md)** - Category grouping model and canonical bundle assignments
- **[Module Contracts](module-contracts.md)** - Runtime-facing interfaces and ownership boundary
- **[Module Security](module-security.md)** - Marketplace/module integrity and publisher metadata
- **[Bridge Registry](bridge-registry.md)** - Registry-facing bridge converter declarations
- **[Directory Structure](directory-structure.md)** - Project structure and organization
- **[Feature Keys](feature-keys.md)** - Key normalization and formats
- **[Dependency Resolution](dependency-resolution.md)** - Module/pip dependency resolution behavior
- **[Thorough Codebase Validation](thorough-codebase-validation.md)** - Validation strategy overview

## Live Command Topology Summary

Current top-level commands in the shipped CLI:

- `specfact init`
- `specfact module`
- `specfact upgrade`
- `specfact project ...`
- `specfact backlog ...`
- `specfact code ...`
- `specfact spec ...`
- `specfact govern ...`

Selected current command examples:

- `specfact code import from-bridge --adapter speckit --repo .`
- `specfact project sync bridge --adapter github --bundle <bundle-name>`
- `specfact project import <markdown-file> --bundle <bundle-name>`
- `specfact spec validate --bundle <bundle-name>`
- `specfact spec generate-tests --bundle <bundle-name> --output tests/`
- `specfact govern enforce sdd [BUNDLE]`
- `specfact module install <name|namespace/name> [--scope user|project]`

## Ownership Boundary

- Core docs site: command topology, runtime lifecycle, contracts, registry, trust, architecture
- Canonical modules docs site: in-depth bundle commands, workflow tutorials, adapters, official module operations

See also:

- [Getting Started](../getting-started/README.md)
- [Documentation Index](../README.md)
- [Canonical modules docs site](https://modules.specfact.io/)
