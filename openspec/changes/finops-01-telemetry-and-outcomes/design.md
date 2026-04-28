# Design: finops-01-telemetry-and-outcomes

## Context

Telemetry can already describe command shape and outcomes, but it does not yet capture a canonical FinOps evidence record tying token spend to concrete results. This change defines that contract in core so bundles, enterprise policy, and distillation logic can all reason about efficiency the same way.

## Goals / Non-Goals

**Goals:**

- Define a first-class FinOps evidence schema with token, cost, flow, and outcome fields.
- Establish a shared outcome enum that other evidence producers can reuse.
- Keep the schema local-first and safe to emit through the redacted telemetry path.

**Non-Goals:**

- Building provider-specific billing collectors in core.
- Implementing budget approvals or chargeback logic; that belongs to later changes.
- Creating dashboards or hosted reporting.

## Decisions

- FinOps evidence is frontmatter-structured markdown and JSON-compatible payloads, so it can live in local memory stores and be mirrored into reports without a database dependency.
- The shared outcome enum is centralized in core because review, knowledge, and enterprise features all need the same vocabulary.
- Efficiency ratio is defined as a contract, not a UI concern, so downstream tools can compare flows consistently.
- Telemetry redaction rules remain authoritative: FinOps fields carry counts and identifiers, never prompt content or free-form repository data.

## Risks / Trade-offs

- [Risk] Different providers report cost on different schedules or granularities.
  Mitigation: the schema separates raw tokens from `cost_usd` and allows late reconciliation in module collectors.
- [Risk] Outcome classification may be ambiguous at session end.
  Mitigation: allow updates or post-hoc classification while preserving the stable enum vocabulary.
- [Risk] FinOps metrics can be mistaken for budgeting policy.
  Mitigation: keep this change strictly about evidence capture and shared metrics; approval logic lands later.

## Migration Plan

1. Add the FinOps evidence spec delta and telemetry extension.
2. Implement the shared schema and outcome enum in core.
3. Update the telemetry emitter to carry safe FinOps metadata when available.
4. Land module-side collectors and outcome classification against the new schema.

## Open Questions

- Whether `score` should be a required numeric field in every FinOps session or optional when only outcome classification is available.
- Whether project identifiers should be opaque hashes by default for enterprise privacy.
