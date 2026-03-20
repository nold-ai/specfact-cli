---
layout: default
title: SpecFact CLI Documentation
description: Core CLI docs for runtime lifecycle, command topology, and official module integration.
permalink: /
---

# SpecFact CLI Documentation

**Docs Home**: `docs.specfact.io` is the canonical docs entry point for SpecFact.

**Core CLI**: this site owns runtime, lifecycle, registry, trust, command-topology, and architecture guidance for `specfact-cli`.

**Modules**: bundle-specific deep docs are canonically owned by `specfact-cli-modules` and are currently published at `https://modules.specfact.io/`.

This core docs site should answer two questions:

- How does the SpecFact platform work end to end?
- How do the official modules plug into the core CLI runtime?

Use the modules docs site when you need the in-depth workflows for backlog, project, code, spec, govern, adapters, or module authoring.

---

## What The Core CLI Owns

The `specfact-cli` repository owns the stable platform surface:

- `specfact init` for bootstrap and IDE setup.
- `specfact module` for lifecycle management of official and marketplace modules.
- `specfact upgrade` for CLI updates.
- Runtime contracts, module discovery, registry bootstrapping, publisher trust, and shared orchestration.
- The grouped command topology that mounts installed workflows under `project`, `backlog`, `code`, `spec`, and `govern`.

Recommended command entrypoints:
- `specfact backlog ceremony standup ...`
- `specfact backlog ceremony refinement ...`
- `specfact backlog verify-readiness --bundle <bundle-name>`

## What The Modules Docs Own

The canonical modules docs site covers the official bundle-specific deep guidance:

- backlog ceremonies, refinement, dependency analysis, delta workflows, and adapter specifics
- project bundle workflows and bridge synchronization
- spec validation, mock, backward-compatibility, and contract-test details
- govern enforcement, patch workflows, and bundle-focused runbooks
- module development, publishing, signing, registries, and marketplace operations

Canonical modules site: `https://modules.specfact.io/`

---

## Quick Start

```bash
# Install and bootstrap official bundles
uvx specfact-cli@latest
specfact init --profile solo-developer

# Analyze an existing repository
specfact code import my-project --repo .

# Snapshot project state
specfact project snapshot --bundle my-project

# Validate drift before implementation
specfact backlog verify-readiness --bundle <bundle-name>

# Validate contracts before release
specfact spec validate --bundle my-project
specfact govern enforce sdd my-project
```

Compatibility note: `specfact backlog daily ...` and `specfact backlog refine ...` remain available, but the preferred workflow entrypoints are `specfact backlog ceremony standup ...` and `specfact backlog ceremony refinement ...`.

## Current Command Groups

The live CLI currently exposes these top-level commands:

- `specfact init`
- `specfact module`
- `specfact upgrade`
- `specfact project ...`
- `specfact backlog ...`
- `specfact code ...`
- `specfact spec ...`
- `specfact govern ...`

Use [Reference: Command Topology](reference/commands.md) for the exact grouped surfaces and migration mapping.

## Core Docs Start Points

- **[Getting Started](getting-started/README.md)**
- **[Command Reference](reference/commands.md)**
- **[Reference Index](reference/README.md)**
- **[Architecture Reference](reference/architecture.md)**
- **[Module Categories](reference/module-categories.md)**
- **[Module Contracts](reference/module-contracts.md)**
- **[Installing Modules](guides/installing-modules.md)**

## Canonical Modules Docs Start Points

- **[Modules Docs Home](https://modules.specfact.io/)**
- **[Modules Command Reference](https://modules.specfact.io/reference/commands/)**
- **[Backlog Refinement Guide](https://modules.specfact.io/guides/backlog-refinement/)**
- **[Project DevOps Flow Guide](https://modules.specfact.io/guides/project-devops-flow/)**
- **[Module Development Guide](https://modules.specfact.io/guides/module-development/)**
- **[Publishing Modules Guide](https://modules.specfact.io/guides/publishing-modules/)**

## For Technical Readers

- **[Architecture Reference](reference/architecture.md)** - Current architecture model and interfaces
- **[Architecture Docs Index](architecture/README.md)** - Component graph, module system, data flow, state machines
- **[Architecture Implementation Status](architecture/implementation-status.md)** - Implemented vs planned features
- **[Architecture ADRs](architecture/adr/README.md)** - Decision records and template

## Additional Core Guides

- **[Installing Modules](guides/installing-modules.md)** - Install, list, uninstall, and upgrade modules
- **[Module Marketplace](guides/module-marketplace.md)** - Registry model, security checks, and discovery priority
- **[Marketplace Bundles](guides/marketplace.md)** - Official bundle ids, trust tiers, and dependency auto-install behavior
- **[Code Review Module](modules/code-review.md)** - Install and use the `nold-ai/specfact-code-review` scaffold under `specfact code review`
- **[Module Signing and Key Rotation](guides/module-signing-and-key-rotation.md)** - Signing and key management runbook
