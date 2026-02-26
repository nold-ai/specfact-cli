---
layout: default
title: Architecture Docs Index
description: Index of SpecFact CLI architecture deep-dive documents.
permalink: /architecture/
---

# SpecFact CLI Architecture Documentation

Architecture documents in this folder describe the current implementation and clearly separate planned features.

## Current Architecture View

- Module-first command system is production-ready.
- Command loading is lazy via `CommandRegistry`.
- Bridge adapters integrate external systems through the `BridgeAdapter` contract.
- Contract-first validation remains the primary engineering model.

## Architecture Documents

- [Component Graph](component-graph.md)
- [Module System](module-system.md)
- [Workflow State Machines](state-machines.md)
- [Interface Contracts](interface-contracts.md)
- [Data Flow](data-flow.md)
- [Implementation Status](implementation-status.md)
- [Architecture Decision Records (ADR)](adr/README.md)
- [Discrepancies Report](discrepancies-report.md)

## Related Reference

- [Main Architecture Reference](../reference/architecture.md)
- [Bridge Registry](../reference/bridge-registry.md)
- [Module Development Guide](../guides/module-development.md)
- [Adapter Development Guide](../guides/adapter-development.md)
