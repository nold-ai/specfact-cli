# Documentation Verification Checklist

This checklist maps required discrepancy-report items to concrete documentation updates for `arch-08-documentation-discrepancies-remediation`.

## Required discrepancy items (pre-implementation mapping)

- [x] Item 1 (module system status): `docs/reference/architecture.md` module system section + `docs/architecture/module-system.md` overview.
- [x] Item 2 (BridgeAdapter interface mismatch): `docs/reference/architecture.md` adapter interface section + `docs/guides/adapter-development.md` BridgeAdapter methods.
- [x] Item 3 (operational modes gap): `docs/reference/architecture.md` operational modes section + `docs/architecture/implementation-status.md` planned vs implemented.
- [x] Item 4 (layer mismatch): `docs/reference/architecture.md` architecture layer overview + `docs/architecture/README.md` overview.
- [x] Item 5 (registry implementation details): `docs/reference/architecture.md` CommandRegistry details + `docs/architecture/module-system.md` discovery/load flow.
- [x] Item 6 (module package structure): `docs/guides/module-development.md` + cross-link in `docs/architecture/module-system.md`.
- [x] Item 7 (ToolCapabilities): `docs/guides/adapter-development.md` + `docs/reference/architecture.md` adapter selection section.
- [x] Item 11 (non-existent diagram components): `docs/architecture/component-graph.md` and related architecture diagrams.
- [x] Item 12 (outdated performance metrics): `docs/reference/architecture.md` performance claims revised/removed.
- [x] Item 13 (missing error handling docs): `docs/reference/architecture.md` error handling conventions section.
- [x] Item 17 (terminology inconsistency): standardize to `ProjectBundle` and `PlanBundle` where referencing models and files.
- [x] Item 18 (version references): normalize version references to current state or remove unstable version claims.
- [x] Item 19 (feature maturity mismatch): remove "transitioning/experimental" phrasing for module system.
- [x] Item 20 (no ADRs): add `docs/architecture/adr/README.md`, `docs/architecture/adr/template.md`, and first ADR.
- [x] Item 21 (missing module development guide): add `docs/guides/module-development.md` and nav link.
- [x] Item 22 (missing adapter development guide): update `docs/guides/adapter-development.md` and nav/discoverability links.

## Post-edit verification

- [x] No remaining "transitioning" references for module system in architecture docs.
- [x] No architecture diagrams claim non-existent "DevOps Adapters" component.
- [x] `BridgeAdapter` docs include `detect`, `import_artifact`, `export_artifact`, `load_change_tracking`, `save_change_tracking`.
- [x] Implementation status page links planned features to OpenSpec changes (including `architecture-01-solution-layer`).
- [x] Navigation includes ADR, module-development guide, adapter-development guide, and implementation status page.
