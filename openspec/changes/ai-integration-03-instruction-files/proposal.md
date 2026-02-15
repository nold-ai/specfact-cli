# Change: Cross-Platform AI IDE Instruction Files

## Why




Each AI IDE has its own instruction file format (`.cursor/rules/*.mdc`, `.github/copilot-instructions.md`, `CLAUDE.md`, `.windsurf/rules/`). Teams using multiple IDEs need SpecFact guidance in each format. Auto-generated lightweight instruction files that point to the core Agent Skill — with glob-based auto-attachment on spec files — ensure consistent spec validation guidance across all IDEs without manual per-platform maintenance.

## What Changes




- **NEW**: `specfact ide setup --platforms cursor,copilot,claude,windsurf` — auto-generate instruction files for selected platforms:
  - `.cursor/rules/specfact.mdc` — Cursor rule with glob: `**/*.yaml, **/*.json, **/openapi*`
  - `.github/instructions/specfact.instructions.md` — Copilot instructions with `applyTo` glob
  - `CLAUDE.md` additions — Claude Code project instructions
  - `.windsurf/rules/specfact.md` — Windsurf rule file
- **NEW**: Each instruction file is a lightweight alias (~200-500 tokens) pointing to the core Agent Skill:
  - When to invoke SpecFact (on API file edits, PR reviews, new endpoints)
  - How to invoke (`specfact validate`, `specfact trace`, `specfact requirements`)
  - How to interpret results (pass/fail/advisory meanings)
- **NEW**: `specfact ide setup --update` — regenerate instruction files to match latest skill content
- **NEW**: Glob-based auto-attachment: instruction files activate automatically when developer works on spec-related files (`*.yaml`, `*.json`, `**/openapi*`, `**/asyncapi*`)
- **NEW**: Instruction file template system: instruction content is generated from a single source template, ensuring consistency across all platform formats

## Capabilities
### New Capabilities

- `cross-platform-instructions`: Auto-generated AI IDE instruction files for Cursor, Copilot, Claude Code, and Windsurf. Lightweight aliases pointing to the core Agent Skill, with glob-based auto-attachment on spec files.

### Modified Capabilities

(none)


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #253
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/253>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: 23d56625f9ca6351 -->