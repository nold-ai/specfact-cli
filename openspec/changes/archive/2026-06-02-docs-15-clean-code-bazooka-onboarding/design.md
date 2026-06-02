## Context

The `specfact-code-review` command surface is module-owned. Core docs should not become a second command reference, but they must give users the product story and first-run path. The modules change now adds stronger cleanup evidence: forecast metrics, AI-bloat index, preserve reasons, remediation packets, preview evidence, and opt-in mutation proof.

The public positioning should shift from a broad "Swiss-knife CLI" frame to a sharper lead hook: AI-bloat defense for Python-first AI-assisted code. That hook is the entry point, not a full product rename. Below the hook, SpecFact remains the local deterministic validation/alignment CLI for contracts, specs, tests, backlog intent, and brownfield delivery.

## Decisions

- Treat this as a docs and public-metadata companion. It must not change runtime code or module behavior.
- Lead first-contact surfaces with AI-bloat defense, then explain the broader validation/alignment platform.
- Use stable wording in core docs: "cleanup forecast", "AI-bloat index", "remediation packets", and "AI IDE handoff".
- Avoid duplicating low-level JSON field contracts; link to modules docs for exact schema and flags.
- Keep the safety framing explicit: `ai_bloat` identifies bloat-shaped cleanup candidates, not AI authorship.
- Keep the handoff model vendor-neutral: Claude, Codex, Cursor, Copilot, and other assistants can consume the same JSON.
- Replace "Swiss-knife" metadata wording with AI-bloat defense / deterministic review wording in package and repo metadata.
- Record GitHub repository metadata values in this change so the out-of-tree metadata mutation is reviewable.

## Public Metadata

Target GitHub repository description:

```text
AI-bloat defense CLI for Python teams: deterministic code review, cleanup forecasts, and spec/contract evidence for AI-assisted and brownfield delivery.
```

Target GitHub topics:

```text
ai, ai-assisted-development, ai-bloat, vibe-coding, code-review, clean-code, code-quality, technical-debt, static-analysis, python, developer-tools, brownfield, legacy-modernization, code2spec, contract-testing, contract-first, spec-driven-development, spec-first, requirements-engineering, testing
```

## Docs Flow

The intended user flow in core docs:

1. Install/init SpecFact.
2. Run simplify-focused code review with JSON output.
3. Inspect cleanup forecast and AI-bloat index.
4. Hand the remediation packets to the AI IDE or LLM of choice.
5. Apply only safe or approved changes.
6. Re-run review to prove findings cleared.

## Risks

- **Core docs drift from module flags.** Mitigation: keep exact flag/schema details in modules docs and link there.
- **Users think AI-bloat means AI-authorship detection.** Mitigation: repeat that this is shape detection and cleanup guidance.
- **Docs over-narrow SpecFact to one feature.** Mitigation: make AI-bloat defense the lead hook while preserving contract/spec/brownfield validation as the underlying platform.
- **GitHub repo metadata changes are outside normal code review.** Mitigation: record exact description/topics here and verify the live state after applying them.
