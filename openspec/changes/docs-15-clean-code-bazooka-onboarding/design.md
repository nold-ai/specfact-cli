## Context

The `specfact-code-review` command surface is module-owned. Core docs should not become a second command reference, but they must give users the product story and first-run path. The planned modules change adds stronger cleanup evidence: forecast metrics, AI-bloat index, preserve reasons, remediation packets, preview evidence, and opt-in mutation proof.

## Decisions

- Treat this as a docs-only companion. It must not change runtime code or module behavior.
- Use stable wording in core docs: "cleanup forecast", "AI-bloat index", "remediation packets", and "AI IDE handoff".
- Avoid documenting low-level JSON field contracts until the modules change finalizes them; link to modules docs for exact schema and flags.
- Keep the safety framing explicit: `ai_bloat` identifies bloat-shaped cleanup candidates, not AI authorship.
- Keep the handoff model vendor-neutral: Claude, Codex, Cursor, Copilot, and other assistants can consume the same JSON.

## Docs Flow

The intended user flow in core docs:

1. Install/init SpecFact.
2. Run code review with JSON output.
3. Inspect cleanup forecast and AI-bloat index.
4. Hand the remediation packets to the AI IDE or LLM of choice.
5. Apply only safe or approved changes.
6. Re-run review to prove findings cleared.

## Risks

- **Core docs drift from module flags.** Mitigation: keep exact flag/schema details in modules docs and link there.
- **Users think AI-bloat means AI-authorship detection.** Mitigation: repeat that this is shape detection and cleanup guidance.
- **Docs promise unimplemented behavior too early.** Mitigation: phrase as "after the Code Review bundle version that includes cleanup forecast" until implementation lands.
