# Design: Intent Engineering Skills — SQUER Workflow for AI IDEs

## Context

`ai-integration-01-agent-skill` ships spec-validation skills that teach AI IDEs when to invoke SpecFact validation after code is written. This change extends SpecFact's skills surface upstream — into the intent-capture and requirements-decomposition phase that happens before a spec is written. The SQUER intent interview model (7 standard questions) provides a well-defined, machine-parseable interview protocol that maps directly to SpecFact's `BusinessOutcome` and `BusinessRule` schemas (defined by requirements-01-data-model). The open Agent Skills standard (YAML frontmatter + Markdown instructions) provides the integration surface for 26+ AI IDE platforms without platform-specific code.

## Goals / Non-Goals

**Goals:**
- Ship 6 skill files covering the full intent engineering workflow (capture → decompose → architecture → trace-validate → evidence-check)
- Extend `specfact ide skill install` with `--type intent` to install intent skills alongside or separately from spec skills
- Keep each skill file self-contained and composable (an agent can invoke one or all)
- Follow SQUER's 7-question interview exactly — this is the scholarly grounding for the intent capture pattern

**Non-Goals:**
- Building a new CLI command group for intent — the skills invoke existing `specfact requirements`, `specfact architecture`, and `specfact validate` commands
- IDE-specific integrations — the open skills standard handles 26+ platforms without per-IDE code
- Replacing `ai-integration-01` — this change extends the skills surface, not replaces it

## Decisions

### D1: Separate skill files per workflow step vs. monolithic intent skill

**Decision**: Separate skill files (`specfact-intent-capture`, `specfact-intent-decompose`, etc.)
**Rationale**: Composability. An agent doing only architecture derivation should not load the full 15,000-token intent workflow. Small skills (~2,000-3,000 tokens each) allow agents to load exactly what they need. The umbrella `specfact-intent/SKILL.md` (~80 tokens) acts as a router.
**Alternative rejected**: Single monolithic skill — exceeds context budgets for lightweight agents; forces full load for partial workflows.

### D2: Skills invoke existing CLI commands vs. new intent-specific commands

**Decision**: Skills invoke existing `specfact requirements capture/validate/trace`, `specfact architecture derive`, `specfact validate --full-chain`
**Rationale**: No new command surface means skills work immediately when requirements-01/02 and architecture-01 land. The skills are documentation and prompt patterns, not CLI extensions. The only new CLI change is the `--type intent` flag on `specfact ide skill install`.
**Alternative rejected**: New `specfact intent capture` top-level command — premature; can be added later if workflows warrant a dedicated entry point.

### D3: SQUER 7-question interview as the canonical intent capture protocol

**Decision**: Follow SQUER's 7 standard questions exactly as the structured elicitation in `specfact-intent-capture/SKILL.md`
**Rationale**: SQUER's Intent Engineer model is the scholarly foundation for this work. The 7 questions (What problem? Who has it? What happens today? What should change? How will we know? What must not break? What's the priority?) map directly to `BusinessOutcome` fields and produce YAML-serializable intent artifacts. Using a standard protocol means skills are teachable and reproducible.
**Alignment**: IntentSpec.org's 5-field schema (Objective, User Goal, Outcomes, Edge Cases, Verification) is compatible — SQUER's 7 questions produce all 5 IntentSpec fields as a superset.

### D4: Skill installation via `specfact ide skill install --type intent`

**Decision**: Extend existing install command with `--type {spec,intent,all}` (default: `spec` for backwards compatibility)
**Rationale**: The `--type` selector keeps the install surface minimal and composable. Teams that only need spec validation don't need intent skills cluttering their IDE context. `--type all` future-proofs for additional skill types (e.g., `governance`, `ceremony`).

## Risks / Trade-offs

- **[Risk] CLI dependency ordering** — Intent skills that invoke `specfact requirements capture` will silently fail if requirements-01/02 are not installed. Mitigation: each skill MUST include a prerequisite check step that runs `specfact --version` and `specfact requirements --help`; if missing, it directs the agent to install the requirements module.
- **[Risk] SQUER question fidelity** — If the 7 questions are paraphrased imprecisely, the resulting intent artifacts diverge from the schema. Mitigation: the skill file pins the exact question text; the decompose skill validates output against the `BusinessOutcome` JSON schema before writing `.req.yaml`.
- **[Trade-off] Skill file maintenance** — Each skill file is a standalone Markdown artifact. When CLI commands evolve (requirements-02, architecture-01), skill files need updating. Mitigation: skill files reference CLI commands by flag signature, not by output format; they tolerate CLI version drift as long as exit codes remain stable.

## Migration Plan

1. Land requirements-01-data-model (#238) and requirements-02-module-commands (#239) first — intent skills invoke these commands.
2. Land ai-integration-01-agent-skill (#251) first — skill install infrastructure must exist.
3. Implement `--type` flag on `specfact ide skill install` (small, backwards-compatible addition).
4. Write and test all 6 skill files against Claude Code, Cursor, and Copilot (minimum 3 agents per config.yaml Minimum Evidence Bar).
5. Run `specfact ide skill install --type intent` in SpecFact's own dev environment as dogfood proof.

## Open Questions

- None currently blocking implementation.
