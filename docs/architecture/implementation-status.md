---
layout: default
title: Architecture Implementation Status
permalink: /architecture/implementation-status/
description: Implemented vs planned architecture capabilities.
keywords: [implementation status, roadmap, architecture]
audience: [team, enterprise]
expertise_level: [advanced]
doc_owner: specfact-cli
tracks: [src/specfact_cli/**, openspec/**, ../specfact-cli-modules/packages/**]
last_reviewed: 2026-07-10
exempt: false
exempt_reason: ""
---

# Architecture Implementation Status

This page tracks implemented vs planned architecture capabilities.

## Implemented

- Module-first lazy command registry (`CommandRegistry`, module package discovery).
- Bridge adapter contract and adapter registry usage in sync flows.
- `ProjectBundle` and change-tracking model support in core models.
- Mode detection and explicit mode selection.

## Planned or Partial

- Shared architecture and traceability contracts remain planned in OpenSpec.
  - Source: `architecture-01-solution-layer`, `traceability-01-index-and-orphans`, and related follow-up changes.
- Older flat core command families such as `specfact architecture ...` and `specfact trace ...` are not canonical delivery targets. `specfact requirements ...` is instead an installed grouped surface owned by `nold-ai/specfact-requirements`.
- Canonical bundle-deep documentation is owned by the [modules documentation site](https://modules.specfact.io/).
  - Any future runtime implementation must be rescoped into grouped bundle-owned surfaces in `specfact-cli-modules`; core retains only shared models, schemas, and integration contracts.
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
