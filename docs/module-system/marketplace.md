---
layout: default
title: Marketplace Bundles
nav_order: 23
permalink: /module-system/marketplace/
redirect_from:
  - /guides/marketplace/
description: Official SpecFact bundle IDs, trust tiers, and bundle dependency behavior.
keywords: [bundles, official modules, trust tiers]
audience: [solo, team, enterprise]
expertise_level: [intermediate]
---

# Marketplace Bundles

SpecFact publishes official workflow bundles in the dedicated modules repository:

- Registry repository: <https://github.com/nold-ai/specfact-cli-modules>
- Registry index: `registry/index.json`

## Official Bundles

These bundles are the primary installation path for workflow commands. Fresh installs start with lean core commands only (`init`, `module`, `upgrade`).

Install commands:

```bash
specfact module install nold-ai/specfact-project
specfact module install nold-ai/specfact-backlog
specfact module install nold-ai/specfact-codebase
specfact module install nold-ai/specfact-spec
specfact module install nold-ai/specfact-govern
specfact module install nold-ai/specfact-requirements
```

Bundle overview:

- `nold-ai/specfact-project`: grouped project workflows (`project`, `plan`, `import`, `sync`, `migrate`)
- `nold-ai/specfact-backlog`: grouped backlog workflows (`backlog`, `policy`, `backlog auth`)
- `nold-ai/specfact-codebase`: grouped code workflows (`analyze`, `drift`, `validate`, `repro`)
- `nold-ai/specfact-spec`: grouped spec workflows (`contract`, `api`, `sdd`, `generate`)
- `nold-ai/specfact-govern`: grouped governance workflows (`enforce`, `patch`)
- `nold-ai/specfact-requirements`: grouped requirements evidence workflows (`requirements`)

## Trust Tiers

Marketplace modules are validated with tier and publisher metadata:

- `official`: trusted publisher allowlist (`nold-ai`) with official verification output
- `community`: signed/verified community publisher module
- unsigned/local-dev: local or unsigned content, intended for development workflows only

When listing modules, official modules display an `[official]` marker.
When installing an official bundle, output confirms verification (for example `Verified: official (nold-ai)`).

## Bundle Dependencies

Some bundles declare bundle-level dependencies that are auto-installed:

- `nold-ai/specfact-spec` auto-installs `nold-ai/specfact-project`
- `nold-ai/specfact-govern` auto-installs `nold-ai/specfact-project`

If a dependency bundle is already installed, installer skips it and continues.

## First-Run and Refresh

On first run, select bundles with profiles or explicit install:

```bash
specfact init --profile solo-developer
specfact init --profile enterprise-full-stack
specfact init --install backlog,codebase
specfact init --install requirements
specfact init --install all
```

When you see a bundled-module refresh warning, reinitialize modules:

```bash
# project scope
specfact module init --scope project

# user scope
specfact module init
```

## See Also

- [Module Marketplace](module-marketplace.md)
- [Installing Modules](installing-modules.md)
- [Module Categories](../reference/module-categories.md)

> Modules docs handoff: this page remains in the core docs set as release-line overview content.
> Canonical bundle-specific deep guidance now lives in the canonical modules docs site, currently
> published at `https://modules.specfact.io/`.
