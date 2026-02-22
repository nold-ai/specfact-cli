---
layout: default
title: ADR-0001 Module-First Architecture
permalink: /architecture/adr/0001-module-first-architecture/
description: Decision record for lazy-loaded module-first CLI architecture.
---

# ADR-0001: Module-First Architecture

- Status: Accepted
- Date: 2026-02-22
- Deciders: SpecFact maintainers
- Related OpenSpec changes: `arch-01-cli-modular-command-registry`, `arch-02-module-package-separation`

## Context

Hard-wired command imports increased startup cost, complicated extension work, and made module lifecycle management difficult.

## Decision

Adopt a module-first architecture backed by `CommandRegistry`:

- Register commands by metadata and lazy loader.
- Discover module packages via `module-package.yaml`.
- Load Typer apps on first command invocation and cache results.
- Keep compatibility shims during migration windows.

## Consequences

- Faster startup and improved command isolation.
- Clear extension surface for module authors.
- Additional manifest and lifecycle governance requirements.
