## Context

This change implements `profile-01-config-layering` from the 2026-02-15 architecture-layer integration plan, refreshed on 2026-07-06 against the validation-evidence roadmap in `openspec/CHANGE_ORDER.md`.

The current implementation target is core `init` and config resolution. Profiles are validation rollout tiers, not broad ceremony or lifecycle enablement.

## Goals / Non-Goals

**Goals:**

- Add deterministic config layering for profile defaults, org baseline, repo overlay, and developer-local overrides.
- Keep compatibility with existing first-run workflow presets and module registry behavior.
- Preserve offline-first behavior and deterministic CLI execution.
- Make tier-derived clean-code defaults part of one shared profile resolver.

**Non-Goals:**

- No profile package under the stale `modules/profile/...` structure.
- No separate clean-code profile selector outside validation tiers.
- No schema-breaking changes outside declared capabilities.
- No dependency expansion beyond the proposal and plan.

## Decisions

- Use module-oriented integration and registry lazy-loading patterns already used in SpecFact CLI.
- Keep all public APIs contract-first with `@icontract` and `@beartype`.
- Make all behavior extensions opt-in or backward-compatible by default.
- Add/modify OpenSpec deltas first so tests can be derived before implementation.
- Store winning-source provenance in generated config as `source_annotations`.
- Preserve legacy profile names as bundle presets, while mapping them to validation tiers when config is written.

## Risks / Trade-offs

- [Dependency ordering drift] -> Mitigation: gate implementation tasks on declared prerequisites.
- [Capability overlap with adjacent changes] -> Mitigation: keep this change scoped to listed capabilities only.
- [Documentation drift] -> Mitigation: include explicit docs update tasks in apply phase.

## Migration Plan

1. Add tests from spec scenarios and capture failing-first evidence.
2. Implement minimal production changes needed for passing scenarios.
3. Update user-facing docs for validation tiers and legacy profile presets.
4. Run quality gates and then open PR to `dev`.

## Open Questions

- Dependency summary: None; this remains the first Wave 2 validation foundation change.
- No additional cross-change sequencing constraints were required during the 2026-07-06 refresh.
