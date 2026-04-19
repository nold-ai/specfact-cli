# Change: FinOps Telemetry and Outcome Evidence

## Why

SpecFact can only optimize AI-assisted workflows if it measures spend, tokens, and outcomes with a shared contract. Today telemetry and review evidence are separate, which prevents the platform from answering whether a flow was cheap, effective, or worth repeating.

## What Changes

- **Define** `finops-telemetry-outcomes` capability defining the canonical FinOps session evidence schema.
- **Add** a shared outcome enum spanning spec, review, and implementation flows.
- **Introduce** an efficiency ratio contract combining score, tokens, and cost into a reusable metric.
- **EXTEND**: Telemetry and evidence flows so token/cost metadata can be emitted without leaking prompts or repository content.
- **EXTEND**: Knowledge/distillation inputs so FinOps evidence can participate in promotion and drift analysis.

## Capabilities

### New Capabilities

- `finops-telemetry-outcomes`: Session evidence schema, shared outcomes, and efficiency ratio for AI-assisted work.

### Modified Capabilities

- `telemetry-otel`: Extend telemetry payloads so FinOps fields can be emitted safely when available.

## Impact

- Depends on `telemetry-01-opentelemetry-default-on` for the default emitter path.
- Supplies the contract consumed by `finops-02-budget-approval-gates` and the modules-side `finops-01-module-cost-outcome`.
- Affects docs, governance evidence, and knowledge distillation; no existing user-facing API is removed.

### Telemetry and FinOps documentation alignment (core and modules)

- Align `telemetry-01-opentelemetry-default-on` and this change in **specfact-cli-modules** docs: document both the **per-project append-only audit path** `.specfact/telemetry/sent.log` and the **general event log** `~/.specfact/telemetry.log` (legacy/global) so operators know which file to tail for redacted transmit history vs general events.
- Document **default-on semantics**: community tier telemetry **enabled by default**; **enterprise deployments default off** unless a **signed org policy** re-enables it (see telemetry change and `enterprise-01-policy-resolution-extension`).
- State explicitly that the **FinOps payload extension is redacted** — counts, identifiers, enums, and bounded metadata only — **no prompt text, spec bodies, or repository content**, and link that posture to the **outcome vocabulary / evidence contract** consumed by `finops-02-budget-approval-gates` and `finops-01-module-cost-outcome`.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #525
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/525>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open
- **Parent Feature**: #515
- **Parent Feature URL**: <https://github.com/nold-ai/specfact-cli/issues/515>
- **Sanitized**: false
