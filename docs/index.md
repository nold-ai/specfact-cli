---
layout: default
title: SpecFact CLI Documentation
description: SpecFact is the validation and alignment layer for software delivery. Start here for the core CLI story, first steps, and the handoff into module-deep workflows.
permalink: /
keywords: [specfact, core-cli, runtime, module-system, architecture]
audience: [solo, team, enterprise]
expertise_level: [beginner, intermediate, advanced]
doc_owner: specfact-cli
tracks:
  - src/specfact_cli/**
  - openspec/**
last_reviewed: 2026-03-29
exempt: false
exempt_reason: ""
---

# SpecFact CLI Documentation

SpecFact is the validation and alignment layer for software delivery.

This site is the canonical starting point for the core CLI story: what SpecFact is, why it exists,
what value you get from it, how to get started, and when to move into deeper bundle-owned workflows.

SpecFact does **not** include built-in AI. It pairs deterministic CLI commands with your chosen IDE
and copilot so fast-moving work has a stronger validation and alignment layer around it.

---

## What is SpecFact?

SpecFact helps you keep backlog intent, specifications, implementation, and validation from drifting
apart.

It is especially useful when:
- AI-assisted or “vibe-coded” work needs more rigor
- brownfield systems need trustworthy reverse-engineered understanding
- teams want to avoid the “I wanted X but got Y” delivery failure
- organizations need a path toward stronger shared policy enforcement

## Why does it exist?

Software delivery drifts in stages. Expectations change as they move from backlog language to
specification, from specification to implementation, and from implementation to review. SpecFact
exists to reduce that drift by giving you deterministic tooling for analysis, validation, and
alignment.

## Why should I use it?

Use SpecFact when you want faster delivery without losing validation, stronger brownfield
understanding before making changes, and less drift between backlog intent, specifications, and the
code that actually lands.

## What do I get?

With SpecFact, you get:
- deterministic local tooling instead of opaque cloud dependence
- a validation layer around AI-assisted delivery
- codebase analysis and sidecar validation for brownfield work
- stronger backlog/spec/code alignment
- a clean handoff from core runtime docs into module-deep workflows on `modules.specfact.io`

## How to get started

1. **[Installation](/getting-started/installation/)** - Install SpecFact CLI
2. **[5-Minute Quickstart](/getting-started/quickstart/)** - Get first value quickly
3. **[specfact init](/core-cli/init/)** - Bootstrap the core runtime and your local setup
4. **[Bootstrap Checklist](/module-system/bootstrap-checklist/)** - Verify bundle readiness

If you are new to SpecFact, start here before jumping into module-deep workflows.

## Choose Your Path

<div class="path-cards">
<div class="path-card">
<h3>Greenfield &amp; AI-assisted delivery</h3>
<p>Use SpecFact as the validation layer around fast-moving implementation work.</p>
<ul>
<li><a href="/getting-started/installation/">Installation</a></li>
<li><a href="/getting-started/quickstart/">5-Minute Quickstart</a></li>
<li><a href="/guides/contract-testing-workflow/">Contract Testing Workflow</a></li>
<li><a href="/guides/ai-ide-workflow/">AI IDE Workflow</a></li>
</ul>
</div>
<div class="path-card">
<h3>Brownfield and reverse engineering</h3>
<p>Use SpecFact to understand an existing system and then hand insight into spec-first workflows.</p>
<ul>
<li><a href="/getting-started/where-to-start/">Where to Start</a></li>
<li><a href="/guides/brownfield-journey/">Brownfield Journey</a></li>
<li>Initialize sidecar validation before running `specfact code validate sidecar run ...`.</li>
<li><a href="/guides/brownfield-roi/">Brownfield ROI</a></li>
<li><a href="/guides/brownfield-faq/">Brownfield FAQ</a></li>
</ul>
</div>
<div class="path-card">
<h3>Backlog to code alignment</h3>
<p>Use SpecFact when the main problem is drift between expectations, specs, and implementation.</p>
<ul>
<li>Start with a backlog-enabled profile such as `specfact init --profile backlog-team`.</li>
<li><a href="/guides/agile-scrum-workflows/">Agile &amp; Scrum Workflows</a></li>
<li><a href="https://modules.specfact.io/getting-started/tutorial-backlog-quickstart-demo/">Backlog Quickstart Demo</a></li>
<li><a href="https://modules.specfact.io/getting-started/tutorial-backlog-refine-ai-ide/">Backlog Refine with AI IDE</a></li>
<li><a href="https://modules.specfact.io/getting-started/tutorial-daily-standup-sprint-review/">Daily Standup and Sprint Review</a></li>
</ul>
</div>
<div class="path-card">
<h3>Team and policy enforcement</h3>
<p>Use core runtime, governance, and shared workflow conventions to scale rigor across teams.</p>
<ul>
<li><a href="/architecture/overview/">Architecture Overview</a></li>
<li><a href="/architecture/implementation-status/">Implementation Status</a></li>
<li><a href="/reference/commands/">Command Reference</a></li>
<li><a href="/reference/documentation-url-contract/">Core vs Modules URL Contract</a></li>
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

## Modules Documentation

`docs.specfact.io` is the default starting point. Move to the modules site when you need deeper
bundle-specific workflows, adapters, and authoring guidance.

- **[Modules Docs Home](https://modules.specfact.io/)** - Backlog, project, spec, govern
- **[Module Development](https://modules.specfact.io/authoring/module-development/)** - Build your own modules
- **[Publishing Modules](https://modules.specfact.io/authoring/publishing-modules/)** - Publish to marketplace

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
