# Change: FinOps Budget Approval Gates

## Why

Capturing FinOps evidence is not enough if SpecFact cannot stop or pause expensive flows before they exceed project or organizational budgets. This change adds the approval and reporting contract that turns telemetry into enforceable spending controls without breaking local-first workflows.

## What Changes

- **NEW**: `finops-budget-gates` capability defining budget policy schema, projected-overage detection, and approval states.
- **NEW**: CLI/report contract for weekly or monthly burndown summaries.
- **NEW**: Resume-token workflow so paused runs can continue after approval without losing context.
- **EXTEND**: FinOps evidence so approval events and over-budget waits are recorded consistently.
- **EXTEND**: Enterprise integration points for later org-level approval routing and chargeback.

## Capabilities

### New Capabilities

- `finops-budget-gates`: Budget policy schema, approval gate, and burndown reporting for AI-assisted flows.

### Modified Capabilities

- `finops-telemetry-outcomes`: Extend FinOps evidence so gate and approval events are auditable.

## Impact

- Depends on `finops-01-telemetry-and-outcomes` for session evidence and shared outcomes.
- Supplies the core contract reused by `enterprise-04-budget-governance-and-chargeback`.
- Affects CLI reporting, governance evidence, and docs; no existing flows are removed, but gated flows may pause before execution.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #526
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/526>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open
- **Parent Feature**: #515
- **Parent Feature URL**: <https://github.com/nold-ai/specfact-cli/issues/515>
- **Sanitized**: false
