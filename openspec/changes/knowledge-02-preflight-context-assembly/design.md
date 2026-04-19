# Design: knowledge-02-preflight-context-assembly

## Architecture

```text
author intent (free text / change name)
           │
           ▼
[Tag extractor] — regex + stopword list, emits candidate tag set
           │
           ▼
[Rule matcher] — applies-to ∩ candidate-tags; keyword match in rule title/body
           │
           ▼
[Priority sorter] — confidence desc, evidence-count desc, version desc
           │
           ▼
[Budget packer] — greedy, ≤1500 tokens, never splits a rule
           │
           ▼
{selected rule ids, snapshot sha, rendered context block}
           │
           ├─► inject before LLM authoring prompt
           └─► persist into .openspec.yaml (preflight_rules + preflight_rules_snapshot_sha)
```

## `.openspec.yaml` extension

```yaml
schema: spec-driven
created: 2026-04-19
preflight_rules:
  - rule-id: module-boundaries@1.2.0
  - rule-id: openspec-authoring@2.0.0
  - rule-id: security-pii-redaction@1.0.0
preflight_rules_snapshot_sha: sha256:abcd…
```

Snapshot sha lets audit code re-derive the exact injected set later by reading pinned rule versions from git history.

## Authoring gate integration

Hook points:

- `openspec new change <name>` — assembler runs, writes preflight block into generated `.openspec.yaml`.
- `opsx:ff` — same; injection happens before any artifact template rendering.
- AI-assisted authoring (Claude Code, Cursor, Copilot via instruction files): assembler output is prepended to the system prompt.

## Validation gate

After draft spec is written:

1. Load all rules carrying `enforcement: validation-gate` or `enforcement: blocker`.
2. Run matcher against draft spec body + frontmatter.
3. Emit finding if a `blocker` rule is violated (duplication, boundary breach, missing required section).
4. Integrate with `code-review-module` finding model so violations surface in the same review report.

## Non-goals

- Embedding similarity in core — deferred to optional modules-side vector adapter.
- Rule authoring UI — rules are authored by hand (from distilled learnings) and via `specfact memory promote`.

## Alternatives considered

1. **Inject every rule**: rejected; token budget would explode and dilute relevance.
2. **Embedding retrieval in core**: rejected; adds heavy dependency and is not required for deterministic matching at current rule counts. Available as optional module.
3. **Post-hoc checking only (no preflight)**: rejected; catches mistakes after the expensive LLM draft, not before.

## Risks

- Tag extractor misses relevant rules. Mitigated by `--include-rule <id>` override and the inspection command (`specfact memory preflight`).
- Rule snapshot drift makes audits brittle. Mitigated by pinning to version + sha in `.openspec.yaml`.
