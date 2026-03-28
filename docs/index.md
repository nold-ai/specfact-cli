---
layout: default
title: SpecFact CLI Documentation
description: Core CLI docs for runtime lifecycle, command topology, and official module integration.
permalink: /
keywords: [specfact, core-cli, runtime, module-system, architecture]
audience: [solo, team, enterprise]
expertise_level: [beginner, intermediate, advanced]
---

# SpecFact CLI Documentation

SpecFact CLI is a contract-first Python CLI that keeps backlogs, specs, tests, and code in sync. This site covers the core platform - runtime, lifecycle, command topology, and architecture.

For module-specific workflows (backlog, governance, adapters), see [modules.specfact.io](https://modules.specfact.io/).

Use the shared portal navigation to move between **Docs Home**, **Core CLI**, and **Modules** without changing interaction patterns.

---

## Find Your Path

<div class="path-cards">
<div class="path-card">
<h3>New User</h3>
<p>Start with the core install and bootstrap path before adding workflow bundles.</p>
<ul>
<li><a href="/getting-started/where-to-start/">Where to Start</a></li>
<li><a href="/getting-started/installation/">Installation</a></li>
<li><a href="/getting-started/quickstart/">5-Minute Quickstart</a></li>
<li><a href="/core-cli/init/">specfact init</a></li>
</ul>
</div>
<div class="path-card">
<h3>Team Lead</h3>
<p>Set up shared runtime conventions, IDE flows, and team-level operating guidance.</p>
<ul>
<li><a href="/guides/ai-ide-workflow/">AI IDE Workflow</a></li>
<li><a href="/guides/agile-scrum-workflows/">Agile &amp; Scrum Workflows</a></li>
<li><a href="/guides/team-collaboration-workflow/">Team Collaboration Workflow</a></li>
<li><a href="/reference/documentation-url-contract/">Core vs Modules URL Contract</a></li>
</ul>
</div>
<div class="path-card">
<h3>Platform Owner</h3>
<p>Use the architecture and registry references to operate SpecFact as shared platform infrastructure.</p>
<ul>
<li><a href="/architecture/overview/">Architecture Overview</a></li>
<li><a href="/architecture/implementation-status/">Implementation Status</a></li>
<li><a href="/reference/commands/">Command Reference</a></li>
<li><a href="/reference/bridge-registry/">Bridge Registry</a></li>
</ul>
</div>
<div class="path-card">
<h3>Module Operator</h3>
<p>Manage installed bundles from core docs, then hand off to modules docs for bundle-owned workflows.</p>
<ul>
<li><a href="/module-system/installing-modules/">Installing Modules</a></li>
<li><a href="/module-system/module-marketplace/">Module Marketplace</a></li>
<li><a href="https://modules.specfact.io/">Modules Docs Home</a></li>
<li><a href="https://modules.specfact.io/authoring/module-development/">Module Development</a></li>
</ul>
</div>
</div>

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

## Workflows

- **[AI IDE Workflow](/guides/ai-ide-workflow/)** - Bootstrap editor integrations around the CLI
- **[Agile & Scrum Workflows](/guides/agile-scrum-workflows/)** - Team routines anchored in the core runtime
- **[Command Chains](/guides/command-chains/)** - Compose core and module commands safely
- **[Contract Testing Workflow](/guides/contract-testing-workflow/)** - Core validation and contract-first delivery

## Reference

- **[Command Reference](/reference/commands/)** - Full command surface
- **[Module Categories](/reference/module-categories/)** - Category taxonomy
- **[Module Contracts](/reference/module-contracts/)** - Contract interfaces
- **[Operational Modes](/core-cli/modes/)** - CI/CD and CoPilot modes
- **[Debug Logging](/core-cli/debug-logging/)** - Diagnostic logging

## Migration

- **[Migration Guide](/migration/migration-guide/)** - Version upgrade guidance
- **[CLI Reorganization](/migration/migration-cli-reorganization/)** - Command surface changes
- **[OpenSpec Migration](/migration/openspec-migration/)** - OPSX workflow migration

## Modules Documentation

For in-depth module workflows, visit the canonical modules site:

- **[Modules Docs Home](https://modules.specfact.io/)** - Backlog, project, spec, govern
- **[Module Development](https://modules.specfact.io/authoring/module-development/)** - Build your own modules
- **[Publishing Modules](https://modules.specfact.io/authoring/publishing-modules/)** - Publish to marketplace
