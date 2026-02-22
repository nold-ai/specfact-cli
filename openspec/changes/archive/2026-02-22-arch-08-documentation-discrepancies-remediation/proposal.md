# Change: Architecture Documentation Discrepancies Remediation

## Why

The architecture discrepancies report (`docs/architecture/discrepancies-report.md`) identified 25 conflicts between documentation, codebase, and OpenSpec: module system described as "transitioning" while code is production-ready, incomplete BridgeAdapter and layer documentation, missing development guides, and spec–code gaps (e.g. architecture commands specified but not yet implemented). These cause confusion for contributors and understate feature readiness. Remediating docs and aligning specs with current capabilities will restore consistency and improve developer experience without changing runtime behavior.

## What Changes

- **UPDATE** `docs/reference/architecture.md` and `docs/architecture/*`: Reflect module system as production-ready since v0.27; document full BridgeAdapter interface (including `load_change_tracking` / `save_change_tracking`); describe actual layer structure (Adapter, Analysis, Module layers in addition to Specification/Contract/Enforcement); clarify operational modes (current implementation vs planned); add CommandRegistry implementation details and required module package structure.
- **UPDATE** Documentation: Add ToolCapabilities model and adapter selection; document error handling patterns and conventions; update or remove outdated performance metrics; fix terminology (Project Bundle / Plan Bundle); standardize version references; remove or correct Mermaid diagrams that reference non-existent components (e.g. DevOps Adapters).
- **NEW** ADR template and initial ADRs: Create `docs/architecture/adr/` with template and at least one ADR for a major decision (e.g. module-first architecture).
- **NEW** Module development guide: `docs/guides/module-development.md` (or equivalent) with required structure, `module-package.yaml` schema, naming conventions, and patterns.
- **NEW** Adapter development guide: Extend or add `docs/guides/adapter-development.md` (or integrate into existing creating-custom-bridges) with BridgeAdapter interface, ToolCapabilities, and examples.
- **ALIGN** Specs with current state: Where specs describe not-yet-implemented behavior (e.g. architecture derive/validate/trace, protocol FSM engine), ensure docs clearly state "planned" or "specified in OpenSpec change architecture-01" and document current limitations (change tracking, protocol validation) in a single place (e.g. docs/architecture/implementation-status.md or equivalent).

No new application code or CLI behavior; documentation and spec-doc alignment only.

## Capabilities

- **documentation-alignment**: Architecture and reference docs accurately reflect current implementation (module system status, BridgeAdapter, layers, modes, CommandRegistry, module structure, ToolCapabilities, error handling, performance, terminology, versions, diagrams).
- **adr-template**: ADR template and initial ADRs for major architectural decisions, discoverable from docs.
- **module-development-guide**: Single guide describing how to develop and package new modules (structure, manifest, commands, contracts).
- **adapter-development-guide**: Guide for implementing adapters (BridgeAdapter interface, change tracking, ToolCapabilities, examples).
- **implementation-status-docs**: Documented current limitations and spec–code alignment (what is implemented vs planned), with pointers to relevant OpenSpec changes.

## Impact

- **Affected documentation**:
  - `docs/reference/architecture.md`
  - `docs/architecture/` (README, module-system, component-graph, data-flow, state-machines, interface-contracts, discrepancies-report.md)
  - New: `docs/architecture/adr/` (template + initial ADR(s)), `docs/architecture/implementation-status.md` (or equivalent)
  - `docs/guides/` (module-development, adapter-development or extended creating-custom-bridges)
  - `docs/_layouts/default.html` (navigation for new pages)
  - `README.md` / `docs/index.md` if terminology or version references are updated
- **Affected specs**: Optional deltas in existing changes (e.g. architecture-01) to add "current implementation status" notes; no new runtime contracts.
- **Backward compatibility**: N/A (documentation only).
- **Rollback plan**: Revert documentation commits.

**Documentation impact (per config.yaml):** All changes are documentation-only and improve accuracy and discoverability at https://docs.specfact.io. New pages will have correct Jekyll front-matter and be linked from `docs/_layouts/default.html`.

## Clarifications for implementation

- **Operational modes**: Remediation will document current state (detector exists; mode-specific behavior as planned) rather than implement new mode logic.
- **Architecture commands**: Will not implement `specfact architecture derive|validate|trace` in this change; docs will state they are specified in `architecture-01-solution-layer` and not yet implemented.
- **Protocol FSM / change tracking**: Will document current limitations and point to relevant OpenSpec changes; no FSM engine or full change-tracking implementation in this change.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #291
- **Issue URL**: https://github.com/nold-ai/specfact-cli/issues/291
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: synced-2026-02-22
