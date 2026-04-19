# Change: Resiliency & Operational Scalability Review Contracts

## Why

SpecFact already reviews code quality, clean-code principles, and architecture traceability — but runtime robustness
(retries, timeouts, idempotency, backpressure, circuit-breakers, graceful degradation, load profiles, failure modes,
capacity planning) is invisible to review. Production incidents typically stem from these categories, not from naming
or DRY violations. A dedicated resiliency review pillar, symmetric to code-review, catches these patterns pre-merge and
feeds evidence into the distillation loop so the LLM learns to author resilient code by default.

## What Changes

- **NEW**: `review-resiliency-finding-model` — extends the existing `review-finding-model` with categories
  `retry-policy`, `timeout-budget`, `idempotency`, `backpressure`, `circuit-breaker`, `graceful-degradation`,
  `load-profile`, `failure-mode`, `capacity-plan`.
- **NEW**: `review-resiliency-scorer` — severity mapping (`blocker | high | medium | low | info`) with deterministic
  rule IDs prefixed `RES-*`.
- **NEW**: `review-resiliency-cli` — `specfact review resiliency [paths] [--report=json|markdown]` with exit-code
  contract aligned to `policy-02-packs-and-modes` enforcement modes.
- **EXTEND**: Evidence emission — when `specfact-knowledge` is installed, resiliency findings append to
  `.specfact/memory/evidence/` using the knowledge-01 schema. Soft dependency: free-tier users without knowledge module
  still get reports.
- **EXTEND**: `review-report-model` — ensure the shared report envelope can carry `resiliency` as a top-level key
  alongside `code_quality`.

## Capabilities

### New Capability: `review-resiliency`

Finding model, scorer contract, CLI command.

### Modified Capability: `review-report-model`

Accept `resiliency` findings under the shared envelope.

**Compatibility / migration for `review-report-model`:** Consumers of the shared `ReviewReport` JSON **MUST tolerate
unknown top-level keys** (forwards-compatible extension). The canonical `review-report-model` envelope **MUST** include
a top-level string field **`schema_version`** on every emitted document; there is **no** optional alias—emitters and
parsers agree on this single field name. **`schema_version` MUST be present** on every JSON export and **MUST bump**
on **breaking** layout changes per `review-report-model` evolution rules. **Minor** bumps cover **additive** optional
sections such as **`resiliency`** while preserving compatibility for parsers that ignore unknown keys. Providers **MUST
publish** a resiliency schema note alongside **`schema_version`** bumps and migration guidance. Rollout: **feature-flag
emitters**, **consumer opt-in** parsers where strict mode is required, and a **deprecation window** for older
`schema_version` values before hard failures. The new top-level **`resiliency`** key sits beside existing pillars such
as **`code_quality`**; tolerant readers ignore unknown sections while strict CI may pin a maximum supported
`schema_version`.

## Impact

- Runner/bundle (Semgrep patterns, linters) lives in `specfact-cli-modules` (out of scope here).
- Consumers: governance-01 evidence envelope, distillation engine.
- Additive for tolerant JSON consumers; strict schema validators must adopt the compatibility rules above before enforcing
  unknown-key failures.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #521
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/521>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open
- **Parent Feature**: #512
- **Parent Feature URL**: <https://github.com/nold-ai/specfact-cli/issues/512>
- **Sanitized**: false
