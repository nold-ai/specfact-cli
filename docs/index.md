---
layout: default
title: SpecFact CLI Documentation
description: Point SpecFact at your code, get a scored review and a fix list in minutes — then go deeper into backlog, specs, and CI when you need to.
permalink: /
keywords: [specfact, core-cli, quickstart, code review, onboarding]
audience: [solo, team, enterprise]
expertise_level: [beginner, intermediate, advanced]
doc_owner: specfact-cli
tracks:
  - src/specfact_cli/**
  - openspec/**
last_reviewed: 2026-04-02
exempt: false
exempt_reason: ""
---

# SpecFact CLI Documentation

**Review AI-assisted code against your own contracts.**
**Catch drift before it reaches PR or main.**

Point SpecFact at your repo, get a scored review with file-level findings, then go deeper into
backlog, specs, and CI when you need more control.

```bash
uvx specfact-cli init --profile solo-developer
uvx specfact-cli code review run --path . --scope full
```

You should see a **Verdict**, a **Score**, and a list of findings on a real repo. That is the
fastest way to see SpecFact on existing code. [Read the full quickstart →](/getting-started/quickstart/)

SpecFact does **not** include built-in AI. It pairs deterministic CLI commands with your chosen IDE and copilot so fast-moving work has a stronger validation and alignment layer around it.

**SpecFact is the validation and alignment layer for software delivery.**

---

## What is SpecFact?

SpecFact helps you keep backlog intent, specifications, implementation, and validation from drifting apart. It supports spec-first handoffs with **OpenSpec** and spec-kit-style workflows so brownfield and AI-assisted teams can keep backlog language, specs, and code aligned.

It is especially useful when:

- AI-assisted or “vibe-coded” work needs more rigor
- brownfield and legacy code need trustworthy reverse-engineered understanding of existing systems
- teams want to avoid the “I wanted X but got Y” delivery failure
- organizations need a path toward stronger shared policy enforcement

## Why does it exist?

SpecFact exists because backlog/spec/code drift is expensive: teams ship the wrong thing, AI-assisted changes skip validation, and policy enforcement breaks down across IDEs and CI. SpecFact gives you a default starting point before you jump into module-deep workflows on the modules site.

## Why should I use it?

Use SpecFact when you want faster delivery without losing validation, stronger brownfield understanding before making changes, and less drift between backlog intent, specifications, and the code that actually lands.

## What do I get?

With SpecFact, you get:

- deterministic local tooling instead of opaque cloud dependence
- a validation layer around AI-assisted delivery
- codebase analysis and sidecar validation for brownfield work
- stronger backlog/spec/code alignment
- a clean handoff from this site into module-deep workflows on [modules.specfact.io](https://modules.specfact.io/)

## How to get started

1. **[Installation](/getting-started/installation/)** — uvx (no install) or pip (persistent CLI)
2. **[5-Minute Quickstart](/getting-started/quickstart/)** — First commands on a repo
3. **[specfact init](/core-cli/init/)** — Profiles, bundles, and IDE setup
4. **[Bootstrap Checklist](/module-system/bootstrap-checklist/)** — Verify bundle readiness

## Choose your path

<div class="path-cards">
<div class="path-card">
<h3>See what&apos;s wrong with your code right now</h3>
<p>Run a scored code review on an existing repo with uvx, then iterate.</p>
<ul>
<li><a href="/getting-started/quickstart/">5-Minute Quickstart</a></li>
<li><a href="/getting-started/installation/">Installation</a></li>
<li><a href="/guides/contract-testing-workflow/">Contract Testing Workflow</a></li>
</ul>
</div>
<div class="path-card">
<h3>Set up IDE slash-command workflows</h3>
<p>Install the CLI, bootstrap bundles, then export prompts for Cursor, VS Code, and other IDEs.</p>
<ul>
<li><a href="/core-cli/init/">specfact init</a></li>
<li><a href="/guides/ai-ide-workflow/">AI IDE Workflow</a></li>
<li><a href="/guides/ide-integration/">IDE Integration</a></li>
</ul>
</div>
<div class="path-card">
<h3>Add a pre-commit or CI gate</h3>
<p>Wire SpecFact into local hooks or GitHub Actions for repeatable checks.</p>
<ul>
<li><a href="/getting-started/installation/#more-options">GitHub Action example</a></li>
<li><a href="/guides/contract-testing-workflow/">Contract Testing Workflow</a></li>
<li><a href="/reference/commands/">Command Reference</a></li>
</ul>
</div>
</div>

## Core Platform

The `specfact-cli` package provides the stable platform surface:

- **[specfact init](/core-cli/init/)** — Bootstrap bundles and optional IDE setup
- **[specfact module](/core-cli/module/)** — Install, enable, and upgrade workflow modules
- **[specfact upgrade](/core-cli/upgrade/)** — CLI self-update

Installed modules add command groups such as `project`, `backlog`, `code`, `spec`, and `govern`. Deeper bundle docs live on [modules.specfact.io](https://modules.specfact.io/).

## Modules Documentation

`docs.specfact.io` is the default starting point and the **canonical starting point for the core CLI story**
for first-time readers on this site. Move to the modules site when you need **module-deep workflows**,
bundle-specific adapters, and authoring guidance.

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
