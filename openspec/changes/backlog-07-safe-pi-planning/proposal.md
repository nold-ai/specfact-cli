# Change: SAFe PI Planning Essentials (WSJF + PI artifacts) — Δ5

## Why

SAFe teams operate at PI/iteration/ART level. Today #116 (E4) includes ROAM list seed and #170 mentions SAFe usage, but there is no PI-level first-class support: no `backlog pi-summary`, no WSJF workflow, no PI readiness policy. Without `.specfact/safe.yaml` and PI artifacts, SAFe is an afterthought, not a supported framework.

## What Changes

- **NEW**: Add CLI command `specfact backlog pi-summary` for PI-level summary: PI scope, team commitments, cross-team dependency contracts, ROAM items (when available from #116).
- **NEW**: Config `.specfact/safe.yaml` for PI/iteration/ART settings; integrate with Policy Engine (#176) for PI readiness policy hooks.
- **NEW**: WSJF assistance: calculation with AI-assisted missing-field proposals and confirmation; output as JSON and Markdown.
- **EXTEND**: Policy Engine (#176) supports PI readiness policy when safe config is present.
- **EXTEND**: Dependency analysis (#116) cross-team dependency contracts and ROAM seed feed PI summary.
- **EXTEND**: Documentation (agile-scrum-workflows) for SAFe PI and WSJF.

## Capabilities

- **safe-pi-planning**: `backlog pi-summary` command; `.specfact/safe.yaml` (PI/iteration/ART); WSJF assistance (calculation + AI-assisted fields + confirmation); PI readiness in Policy Engine; cross-team dependency contracts.

## Impact

- **Affected specs**: New `openspec/changes/backlog-07-safe-pi-planning/specs/safe-pi/spec.md` (Given/When/Then for pi-summary, config, WSJF, policy integration).
- **Affected code**: New command `specfact backlog pi-summary`; safe config loader; WSJF calculation and AI-assisted field proposals; Policy Engine PI readiness hook.
- **Affected documentation** (<https://docs.specfact.io>): docs/guides/agile-scrum-workflows.md.
- **Integration points**: unify-policies-engine (#176), add-backlog-dependency-analysis-and-commands (#116) for ROAM and dependency contracts.
- **Backward compatibility**: Additive; new command and config; existing Scrum/Kanban commands unchanged.

## Source Tracking

- **GitHub Issue**: #184
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/184>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
