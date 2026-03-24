---
layout: default
title: SpecFact CLI Documentation
description: Core CLI docs for runtime lifecycle, command topology, and official module integration.
permalink: /
---

# SpecFact CLI Documentation

SpecFact CLI is a contract-first Python CLI that keeps backlogs, specs, tests, and code in sync. This site covers the core platform - runtime, lifecycle, command topology, and architecture.

For module-specific workflows (backlog, governance, adapters), see [modules.specfact.io](https://modules.specfact.io/).

---

## Core Platform

The `specfact-cli` package provides the stable platform surface:

- **[specfact init](/core-cli/init/)** - Bootstrap and IDE setup
- **[specfact module](/core-cli/module/)** - Module lifecycle management
- **[specfact upgrade](/core-cli/upgrade/)** - CLI updates
- Runtime contracts, module discovery, registry bootstrapping, publisher trust, and shared orchestration

Installed modules mount workflows under `project`, `backlog`, `code`, `spec`, and `govern`.

## Get Started

1. **[Installation](/getting-started/installation/)** - Install SpecFact CLI
2. **[5-Minute Quickstart](/getting-started/quickstart/)** - First analysis in under 5 minutes
3. **[Bootstrap Checklist](/module-system/bootstrap-checklist/)** - Verify modules are installed

## Module System

- **[Installing Modules](/module-system/installing-modules/)** - Install and manage modules
- **[Module Marketplace](/module-system/module-marketplace/)** - Registry model and discovery
- **[Marketplace Bundles](/module-system/marketplace/)** - Official bundle IDs and trust tiers
- **[Custom Registries](/module-system/custom-registries/)** - Private registry configuration

## Architecture

- **[Architecture Overview](/architecture/overview/)** - Current architecture model
- **[Architecture Docs](/architecture/)** - Component graph, data flow, state machines
- **[Implementation Status](/architecture/implementation-status/)** - Implemented vs planned
- **[ADRs](/architecture/adr/)** - Architecture decision records

## Reference

- **[Command Reference](/reference/commands/)** - Full command surface
- **[Module Categories](/reference/module-categories/)** - Category taxonomy
- **[Module Contracts](/reference/module-contracts/)** - Contract interfaces
- **[Operational Modes](/core-cli/modes/)** - CI/CD and CoPilot modes
- **[Debug Logging](/core-cli/debug-logging/)** - Diagnostic logging

## Migration

- **[Migration Guide](/migration/migration-guide/)** - Version upgrade guidance
- **[0.16 to 0.19 Migration](/migration/migration-0.16-to-0.19/)** - Specific version steps
- **[CLI Reorganization](/migration/migration-cli-reorganization/)** - Command surface changes
- **[OpenSpec Migration](/migration/openspec-migration/)** - OPSX workflow migration

## Modules Documentation

For in-depth module workflows, visit the canonical modules site:

- **[Modules Docs Home](https://modules.specfact.io/)** - Backlog, project, spec, govern
- **[Module Development](https://modules.specfact.io/guides/module-development/)** - Build your own modules
- **[Publishing Modules](https://modules.specfact.io/guides/publishing-modules/)** - Publish to marketplace
