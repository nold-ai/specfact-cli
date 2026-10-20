# Change: Refresh native upstream artifact compatibility

## Why

Apply the owner-approved agentic SDLC roadmap to existing Python, OpenSpec/Spec Kit and GitHub users. Preserve the distinction between reviewed assertions, behavior evidence and authenticated authority. This is a bounded follow-up, not a replacement authoring or review engine.

## What Changes

- Pinned upstream artifact profiles: The adapter SHALL test pinned Spec Kit v1.1.0 fixtures alongside retained v0.12.18 and supported OpenSpec fixtures. Fixture metadata SHALL identify upstream tag/commit, artifact paths and content digests. Support SHALL be evaluated from the effective artifact profile, including enabled known extensions and template resolution, rather than inferred from Markdown or a claimed CLI version. The supported profile allowlist SHALL be explicit and versioned; unknown or unsupported custom profiles SHALL be rejected with an actionable diagnostic.
- Extension coexistence and atomic import: A supported SpecFact extension that only adds invocation hooks SHALL NOT by its presence invalidate a supported native artifact profile. An extension that alters artifact templates SHALL require a tested effective profile. Import and readiness validation SHALL complete before persistence; any profile, parse or readiness failure SHALL leave existing imported state unchanged. Import SHALL remain offline and SHALL NOT execute upstream scripts, fetch templates or rewrite upstream inputs.

## Capabilities

### New Capabilities

- `upstream-format-compatibility`: recognize tested effective artifact profiles and compose their results with the existing native readiness contract.

### Modified Capabilities

None. The separate `upstream-format-compatibility` capability consumes the `openspec-speckit-evidence-adapter` contract owned by `requirements-04-upstream-source-readiness` (#648). That capability retains ownership of native readiness, zero-record error results, structured diagnostics and source preservation. This change adds effective-profile recognition and caller persistence conditions without normatively modifying that base capability. Existing lean reconciliation and optional assurance retain their own ownership.

## Impact

Planning only in this PR; no runtime, registry, manifest or version changes. Core owns shared profile recognition, parsing/readiness contracts and pinned fixture metadata. Modules owns command persistence and signed runtime acceptance.

At implementation, update owning command help, adapter/reference and workflow guides on docs.specfact.io, README entry points where needed, frontmatter and navigation for added pages. Additive APIs remain optional; offline parsing/verification remains available. Rollback restores the prior compatible signed core/module pair and disables optional integration without rewriting historical reports.

## Dependencies and delivery

This follow-up depends on the [native source readiness requirement](../requirements-04-upstream-source-readiness/specs/openspec-speckit-evidence-adapter/spec.md) from `requirements-04-upstream-source-readiness` (#648). Compose effective-profile recognition with those same importers; preserve their source IDs and rejection-before-persistence behavior. Verify the released prerequisite before implementation. Archive `requirements-04-upstream-source-readiness` into the canonical `openspec-speckit-evidence-adapter` spec before archiving this separate capability. No new runtime prerequisite on #740. Modules counterpart consumes the released shared profile contract; retain legacy native import. Follow up on closed core #350/modules #168 rather than reopen them.

Implementation follows specification, derived tests, meaningful failing-before evidence, code, passing evidence and scope-appropriate gates. Use current repository reality and live issue readiness before work; do not interpret this planning approval as authority to bypass an In Progress owner or signed release gate.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: [#749](https://github.com/nold-ai/specfact-cli/issues/749)
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/749>
- **Repository**: `nold-ai/specfact-cli`
- **Parent Feature**: #371
- **Last Synced Status**: planning / Todo, 2026-10-04

## Research boundary

The roadmap and sources are in [AGENTIC_SDLC_ROADMAP.md](../../AGENTIC_SDLC_ROADMAP.md). Product priority is an owner decision. Productivity, savings, complete hidden-behavior detection and universal independent reviewer recall are not established claims.

- **Paired Modules Story**: [nold-ai/specfact-cli-modules#490](https://github.com/nold-ai/specfact-cli-modules/issues/490)

## Planning validation

See [AGENTIC_SDLC_VALIDATION.md](../../AGENTIC_SDLC_VALIDATION.md) for actual proposal checks and the explicit Python-only analyzer applicability exception. Runtime review and release tasks remain pending.
