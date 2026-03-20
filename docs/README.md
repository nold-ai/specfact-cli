---
layout: default
title: Documentation Index
permalink: /documentation-index/
description: High-level index for the SpecFact core CLI docs and canonical modules docs handoff.
---

# SpecFact CLI Documentation

This repository owns the **core CLI** documentation set for SpecFact.
It explains the overall process of using SpecFact CLI, the platform runtime, and how official modules integrate into the grouped command surface.

For **module-specific deep functionality**, use the canonical modules docs site at `https://modules.specfact.io/`.
The canonical modules docs site owns the detailed guides for bundle workflows, adapters, and module authoring.

## Core Docs Scope

Use this docs set for:

- CLI bootstrap, lifecycle, and upgrade flows
- module registry, trust, and ownership boundaries
- overall workflow topology across `project`, `backlog`, `code`, `spec`, and `govern`
- runtime and architecture reference for the lean-core platform

## Modules Docs Scope

Use the canonical modules docs site for:

- backlog refinement, ceremony, dependency-analysis, and delta workflows
- project bundle and bridge-sync runbooks
- spec bundle deep dives and govern bundle deep dives
- adapter-specific behavior and official bundle tutorials
- module development, publishing, signing, and marketplace operations

The canonical modules docs site is currently published at `https://modules.specfact.io/`.
This docs set keeps release-line overview and handoff content for bundle workflows while the canonical modules docs site carries the deep bundle-specific guidance.

## Core Entry Points

- [Docs Home](index.md)
- [Getting Started](getting-started/README.md)
- [Command Reference](reference/commands.md)
- [Reference Index](reference/README.md)
- [Architecture Reference](reference/architecture.md)

## Current Core Command Topology

The live CLI groups installed workflow commands by category:

- `specfact init`
- `specfact module`
- `specfact upgrade`
- `specfact project ...`
- `specfact backlog ...`
- `specfact code ...`
- `specfact spec ...`
- `specfact govern ...`

Preferred backlog workflow entrypoints:

- `specfact backlog ceremony standup ...`
- `specfact backlog ceremony refinement ...`
- `specfact backlog verify-readiness --bundle <bundle-name>`
- `specfact backlog analyze-deps --bundle <bundle-name>`

Compatibility note: `specfact backlog daily ...` and `specfact backlog refine ...` remain available, but the ceremony forms are the preferred command path.

What the backlog ceremony and readiness commands do in practice:
- Converts team working agreements (DoR, DoD, flow/PI readiness) into deterministic checks.
- Flags exact readiness gaps per backlog item with actionable evidence pointers.
- Runs structured ceremony workflows against live backlog data.

Start with:
- `specfact backlog ceremony standup --help`
- `specfact backlog verify-readiness --bundle <bundle-name>`
- `specfact backlog refine --help`

## Core vs Modules Navigation

- **Core CLI docs**: runtime, lifecycle, contracts, command topology, architecture
- **Canonical modules docs site**: bundle-specific tutorials, command details, adapters, module authoring

### Recommended next reads

- [Installing Modules](guides/installing-modules.md)
- [Module Categories](reference/module-categories.md)
- [Module Contracts](reference/module-contracts.md)
- [Canonical modules docs site](https://modules.specfact.io/)
