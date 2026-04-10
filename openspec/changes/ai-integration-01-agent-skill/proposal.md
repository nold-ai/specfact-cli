# Change: Agent Skill for Spec Intelligence (Skills-First Interface)

## Why

AI IDEs generate 41% of all code with zero specification validation. No spec-driven tool offers a Skills-first integration that keeps context usage near-zero until activated. Agent Skills — adopted by 26+ platforms (Claude Code, Copilot, Cursor, Windsurf, Gemini CLI, Codex) in under two months — provide the most context-efficient integration path: ~80 tokens at rest vs 13,647+ tokens for MCP servers. A SpecFact Agent Skill teaches AI agents when and how to invoke SpecFact validation, making specification intelligence available across the entire AI IDE ecosystem with a single implementation.

## What Changes

- **NEW**: Agent Skill at `skills/specfact/SKILL.md` following the open standard:
  - YAML frontmatter: name, description, allowed-tools (bash/terminal)
  - Markdown instructions: when to invoke SpecFact, what validation modes exist, how to interpret results
  - Progressive disclosure: agents see ~80 tokens of metadata at session start, load full instructions (~2,000-3,000 tokens) only when spec-related work is detected
- **NEW**: Per-workflow composable sub-skills:
  - `skills/specfact-assess-pr/SKILL.md` — validate a PR against impacted business requirements
  - `skills/specfact-check-architecture/SKILL.md` — verify code changes align with architectural decisions
  - `skills/specfact-coverage/SKILL.md` — show which requirements have full traceability
- **NEW**: Skill-triggered CLI invocation patterns:
  - On API file edit → `specfact validate --full-chain --output json`
  - On PR review → `specfact trace show REQ-{id}` for impacted requirements
  - On new endpoint → `specfact requirements list --show-coverage` to check for orphans
- **NEW**: `specfact ide skill install` — copy skill files to the appropriate location for the current project
- **NEW**: Skill bundled resources: common spec patterns, validation result interpretation guide, example workflows

## Capabilities

### New Capabilities

- `agent-skill-spec-intelligence`: Agent Skill (open standard, 26+ platform support) for specification validation, traceability queries, and requirements coverage — ~80 tokens at rest, ~2,000-3,000 tokens on activation. Includes composable sub-skills for PR assessment, architecture checking, and coverage reporting.

### Modified Capabilities

(none)

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #251
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/251>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: 2b715dada0ffb0b0 -->