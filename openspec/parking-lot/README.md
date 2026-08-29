# Parking Lot

Change proposals here are **paused, not abandoned**. Each one was authored in good faith,
but is currently waiting on an external signal before implementation makes sense.

## Why this directory exists

The `openspec/changes/` directory grew to nearly 50 active proposals — many of them
building infrastructure for customers, publishers, or evidence corpora that do not yet
exist. Carrying them as live changes:

- Made the project look unfocused to anyone reading the repo.
- Scattered effort across speculative platforms while the core thesis
  (validation evidence and AI-bloat defense for AI-assisted delivery) was still
  incomplete.
- Inflated coordination cost (cross-change contracts, integration umbrellas) for work
  that may never ship as proposed.

Moving these into a parking lot preserves the thinking and the structure while
restoring focus to the active roadmap.

## Restoration policy

Any proposal here can be returned to `openspec/changes/` by:

1. Identifying the trigger that justifies un-parking (a paying customer asked, a
   publisher wants to onboard, the evidence corpus crossed a usable threshold, etc.).
2. Re-validating the proposal against current architecture — six months of drift may
   have invalidated assumptions.
3. Moving the directory back under `openspec/changes/`.
4. Re-running `openspec validate <change-id>`.

## Contents and un-park triggers

| Change | Un-park trigger |
|---|---|
| `enterprise-01-policy-resolution-extension` | First paying enterprise customer with central-policy requirements |
| `enterprise-02-rbac-and-audit-trail` | First paying enterprise customer with audit/RBAC requirements |
| `enterprise-03-aggregation-and-drift-analytics` | Multiple enterprise teams generating cross-team evidence |
| `enterprise-04-budget-governance-and-chargeback` | First enterprise with multi-team chargeback requirements |
| `finops-01-telemetry-and-outcomes` | Heavy LLM workloads inside SpecFact, or a customer asking for spend evidence |
| `finops-02-budget-approval-gates` | Same as finops-01 |
| `knowledge-01-distillation-engine` | ≥1000 review findings or governance evidence records to mine |
| `knowledge-02-preflight-context-assembly` | knowledge-01 produces non-trivial rules in practice |
| `marketplace-03-publisher-identity` | First external third-party publisher requesting onboarding |
| `marketplace-04-revocation` | Same as marketplace-03 |
| `marketplace-05-registry-federation` | Same as marketplace-03 |
| `security-01-unified-findings-model` | First customer asking for unified security finding output |
| `security-02-eu-gdpr-baseline` | First regulated-domain customer or partner |
| `review-resiliency-01-contracts` | Code-review module shipped and used; resiliency gap raised by a real user |
| `profile-02-central-config-sources` | profile-01 shipped, ≥5 users complain about config drift |
| `profile-03-domain-overlays` | profile-02 shipped, ≥1 enterprise asking for domain-specific overlays |
| `requirements-08-bounded-red-green-proof` | Fresh evidence that historical replay prevents materially more defects than seal-bound checkpoints at acceptable local runtime cost |
| `cli-val-01-behavior-contract-standard` | cli-val-03 + cli-val-04 shipped; gaps require a separate behavior-contract artifact |
| `cli-val-02-output-snapshot-stability` | A user reports a silent output regression that snapshots would have caught |
| `cli-val-05-ci-integration` | cli-val-03 + cli-val-04 shipped and need CI gates |
| `cli-val-06-copilot-test-generation` | Manual scenario authoring becomes the bottleneck |
| `ai-integration-04-intent-skills` | Real user pull for a tiny validation-intent helper, not upstream intent engineering |

## Not parked (active roadmap)

The following remain in `openspec/changes/` because they directly serve the core thesis:

- `requirements-01..03` as upstream context adapters for validation evidence
- `architecture-01-solution-layer` as architecture-boundary validation input
- `traceability-01-index-and-orphans`
- `validation-02-full-chain-engine`
- `governance-01-evidence-output`
- `governance-02-exception-management`
- `profile-01-config-layering`
- `ai-integration-01-agent-skill`, `ai-integration-03-instruction-files`
- `cli-val-03-misuse-safety-proof`, `cli-val-04-acceptance-test-runner`

The following remain in `openspec/changes/` but need scope trimming before
implementation (Step 2 of the triage):

- `openspec-01-intent-trace`
- `ai-integration-02-mcp-server`
- `telemetry-01-opentelemetry-default-on`
- `architecture-02-well-architected-review` (gated on architecture-01 shipping)
