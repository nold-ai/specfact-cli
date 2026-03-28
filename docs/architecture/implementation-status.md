---
layout: default
title: Architecture Implementation Status
permalink: /architecture/implementation-status/
description: Implemented vs planned architecture capabilities.
keywords: [implementation status, roadmap, architecture]
audience: [team, enterprise]
expertise_level: [advanced]
---

# Architecture Implementation Status

This page tracks implemented vs planned architecture capabilities.

## Implemented

- Module-first lazy command registry (`CommandRegistry`, module package discovery).
- Bridge adapter contract and adapter registry usage in sync flows.
- `ProjectBundle` and change-tracking model support in core models.
- Mode detection and explicit mode selection.

## Planned or Partial

- `specfact architecture derive|validate|trace` command family is planned.
  - Source: OpenSpec `architecture-01-solution-layer`.
- Protocol FSM runtime engine is partial (models/specs exist; full execution engine/guards are planned).
  - Source: OpenSpec `architecture-01-solution-layer` and dependent validation changes.
- Change tracking is adapter-dependent and not uniformly complete across all backlog providers.

## Known limitations

- Documentation/specs may define forward-looking behavior before command implementation lands.
- Not all adapters implement the same depth for proposal/change-tracking persistence.

## References

- [Architecture Reference](../architecture/overview.md)
- [Architecture Docs Index](README.md)
- [Discrepancies Report](discrepancies-report.md)
