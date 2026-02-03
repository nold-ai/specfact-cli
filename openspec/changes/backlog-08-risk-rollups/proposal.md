# Change: Explainable Risk Rollups (single score, traceable) — Δ6

## Why

Every ceremony (standup, refinement, sprint summary, PI planning, release readiness) needs a consistent risk model with explainable inputs. Today risk is mentioned piecemeal in extensions but not modeled or wired. A single risk rollup mechanism—dependency criticality, policy failures, complexity flags, capacity overage, aging/WIP violations—makes all commands "exceptions-first" by default and gives teams one place to see "what might blow up."

## What Changes

- **NEW**: Introduce a Risk model with inputs: dependency criticality, policy failures (DoR/DoD/flow), complexity flags, capacity overage, aging/WIP violations.
- **NEW**: Produce a single rollup score (low/medium/high) with traceable contributions: JSON output with input contributions, reasons, and evidence pointers.
- **NEW**: Integrate risk rollup into standup, refinement, sprint-summary, (when available) PI summary, and (when available) `backlog verify-readiness` (release) so each command can surface risk section.
- **EXTEND**: Policy Engine (#176) and dependency analysis (#116) feed risk inputs; sprint-planning (#170) and complexity/splitting (#171) contribute capacity and complexity signals.
- **EXTEND**: Documentation (agile-scrum-workflows) for risk model and rollup usage.

## Capabilities

- **risk-rollups**: Risk model with configurable inputs; single rollup score (low/medium/high); JSON output with input contributions, reasons, evidence pointers, optional weights; integration with standup, refinement, sprint-summary, verify-readiness (when available).

## Impact

- **Affected specs**: New `openspec/changes/backlog-08-risk-rollups/specs/risk-rollups/spec.md` (Given/When/Then for risk model, rollup, JSON output, command integration).
- **Affected code**: New module for risk model (e.g. `src/specfact_cli/risk/` or under commands); rollup aggregation; CLI output for risk in backlog daily, refine, sprint-summary.
- **Affected documentation** (<https://docs.specfact.io>): docs/guides/agile-scrum-workflows.md.
- **Integration points**: add-backlog-dependency-analysis-and-commands (#116), unify-policies-engine (#176), sprint-planning-capacity-commitment-support (#170), story-complexity-splitting-hints-support (#171).
- **Backward compatibility**: Additive; existing commands unchanged until risk section is enabled or requested.

## Source Tracking

- **GitHub Issue**: #182
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/182>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
