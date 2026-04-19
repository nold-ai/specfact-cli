# Change: Preflight Context Assembly for OpenSpec Authoring

## Why

Once the distillation engine (knowledge-01) produces rules, those rules are useless unless the LLM sees them at the moment it authors a spec or change. Today, OpenSpec authoring runs with no rule injection, so every draft is written from cold context and the distilled knowledge is effectively ignored. A preflight context assembler that picks tag-matched rules, fits them to a token budget, injects them before the authoring prompt, and records which rules were injected in the `.openspec.yaml` frontmatter — closes the flywheel and provides auditable traceability.

## What Changes

- **NEW**: Pre-flight context assembler — deterministic keyword + `applies-to` tag matcher (no embeddings in core); selects rule subset within a token budget (default 1500).
- **NEW**: OpenSpec authoring gate — before `openspec new` or AI-assisted change creation, the assembler runs and selected rule IDs are recorded in `.openspec.yaml` frontmatter under new key `preflight_rules: [...]`.
- **NEW**: Spec validation gate — after draft, runs duplication/boundary check against `rules/module-boundaries.md` and `rules/openspec-authoring.md` (or any rule carrying `enforcement: validation-gate`).
- **NEW**: `specfact memory preflight <prompt-or-intent>` — inspection command returning the rule set that would be injected for a given intent.
- **EXTEND**: `.openspec.yaml` schema adds `preflight_rules` and `preflight_rules_snapshot_sha` fields for drift audit.

## Capabilities

### New Capability: `preflight-context-assembly`

Assembler, authoring gate, validation gate, inspection command, `.openspec.yaml` extension.

## Impact

- Depends on knowledge-01 (rule schema + backend).
- Consumed by every future OpenSpec authoring workflow; establishes the rule-injection contract used by enterprise-03 drift analytics.
- Adds deterministic, reproducible injection — a change authored yesterday can be audited against the exact rule snapshot used.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #520
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/520>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open
- **Parent Feature**: #516
- **Parent Feature URL**: <https://github.com/nold-ai/specfact-cli/issues/516>
- **Sanitized**: false
