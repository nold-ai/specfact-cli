---
layout: default
title: Discrepancies Report
permalink: /architecture/discrepancies-report/
---

# SpecFact CLI Architecture Discrepancies Report

## Executive Summary

This report originally captured architecture documentation and spec/code discrepancies.
It is now updated after remediation work completed in OpenSpec change
`arch-08-documentation-discrepancies-remediation` (2026-02-22).

- Scope of this report: architecture docs/spec/code alignment status
- Current status: most documentation discrepancies are resolved
- Remaining gaps: implementation gaps that are intentionally documented as planned/partial

## Baseline and Sources

- Remediation change: `openspec/changes/arch-08-documentation-discrepancies-remediation/`
- Verification checklist: `openspec/changes/arch-08-documentation-discrepancies-remediation/DOC_VERIFICATION_CHECKLIST.md`
- Architecture reference: `docs/reference/architecture.md`
- Architecture docs index: `docs/architecture/README.md`
- Implementation status: `docs/architecture/implementation-status.md`

## Discrepancy Status Matrix

Legend:

- `Resolved`: discrepancy has been remediated and documented accurately
- `Partial`: discrepancy is reduced/clarified, but implementation is still incomplete
- `Open`: discrepancy remains and requires additional implementation/spec work

1. Module system implementation vs docs: `Resolved`
2. Bridge adapter interface mismatch: `Resolved`
3. Operational modes docs gap: `Resolved` (documented current limits and planned behavior)
4. Architecture layer mismatch: `Resolved`
5. Command registry implementation detail gap: `Resolved`
6. Module package structure missing in docs: `Resolved`
7. Adapter capabilities docs gap: `Resolved`
8. Architecture derive command missing in implementation: `Open` (proposal now split/rescoped; no flat core command is authorized)
9. Change tracking implementation partial vs spec breadth: `Partial`
10. Protocol FSM implementation minimal vs detailed spec: `Partial`
11. Diagram references to non-existent components: `Resolved`
12. Outdated performance metrics: `Resolved` (outdated hard claims removed/tempered)
13. Missing error handling documentation: `Resolved`
14. Missing architecture module vs architecture specs: `Open` (runtime delivery must be reassigned into canonical grouped bundle ownership)
15. Incomplete bridge adapter implementations vs references: `Partial`
16. Protocol validation gaps: `Partial`
17. Terminology inconsistencies: `Resolved`
18. Version reference inconsistencies: `Resolved`
19. Feature maturity mismatch (experimental vs production-ready): `Resolved`
20. No ADR records: `Resolved`
21. Missing module development guide: `Resolved`
22. Missing adapter development guide: `Resolved`
23. Missing architecture commands: `Open` (the old flat command family is no longer the target shape)
24. Partial change tracking coverage: `Partial`
25. Incomplete protocol support: `Partial`

## Resolved in arch-08

The following remediation outputs are now present:

- Updated architecture reference with accurate module-first status and adapter contract details.
- Updated architecture pages (`module-system`, `component-graph`, `data-flow`, `state-machines`, `interface-contracts`).
- Added ADR structure and initial ADR:
  - `docs/architecture/adr/README.md`
  - `docs/architecture/adr/template.md`
  - `docs/architecture/adr/0001-module-first-architecture.md`
- Added implementation status page for implemented vs planned capabilities.
- Added/updated development guides:
  - `docs/guides/module-development.md`
  - `docs/guides/adapter-development.md`
- Navigation and discoverability updates in:
  - `docs/_layouts/default.html`
  - `docs/index.md`

## Remaining Gaps (Not Doc-Only)

These items are not documentation mismatches anymore; they are implementation/spec-delivery work:

1. `specfact architecture derive|validate|trace` command family is still planned.
   - That original flat command shape is now stale relative to the lean-core plus bundles architecture.
   - Any future delivery must be split into core-owned contracts and grouped bundle-owned runtime commands in `specfact-cli-modules`.
2. Protocol FSM execution/validation engine is still partial.
3. Change tracking depth is not yet uniform across all adapters/providers.
4. Some architecture-level capabilities remain defined in OpenSpec before runtime delivery.

## Follow-Up Plan

### Phase A: Architecture command delivery

- Rescope `architecture-01-solution-layer` and related changes onto canonical grouped command owners before implementation work starts.
- Keep shared contracts and schema work in core; deliver any runtime command surface from the appropriate bundle in `specfact-cli-modules`.
- Add contract/integration tests and usage docs only after the post-split command home is approved.

### Phase B: Protocol runtime completion

- Expand protocol FSM execution and guard validation support.
- Align docs/spec examples with actual runtime constraints.

### Phase C: Change tracking normalization

- Standardize change-tracking semantics across adapters.
- Document provider-level capability matrix explicitly.

## Maintenance Rules

1. Keep `docs/architecture/implementation-status.md` as the canonical implemented-vs-planned source.
2. When a planned capability ships, update both implementation status and this report in the same PR.
3. If a new discrepancy is found, add it with `Resolved`/`Partial`/`Open` status and an owner change reference.

## Conclusion

Documentation discrepancies targeted by `arch-08` are substantially remediated.
The remaining items are primarily implementation backlog items, now clearly documented as planned or partial rather than presented as current behavior.
