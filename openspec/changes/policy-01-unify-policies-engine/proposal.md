# Change: Unified Policy Engine (DoR/DoD/Flow/PI) — Δ1

## Why

Teams love tools that enforce working agreements consistently. Today DoR/DoD are fragmented across features; Kanban/SAFe policies are not first-class. A single Policy framework with `policy.validate` (hard failures; deterministic) and `policy.suggest` (AI-assisted; confidence-scored; patch-ready) gives one mechanism for DoR, DoD, Kanban entry/exit, and SAFe PI readiness so refinement, planning, and standup share the same quality gates.

## What Changes

- **NEW**: Introduce a single "Policy" framework with:
  - `policy.validate` (hard failures; deterministic)
  - `policy.suggest` (AI-assisted; confidence-scored; patch-ready)
- **NEW**: First policies shipped: Scrum (DoR + DoD), Kanban (entry/exit policies per column), SAFe (PI readiness policy hooks, minimal baseline).
- **NEW**: Produce machine-readable output: JSON for CI gates and Markdown for humans.
- **NEW**: Config: `.specfact/policy.yaml`; `specfact policy validate` runs without network access (against snapshots when applicable).
- **EXTEND**: Policy results include: rule id, severity, evidence pointer (field/path), and recommended action.
- **EXTEND**: Documentation (agile-scrum-workflows, devops-adapter-integration) for Policy Engine.

## Capabilities

- **policy-engine**: Policy framework (validate, suggest); DoR/DoD/Flow/PI policies; JSON and Markdown output; config-driven rules; evidence and recommended action per result.

## Impact

- **Affected specs**: New `openspec/changes/policy-01-unify-policies-engine/specs/policy-engine/spec.md` (Given/When/Then for validate, suggest, policies, output formats).
- **Affected code**: New module for policy engine (e.g. `src/specfact_cli/policy/` or under commands); CLI `specfact policy validate`, `specfact policy suggest`; integration points for refinement, standup, sprint-summary (DoR coverage).
- **Affected documentation** (<https://docs.specfact.io>): docs/guides/agile-scrum-workflows.md, docs/guides/devops-adapter-integration.md.
- **Integration points**: definition-of-done-support, daily-standup-exceptions-first, sprint-planning-capacity-commitment-support (DoR coverage), patch-mode-preview-apply (suggest → patch).
- **Backward compatibility**: Additive; existing behavior unchanged until callers use Policy Engine.

## Source Tracking

- **GitHub Issue**: #176
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/176>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
