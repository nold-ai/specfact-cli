# Design: Bridge Registry for Cross-Module Service Interoperability

## Context

`arch-04-core-contracts-interfaces` establishes module IO contracts and core/module isolation, but it does not define how modules publish reusable schema converters for external services. The internal analysis dated 2026-02-08 and the implementation plan identify this as the next architectural step (arch-05) required before marketplace-grade module decoupling.

Current state:

- Service mapping logic is module-local and not discoverable through a common registry contract.
- Module manifests support dependencies and core compatibility, but not converter bridge declarations.
- Core must stay decoupled from module internals while still enabling dynamic bridge usage.

## Goals / Non-Goals

**Goals:**

- Introduce a registry-level bridge abstraction (`SchemaConverter`, `BridgeRegistry`) for bidirectional schema conversion.
- Make bridge declarations manifest-driven (`service_bridges`) and validated at module registration time.
- Keep core/module isolation intact: no hardcoded core imports of module adapter implementations.
- Deliver backlog reference converters (ADO, Jira, Linear, GitHub) as first adopters.
- Document extension points for custom enterprise bridge mappings.

**Non-Goals:**

- Cryptographic signature validation and trust chain (arch-06).
- Marketplace install/uninstall UX and remote registry APIs (marketplace-01/02).
- Per-module Python environment isolation.
- Breaking existing module registration APIs.

## Decisions

### Decision 1: Protocol + Registry Pattern for Bridges

**Choice:** Define a `SchemaConverter` Protocol and a centralized `BridgeRegistry` with `register_converter()` and `get_converter()` methods.

**Rationale:**

- Preserves plugin-style extensibility already used in module discovery.
- Keeps conversion contract explicit and testable.
- Avoids hardcoded adapter branching in sync/backlog flows.

**Alternatives considered:**

- Inline converter logic in each command path: duplicates logic and increases coupling.
- Abstract base class with strict inheritance: less flexible than protocol-based structural typing.

### Decision 2: Manifest-Driven Bridge Registration

**Choice:** Extend `module-package.yaml` metadata with `service_bridges` entries containing bridge id, description, and converter class path.

**Rationale:**

- Keeps registration declarative and discoverable.
- Allows lifecycle validation before registration.
- Supports future marketplace metadata verification without changing runtime architecture.

**Alternatives considered:**

- Hardcoded module-specific bridge lists in core: violates core isolation.
- Runtime classpath scanning without manifest declarations: less deterministic and harder to validate.

### Decision 3: Graceful Degradation on Bridge Registration Failures

**Choice:** If a bridge declaration is invalid or import fails, skip that bridge with warning/debug logging; do not crash CLI startup.

**Rationale:**

- Matches existing module lifecycle behavior for compatibility/dependency issues.
- Supports parallel module evolution without blocking unrelated workflows.

**Alternatives considered:**

- Fail-fast for any invalid bridge: safer but too disruptive for modular incremental rollout.

### Decision 4: Backlog Module as Reference Bridge Provider

**Choice:** Implement first converter set in backlog module (`ado`, `jira`, `linear`, `github`) and register through metadata.

**Rationale:**

- Backlog already contains major external service integration surface.
- Provides concrete pattern for future modules to follow.

## Risks / Trade-offs

- **Risk:** Converter class import paths drift from code layout.
  - **Mitigation:** Add registration-time path validation tests and clear startup warnings.
- **Risk:** Bridge IDs collide across modules.
  - **Mitigation:** Deterministic registration rules and explicit duplicate handling with warnings.
- **Risk:** Converter logic divergence across modules.
  - **Mitigation:** Publish docs and contract tests against the `SchemaConverter` protocol.
- **Trade-off:** Non-fatal bridge failures improve resilience but can hide misconfiguration.
  - **Mitigation:** Elevated warning logs and dedicated validation tests in CI.

## Migration Plan

1. Add bridge registry and converter protocol with unit tests.
2. Extend manifest schema and parser for `service_bridges` metadata.
3. Add lifecycle registration hooks for bridge declaration validation and registry insertion.
4. Add backlog reference converters and manifest declarations.
5. Update docs and run quality gates.

Rollback strategy:

- Remove bridge registration calls from module lifecycle.
- Remove `service_bridges` metadata usage while keeping manifests backward compatible.
- Keep backlog adapters functional through existing direct paths until reintroduced.

## Open Questions

- Should duplicate bridge IDs fail registration or use first-wins semantics with warnings?
- Should converter registration support versioned bridge contracts in arch-06 or later?
- Should enterprise custom mappings be loaded at bridge-level registration or adapter execution time?

## Sequence Diagram: Manifest-Driven Bridge Registration

```text
CLI Startup -> ModuleRegistry: discover module packages
ModuleRegistry -> ManifestParser: parse module-package.yaml
ManifestParser --> ModuleRegistry: metadata (+service_bridges)
ModuleRegistry -> BridgeRegistry: register_converter(bridge_id, converter_class)
BridgeRegistry --> ModuleRegistry: success or warning
ModuleRegistry --> CLI Startup: module commands + bridges available
CLI Command -> BridgeRegistry: get_converter(service_id)
BridgeRegistry --> CLI Command: SchemaConverter implementation
```
