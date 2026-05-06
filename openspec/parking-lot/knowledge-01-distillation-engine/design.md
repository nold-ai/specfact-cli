# Design: knowledge-01-distillation-engine

## Architecture

```text
reviewers · validators · governance gates · AI PR bots
           │
           ▼ emit (frontmatter markdown)
    .specfact/memory/evidence/
           │
           ▼  specfact memory distill
   ┌──────────────────────┐
   │ Curator prompt (LLM) │   deterministic seed + rule skeleton
   └──────────────────────┘
           │
           ▼ proposes diffs
    .specfact/memory/learnings/     (staging, confidence-tracked)
           │
           ▼ promotion gate (min-evidence-count, human review)
    .specfact/memory/rules/         (versioned, ≤500 tokens, git-tracked)
           │
           ▼ consumed by knowledge-02 preflight assembler
```

## Schemas

### Evidence (append-only)

```yaml
---
type: evidence
schema_version: 1.0
source: review-code | review-resiliency | security | architecture | finops | ai-pr-bot
domain: [naming, boundaries, retry, cve, …]
applies-to: [module, language, framework, *]
fingerprint: sha256(canonical-body)
observed-at: ISO-8601
outcome: rework-required | spec-approved | code-merged-clean | test-passed-first-run | rule-updated
source-ref: path#line | issue#id | pr#id
---
<free-form body — evidence content, redacted of PII>
```

### Learning (staged)

```yaml
---
type: learning
schema_version: 1.0
applies-to: […]
domain: [...]
evidence-count: 3
evidence-refs: [fingerprint, ...]
confidence: 0.0-1.0
proposed-rule: path-to-rule-file.md
---
```

### Rule (≤500 tokens)

```yaml
---
type: rule
schema_version: 1.0
version: 1.0.0
applies-to: […]
domain: [...]
confidence: 0.0-1.0
evidence-count: N
promoted-at: ISO-8601
supersedes: previous-rule-id?
---
<compact imperative rule body, ≤500 tokens>
```

## `specfact memory distill`

Pipeline (deterministic order):

1. Discover new evidence (fingerprint not yet linked to a learning).
2. Group by `(domain, applies-to)` tuple.
3. For each group meeting `min-evidence-count`, assemble curator prompt with:
   - Canonical system prompt (versioned, stored in `prompts/curator_v1.md`).
   - Evidence bodies (redacted).
   - Existing rules in same `domain` (to avoid duplication and drive supersession).
4. LLM returns structured output: `proposed_rule_body`, `confidence`, `supersedes?`.
5. Write diff to `.specfact/memory/learnings/<id>.md` and a dry-run git diff against `rules/`.
6. Exit without mutating `rules/` — human promotes via `specfact memory promote <id>`.

## MemoryBackend protocol

```python
class MemoryBackend(Protocol):
    def add_entry(self, entry: MemoryEntry) -> EntryId: ...
    def query(self, tags: list[str], kind: EntryKind, limit: int) -> list[MemoryEntry]: ...
    def link(self, src: EntryId, dst: EntryId, relation: Relation) -> None: ...
    def list_by_tag(self, tag: str) -> list[EntryId]: ...
```

### MemoryBackend stability and extension contract

- **Stable extension point:** `MemoryBackend` is part of the public distillation contract and is **semver-major locked** with the `specfact-cli` release that first ships it.
- **Required methods (signatures stable across minor/patch):** `MemoryBackend.add_entry`, `MemoryBackend.query`, `MemoryBackend.link`, `MemoryBackend.list_by_tag` — parameter and return types MUST remain compatible for the same major version.
- **Optional provider-specific methods:** implementations MAY add methods prefixed `x_` (for example `x_vector_similarity`) without breaking the protocol for callers that ignore unknown methods.
- **Errors:** transient I/O or backend outages raise `MemoryBackendError`; invalid configuration raises `MemoryBackendConfigError` (distinct types so callers can retry vs fix config).
- **Compatibility policy:** adding a **new required** method is a **semver-major** change; minor releases MAY add optional `x_*` hooks only. Deprecation of a required method requires at least one minor release with warnings/docs before removal in the next major.

Reference implementation: markdown-graph backend stores entries as files, relations as frontmatter link lists, rebuildable index at `.specfact/memory/.index.json`.

## Non-goals

- Vector search in v1 (optional Chroma adapter lives in modules repo).
- Automatic merge of rule changes — always human-gated.
- Cross-repo rule federation (handled by enterprise-03).

## Alternatives considered

1. **Auto-promote high-confidence learnings**: rejected. Rules are load-bearing for every future LLM call; silent rule drift is worse than missed learnings.
2. **Single JSON document for all evidence**: rejected. Markdown-first lets humans read and edit in the same tools they use for specs; git diff is the audit trail.
3. **Embeddings-first storage**: rejected as default. Requires Python packaging overhead and a vector DB; markdown-graph matches the local-first posture.

## Risks

- Curator prompt drift producing inconsistent rules. Mitigated by versioned prompt files and deterministic evidence ordering.
- Evidence accumulation without distillation cycles. Mitigated by `specfact memory status` surface showing un-distilled counts.
