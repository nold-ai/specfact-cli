# Change: Generated AGENTS, OpenSpec, Spec Kit, and Harness Instructions

## Scope rescope — 2026-09-20

Generate lean validation references by default from the installed inventory. Emit approved-seal, preflight, checkpoint, or stop-on-stale instructions only for an explicitly selected assurance policy and installed optional capability. Do not inject those gates into every AGENTS/OpenSpec/Spec Kit workflow. Keep #251 as the prerequisite.

This owner-requested scope amendment takes precedence over conflicting default-workflow or dependency wording below. It changes planning only; runtime policy is unchanged. [Replacement policy](../requirements-09-minimal-evidence/proposal.md).

## Why

Once module-owned skills can be installed canonically, repositories still need small, deterministic instruction references that tell agents when the workflow is mandatory and how to invoke it in the active harness. Those references must preserve upstream OpenSpec/Spec Kit ownership and avoid copying the preflight loop or validator rules into every instruction file.

## What Changes

- **NEW**: Generate bounded, idempotent managed sections for root AGENTS.md and supported harness instruction files.
- **NEW**: Generate OpenSpec-aware change selection and validation references; include preflight before apply only when explicitly selected policy requires the installed optional workflow.
- **NEW**: Generate Spec Kit-aware planning/validation references, respecting opt-in agent-context ownership. Place preflight before implementation only under an explicitly selected assurance policy.
- **NEW**: Resolve the installed canonical skill and emit the harness-native invocation reference plus stop conditions.
- **CLARIFY**: Ordinary instructions select/validate the change and reference current tests. Only explicitly selected assurance policy adds preflight, approved-seal, stale/unknown stop and refinement approval requirements; missing selected capabilities produce setup diagnostics.
- **EXCLUDE**: Validation logic, canonical workflow content, skill installation, and Codex/ECC/hatch3r adapter packaging remain separately owned.

## Capabilities

### New Capabilities

- `cross-platform-instructions`: Generated AGENTS/OpenSpec/Spec Kit and command-harness references to installed module-owned workflows.

### Modified Capabilities

(none)

## Impact

- This rescope is planning-only. No production code, tests, AGENTS.md section, OpenSpec/Spec Kit file, prompt, skill, plugin, adapter, hook, workflow, manifest, signature, version, or dependency is changed now.
- Future generation consumes #251's verified installation inventory and module workflow descriptor; it never vendors skill content.
- External adapter packages remain in modules `preflight-04-harness-adapters`.

## Dependencies

- Retains parent Feature [#372](https://github.com/nold-ai/specfact-cli/issues/372), under Epic [#257](https://github.com/nold-ai/specfact-cli/issues/257).
- Blocked by `ai-integration-01-agent-skill` [#251](https://github.com/nold-ai/specfact-cli/issues/251).
- Blocks modules `preflight-04-harness-adapters`.

## Explicit Non-Goals

- No Python validator, readiness aggregation, approval/seal, or implementation-conformance logic.
- No module-owned skill/workflow prose.
- No Codex plugin, ECC companion, hatch3r pack, hook, or external repository contribution.
- No takeover of Spec Kit's opt-in `agent-context` extension or OpenSpec's generated command lifecycle.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #253
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/253>
- **Last Synced Status**: proposed
- **Sanitized**: false
