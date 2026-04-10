## Context

The repository currently relies on a large `AGENTS.md` file to carry bootstrap rules, workflow gates, and long-form operational detail. That creates two problems:

1. New sessions spend unnecessary context budget loading governance that is not always relevant.
2. Different AI models may compress or forget parts of the long document, causing inconsistent behavior around worktrees, change validation, cache refresh, TDD order, and finalization gates.

The proposed rule system keeps `AGENTS.md` as the mandatory bootstrap surface, but reduces it to a small governance contract that points to a canonical `docs/agent-rules/INDEX.md` plus a mandatory non-negotiable checklist. Detailed rules move into focused Markdown artifacts with frontmatter so rule loading can be deterministic and selective.

The deterministic bootstrap also needs to carry forward the GitHub issue-handling improvements already being introduced in repository governance: agents must not rely on stale plan text alone when linked change issues have live GitHub metadata that can invalidate readiness. Parent resolution, labels, project assignment, blockers, blocked-by links, and issue status must be handled as explicit governance checks rather than soft reminders.

## Goals / Non-Goals

**Goals:**

- Define a deterministic bootstrap path that every session follows before implementation work.
- Keep `AGENTS.md` small while preserving it as the mandatory governance layer.
- Introduce a frontmatter schema that makes rule applicability, priority, stop conditions, and user-interaction requirements machine-readable.
- Make rule loading selective so only relevant governance detail is loaded for a given task.
- Preserve existing hard gates such as worktree requirements, OpenSpec validation, cache-first GitHub lookup, TDD evidence, quality gates, and module signature enforcement.

**Non-Goals:**

- Replacing OpenSpec lifecycle rules with a new workflow engine.
- Creating a generic policy engine for arbitrary repositories.
- Automatically resolving stale, ambiguous, or concurrent work situations without user input.
- Removing platform-specific alias files such as `CLAUDE.md` or `.github/copilot-instructions.md`.

## Decisions

### Decision: Keep `AGENTS.md` as a compact bootstrap contract

`AGENTS.md` remains the first required instruction surface, but its role changes from comprehensive handbook to compact governance contract. It will:

- define the mandatory startup sequence
- point to the canonical rule index
- point to the always-load non-negotiable checklist
- define precedence for explicit user override versus repository governance

This preserves compatibility with tools and models that already look for `AGENTS.md` while preventing governance sprawl inside that file.

Alternative considered:

- Move everything to `docs/agent-rules/` and leave only a pointer in `AGENTS.md`.
- Rejected because many agents and IDE integrations are biased toward reading `AGENTS.md` first and may miss a too-thin pointer file.

### Decision: Introduce a canonical rule index with deterministic loading semantics

`docs/agent-rules/INDEX.md` becomes the dispatcher for governance rules. The index defines:

- the mandatory always-load rule set
- applicability signals for domain-specific files
- load order and precedence
- stop/continue semantics

This keeps task routing deterministic instead of relying on the model to infer which long documents to read.

Alternative considered:

- Let agents discover rule files heuristically by file names.
- Rejected because that is not deterministic across models and creates drift over time.

### Decision: Use YAML frontmatter for every rule artifact

Each `docs/agent-rules/*.md` file will include frontmatter fields such as:

- `id`
- `title`
- `always_load`
- `applies_when`
- `priority`
- `blocking`
- `user_interaction_required`
- `stop_conditions`
- `depends_on`

This makes rule selection and enforcement durable across compacted sessions and across different AI models.

Alternative considered:

- Encode the metadata inside Markdown prose only.
- Rejected because prose-only rule routing is easier to forget and harder to validate.

### Decision: Make non-negotiable gates a standalone always-load artifact

`docs/agent-rules/05-non-negotiable-checklist.md` will hold the invariant SHALL rules. It is always loaded after the index and before any domain-specific rules. This creates a small, stable enforcement nucleus that survives context compaction better than a large handbook.

### Decision: Extend cache-first governance to session bootstrap

The existing `github-hierarchy-cache` capability already requires cache-first guidance. This change extends it so the compact bootstrap path explicitly checks whether the local cache is missing or stale and refreshes it before governance work that depends on hierarchy metadata.

### Decision: Make GitHub metadata completeness and issue-state ambiguity explicit readiness gates

The compact governance system will treat GitHub issue metadata as part of deterministic implementation readiness for public work. Applicable rule files and the always-load checklist must explicitly require:

- parent resolution from cache-backed or refreshed GitHub reality
- labels and project assignment completeness
- blockers and blocked-by completeness
- a live issue-state check for `in progress` ambiguity

If an issue is already marked `in progress`, the governance system must force a clarification stop before implementation continues. This keeps concurrent work from being silently duplicated across sessions.

Alternative considered:

- Preserve these checks only as optional planning guidance in long-form prose.
- Rejected because those checks are exactly the kind of detail that gets dropped when contexts are compacted or when different models summarize instructions differently.

## Risks / Trade-offs

- [Rule sprawl moves from one file to many files] → Mitigate with a strict index, a bounded always-load subset, and mandatory frontmatter validation.
- [Agents may read `AGENTS.md` but skip the index] → Mitigate by making the bootstrap contract explicit and repetitive in the small `AGENTS.md`.
- [Applicability rules become ambiguous] → Mitigate by defining exact task signals and precedence in the index.
- [Cross-model behavior still diverges if metadata is incomplete] → Mitigate by requiring frontmatter fields and validation tests for every rule file.
- [Agents proceed from stale local change context while GitHub reality changed] → Mitigate by making cache refresh, metadata completeness, and `in progress` state checks explicit blocking gates.
- [Documentation drift between `AGENTS.md`, rule files, and alias instructions] → Mitigate by making alias surfaces reference canonical rule artifacts instead of embedding duplicated policy text.

## Migration Plan

1. Define the governance bootstrap contract and frontmatter schema in specs.
2. Replace the large `AGENTS.md` body with a compact bootstrap/governance layer.
3. Create `docs/agent-rules/INDEX.md`, `05-non-negotiable-checklist.md`, and the first domain rule files.
4. Update related alias or workflow instruction surfaces to reference the canonical rules rather than duplicating long guidance.
5. Add validation coverage for frontmatter schema, required always-load files, deterministic loading/precedence behavior, and GitHub readiness gates.
6. Verify the GitHub hierarchy cache guidance and issue-metadata readiness checks still work under the new bootstrap flow.

## Open Questions

- Whether rule-file validation should live in an existing docs/frontmatter validator or in a dedicated governance validator.
- Whether some high-frequency domain rules should also be always-load, or only index-selected.
- Whether platform-specific instruction generators should emit direct rule-file references or a stable alias that resolves through the same index.
