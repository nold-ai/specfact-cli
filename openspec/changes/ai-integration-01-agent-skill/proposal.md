# Change: Shared Module-Owned Skill Discovery, Installation, and Export

## Why

SpecFact modules can own focused agent workflows, but users need one core installation and export surface that discovers those assets, verifies their identity, and materializes them in a portable canonical layout. Without a shared distributor, each module or harness would copy skill content and drift independently.

## What Changes

- **NEW**: Discover versioned skill descriptors and assets shipped by installed official or trusted SpecFact modules.
- **NEW**: Install, list, update, verify, and uninstall discovered skills at project or user scope through one core-owned interface.
- **NEW**: Support canonical `.agents/skills/<skill-name>/SKILL.md` materialization plus stable metadata needed by compatible exporters.
- **NEW**: Preserve module/version/content-digest provenance, collision policy, safe-write behavior, and an uninstall inventory.
- **CLARIFY**: Modules own skill workflow content. This change owns only discovery, verification, installation, and export.
- **CLARIFY**: The future preflight and implementation-check workflows are supplied by the signed modules #434 handoff; this change does not define or validate either workflow.

## Capabilities

### New Capabilities

- `agent-skill-spec-intelligence`: Shared discovery, integrity verification, installation, and canonical export of module-owned SpecFact skills.

### Modified Capabilities

(none)

## Impact

- This rescope is planning-only. No production code, tests, skill files, exports, module package, manifest, signature, version, plugin, adapter, hook, workflow, or dependency is changed now.
- Future core implementation may materialize canonical `.agents/skills` assets but does not author module workflow prose or run preflight validators.
- Generated AGENTS/OpenSpec/Spec Kit and harness instruction references remain in `ai-integration-03-instruction-files`.

## Dependencies

- Retains parent Feature [#372](https://github.com/nold-ai/specfact-cli/issues/372), under Epic [#257](https://github.com/nold-ai/specfact-cli/issues/257).
- Blocked by the signed modules `preflight-05-implementation-conformance` handoff so the first installed identity includes both preflight and seal-bound implementation-check workflows.
- Blocks `ai-integration-03-instruction-files` [#253](https://github.com/nold-ai/specfact-cli/issues/253).

## Explicit Non-Goals

- No preflight or implementation-check workflow content, readiness validators, approval/seal behavior, checkpoint execution, or implementation conformance.
- No generated AGENTS.md/OpenSpec/Spec Kit instructions.
- No Codex plugin, ECC companion, hatch3r pack, or other external harness adapter packaging.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #251
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/251>
- **Last Synced Status**: proposed
- **Sanitized**: false
