# Change: Minimal Evidence for Reliable Delivery

## Why

Current Requirements delivery proves development chronology beyond the original current-run goal of #662. Frozen mappings, retained RED provenance, exact-head authority comments, and promotion reuse impose substantial maintenance and authoring overhead. Retain evidence that detects defects and identifies the tested revision while removing that history protocol from normal delivery.

## What Changes

- Adopt a compact, automatically generated minimum evidence bundle (MEB) from existing current-candidate tests and independent quality/security checks.
- Keep spec/test-first work and meaningful bug reproduction; replace mandatory committed transcripts and hosted RED checkpoints with short validation notes and CI artifacts.
- Consume the paired signed modules current-run contract, without approval receipts, prior RED artifacts, repeated suites, or custom release-promotion ancestry reuse.
- Coordinate the core required check and organization-required workflow cutover without unconditional-success placeholders or weakening source/module authentication.
- Rescope optional preflight/seal/checkpoint dependencies away from C14/C15, generic skills/instructions, and native execution. Preserve the optional feature's internal dependencies.
- Supersede the unimplemented R07 correction; leave shipped evidence and abandoned R08 history unchanged.

## Capabilities

### New Capabilities

- `minimum-evidence-delivery`: Lean current-run MEB, independent gates, bounded storage, coordinated enforcement, and default-policy isolation.

### Modified Capabilities

- `requirements-runtime-proof-delivery`: Restrict retained RED obligations to explicit legacy historical-proof requests, removing them from the ordinary delivery prerequisite.

## Impact

Planning only now: OpenSpec artifacts, dependency/scope tracking, and wiki mirrors. No runtime, hooks, CI, rulesets, signatures, release metadata, or canonical specs change in this planning work.

Implementation later touches core Requirements orchestration, pre-commit policy, agent/OpenSpec templates, and nold-ai/.github trusted workflow policy. Keep module-owned semantics and offline local operation. No new service, global evidence graph, telemetry product, or mandatory LLM review is introduced.

Update contributor governance and Requirements/CI reference documentation at implementation time; retain existing navigation unless new pages are necessary. Paired module command/help documentation belongs to #481.

## Dependencies and rollout

Product handoff: modules #481 signed release -> core adoption/pilot -> coordinated dev/main and organization policy cutover -> obsolete default-path removal. Governance preparation does not wait for a new runtime release: update and review
agent rules, templates and contributor guidance before behavior tests or code.
Runtime enforcement changes remain coordinated with the verified pilot. Neither new story depends on the preflight or full-chain graph roadmap.

Core #662 becomes replacement-reconciliation tracking; do not implement its old R07 tasks independently. See [dependency review](DEPENDENCY_REVIEW.md) for all open issues and change dispositions, including recovered C14/C15 proposals and the distinction between shipped modules C14 and pending core adoption.

Rollback restores the previous signed fixture, workflow, and ruleset together. Preserve explicit legacy readers and historical artifacts; never claim that old evidence validates a new revision.

## Workflow consumer alignment

The downstream `workflow-01-turn-orchestration` consumes these current claims without requiring prior local receipts, changing producer verdicts or promoting local state to protected CI authority. Its separate executor does not widen this reconciler. Modules #481 blocks workflow modules #483; the workflow is not an upstream dependency of R09.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #740
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/740>
- **Repository**: `nold-ai/specfact-cli`
- **Parent Feature**: #374 (End-to-End Integration Proof), under #258
- **Paired Modules Story**: <https://github.com/nold-ai/specfact-cli-modules/issues/481>
- **Last Synced Status**: proposed / Todo, 2026-09-20
- **Scope authority**: Owner-requested rescope before implementation; no runtime adoption claimed.
