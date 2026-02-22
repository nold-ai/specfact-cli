# SpecFact CLI Architecture Documentation

This folder contains comprehensive architecture documentation for SpecFact CLI.

## Overview

The SpecFact CLI architecture is built around three core layers:

1. **Specification Layer** - Plan bundles and protocol definitions
2. **Contract Layer** - Runtime contracts, static checks, and property tests  
3. **Enforcement Layer** - No-escape gates with budgets and staged enforcement

## Key Components

### System Component Graph

- **[Component Graph](component-graph.md)** - Visual representation of major components and their relationships

### Module Architecture

- **[Module System](module-system.md)** - Detailed module registry and lazy loading architecture

### State Machine Logic

- **[Workflow State Machines](state-machines.md)** - CLI workflow state transitions and protocol FSMs

### Interface Contracts

- **[Interface Contracts](interface-contracts.md)** - Public API contracts and module boundaries

### Data Flow

- **[Data Flow Analysis](data-flow.md)** - How data moves through the system

## Architecture Principles

1. **Contract-Driven Development** - Contracts as executable specifications
2. **Modular Design** - Lazy-loaded modules with explicit interfaces
3. **Dual-Mode Operation** - CI/CD automation vs CoPilot-assisted workflows
4. **Progressive Enhancement** - Shadow → Warn → Block enforcement stages
5. **Offline-First** - No external dependencies for core functionality

## Related Documentation

- [Main Architecture Reference](../../reference/architecture.md)
- [Module Contracts Reference](../../reference/module-contracts.md)
- [Bridge Registry](../../reference/bridge-registry.md)

## Discrepancies and Alignment Issues

- **[Discrepancies Report](discrepancies-report.md)** - Identified conflicts between docs, code, and specs
