# Change: Knowledge Distillation Engine

## Why

SpecFact produces substantial evidence from reviews, validations, and governance gates, but that evidence is currently write-only — no feedback loop exists to convert repeated findings into reusable rules. Without a distillation engine the LLM authors the same spec mistakes, the same code-review categories, and the same FinOps overruns indefinitely. A deterministic, human-in-the-loop distillation engine turns evidence into compact (≤500-token) rules that downstream (knowledge-02 preflight context) inject into future LLM interactions. This is the core of the flywheel tying all five governance pillars together.

## What Changes

- **NEW**: Evidence / learning / rule schema — frontmatter contracts for three artefact tiers (`evidence` → `learning` → `rule`), each with `applies-to`, `domain`, `version`, `confidence`, `evidence-count`, `source-refs`.
- **NEW**: Rule files hard-capped at 500 tokens (enforced at write-time and in validation).
- **NEW**: `specfact memory distill` CLI that reads evidence directory, calls configured LLM with a deterministic curator prompt, emits a git-diff against `rules/` for human review. No auto-merge.
- **NEW**: Promotion threshold policy — profile-level `min-evidence-count` (default 3) gating evidence → learning → rule transitions.
- **NEW**: `MemoryBackend` protocol (`add_entry`, `query`, `link`, `list_by_tag`). Markdown-graph adapter is the reference and default implementation; vector-store adapters (e.g., Chroma) are optional and explicitly not required for correctness.
- **NEW**: Append-only evidence write path with deterministic file naming (`{timestamp}_{fingerprint}.md`) under `.specfact/memory/evidence/`.

## Capabilities

### New Capability: `knowledge-distillation`

Schema, distill CLI, promotion policy, MemoryBackend protocol, markdown-graph reference implementation.

## Impact

- Unblocks knowledge-02 (preflight context assembly) and enterprise-03 (drift analytics).
- Dependents: review-resiliency-01, security-01, architecture-02, finops-01 all emit evidence through this schema.
- Zero-config local-first: works offline with markdown-only backend; LLM curator call is the only network dependency and is opt-in via `--curator` flag.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #519
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/519>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open
- **Parent Feature**: #516
- **Parent Feature URL**: <https://github.com/nold-ai/specfact-cli/issues/516>
- **Sanitized**: false
