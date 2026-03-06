# Change: Intent Engineering Skills — SQUER Workflow for AI IDEs

## Why

AI IDEs generate requirements, architecture, and code but have no structured intent-capture workflow. The result is "green specs, wrong product" — every contract passes but the shipped feature misses the business outcome because no tool validated the upstream intent. `ai-integration-01-agent-skill` ships general spec-validation skills; it does not provide the upstream intent-engineering workflow (7-question business interview, requirements decomposition, architecture derivation, trace validation). A dedicated intent skills set — following the SQUER intent interview model and the open Agent Skills standard — closes this gap by making persona-outcome capture and traceability validation available as first-class IDE slash commands across all 26+ AI IDE platforms.

## What Changes

- **NEW**: Intent-engineering Agent Skills at `skills/specfact-intent/`:
  - `skills/specfact-intent/SKILL.md` — umbrella intent skills entrypoint; ~80 tokens at rest, full instructions on activation
  - `skills/specfact-intent-capture/SKILL.md` — SQUER 7-question intent interview: What problem? Who has it? What happens today? What should change? How will we know? What must not break? What's the priority? Captures to `.specfact/requirements/{id}.req.yaml`
  - `skills/specfact-intent-decompose/SKILL.md` — Takes captured BusinessOutcome, decomposes into BusinessRules (Given/When/Then) and ArchitecturalConstraints
  - `skills/specfact-intent-architecture/SKILL.md` — Generates Architecture Decision Records from requirements context using `specfact architecture derive`
  - `skills/specfact-intent-trace-validate/SKILL.md` — Validates full traceability chain (outcome → code), reports gaps with fix prompts
  - `skills/specfact-intent-evidence-check/SKILL.md` — Checks evidence completeness for all artifacts in the chain
- **NEW**: `specfact ide skill install --type intent` — copies intent skills to the correct location for the active AI IDE
- **NEW**: Prompt-validate-feedback loop documentation: pattern for using intent skills with `specfact validate --full-chain` in a 3-phase cycle (prompt → validate → feedback)
- **EXTEND**: `specfact ide skill install` — adds `--type intent` option alongside existing `--type spec` (ai-integration-01)
- **EXTEND**: Skills discovery: intent skills listed by `specfact ide skill list`

## Capabilities

### New Capabilities

- `agent-skill-intent-workflow`: SQUER 7-question intent capture skill (~80 tokens at rest), BusinessRule G/W/T decomposition skill, architecture derivation skill, traceability validation skill, and evidence-check skill — all following the open Agent Skills standard for 26+ AI IDE platforms. Installed via `specfact ide skill install --type intent`.

### Modified Capabilities

- `agent-skill-spec-intelligence`: Extended skill discovery and install CLI to support `--type` selector (spec vs intent); `specfact ide skill list` enumerates both skill types.

## Impact

- New directory: `skills/specfact-intent*/` (6 skill files, ~2,000-3,000 tokens each)
- CLI change: `specfact ide skill install --type {spec,intent}` (new `--type` option, backwards-compatible default `spec`)
- Depends on: `ai-integration-01-agent-skill` (#251) — must land first; `requirements-01-data-model` (#238) — intent skills invoke `specfact requirements capture`; `requirements-02-module-commands` (#239) — skills call `specfact requirements validate` and `specfact requirements trace`
- Wave 8 — blocked by ai-integration-01 (#251) and requirements-02 (#239)
- Docs: new guide `docs/guides/intent-capture-workflow.md`; update `docs/guides/ai-ide-workflow.md` to include intent skills

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #349
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/349>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
