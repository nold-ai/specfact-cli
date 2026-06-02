---
layout: default
title: Documentation Index
permalink: /documentation-index/
description: High-level index for the SpecFact core CLI docs and canonical modules docs handoff.
---

# SpecFact CLI Documentation

This repository owns the **core CLI** documentation set for SpecFact.
Use it as the canonical starting point when a user still needs orientation around what SpecFact is,
why it exists, what value it provides, and how to get started.

SpecFact is the AI-bloat defense and validation CLI for Python-first AI-assisted and brownfield
delivery. The core docs explain the product story, runtime lifecycle, bootstrap path, and the
handoff into deeper module-owned workflows.

Start with AI-bloat defense: run review, inspect the cleanup forecast and AI-bloat index, hand
remediation packets to your AI IDE, then re-run for proof. These signals are cleanup guidance, not
AI-authorship detection. Exact flags and JSON fields live in the
[AI bloat quickstart](https://modules.specfact.io/quickstart-ai-bloat/) and
[Code Review run guide](https://modules.specfact.io/bundles/code-review/run/).

For **module-specific deep functionality**, use the canonical modules docs site at
`https://modules.specfact.io/`. The canonical modules docs site owns the detailed guides for bundle
workflows, adapters, and module authoring.

## Core Docs Scope

Use this docs set for:

- AI-bloat defense first-contact onboarding and quickstart routing
- CLI bootstrap, lifecycle, and upgrade flows
- module registry, trust, and ownership boundaries
- overall workflow topology across `project`, `backlog`, `code`, `spec`, and `govern`
- runtime and architecture reference for the lean-core platform

## Modules Docs Scope

Use the canonical modules docs site for:

- cleanup forecast, remediation packet, and Code Review JSON schema details
- backlog refinement, ceremony, dependency-analysis, and delta workflows
- project bundle and bridge-sync runbooks
- spec bundle deep dives and govern bundle deep dives
- adapter-specific behavior and official bundle tutorials
- module development, publishing, signing, and marketplace operations

The canonical modules docs site is currently published at `https://modules.specfact.io/`.
This docs set keeps release-line overview and handoff content for bundle workflows while the canonical modules docs site carries the deep bundle-specific guidance.

If a modules page is ever used as a first-contact surface, it must explain that `modules.specfact.io`
is the deeper workflow layer and direct un-oriented users back to `docs.specfact.io` for the core
product story and fast-start path.

## Cross-site contract

- [Documentation URL contract (core and modules)](reference/documentation-url-contract.md) — linking rules vs `modules.specfact.io`

## Core Entry Points

- [Docs Home](index.md)
- [Getting Started](getting-started/README.md)
- [Command Reference](reference/commands.md)
- [Reference Index](reference/README.md)
- [Architecture Reference](architecture/overview.md)

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

- [Installing Modules](module-system/installing-modules.md)
- [Module Categories](reference/module-categories.md)
- [Module Contracts](reference/module-contracts.md)
- [Canonical modules docs site](https://modules.specfact.io/)
