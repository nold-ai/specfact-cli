# Change: Generated AGENTS, OpenSpec, Spec Kit, and Harness Instructions

## Why

Once module-owned skills can be installed canonically, repositories still need small, deterministic instruction references that tell agents when the workflow is mandatory and how to invoke it in the active harness. Those references must preserve upstream OpenSpec/Spec Kit ownership and avoid copying the preflight loop or validator rules into every instruction file.

## What Changes

- **NEW**: Generate bounded, idempotent managed sections for root AGENTS.md and supported harness instruction files.
- **NEW**: Generate OpenSpec-aware instructions that place preflight after proposal artifacts are ready and before any apply/implementation command.
- **NEW**: Generate Spec Kit-aware instructions that place preflight after clarification/plan/tasks/analyze quality work and before implementation, while respecting Spec Kit's opt-in agent-context ownership.
- **NEW**: Resolve the installed canonical skill and emit the harness-native invocation reference plus stop conditions.
- **CLARIFY**: Instructions state the gate only: run preflight, require a current approved seal, stop on blocked/unknown/stale results, and obtain user approval for material refinement.
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
