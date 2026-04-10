# CLAUDE.md

This file is an alias surface for Claude Code. Follow [AGENTS.md](AGENTS.md) as the primary bootstrap contract, then load the canonical governance docs in [docs/agent-rules/INDEX.md](docs/agent-rules/INDEX.md).

## Claude-specific note

Claude must treat the canonical rule docs as the source of truth for worktree policy, OpenSpec gating, GitHub completeness checks, TDD order, quality gates, versioning, and documentation rules. Do not rely on this file as a standalone governance handbook.

When a sibling internal repository with a `wiki/` tree is present (see **Strategic context** in `AGENTS.md` and [Internal wiki and strategic context](docs/agent-rules/40-openspec-and-tdd.md#internal-wiki-and-strategic-context) in the OpenSpec rule), read those wiki files by absolute path before designing a new OpenSpec change. Keep wiki content out of the public repository. When you materially change an active OpenSpec change, mirror it to `wiki/sources/<change-id>.md` in that sibling repo (then rebuild the graph per the same rule); if the sibling checkout is missing, record a follow-up instead of assuming the wiki is current.

## Clean-code alias

Claude must preserve the clean-code compliance gate and its category references. The canonical review surface enforces `naming`, `kiss`, `yagni`, `dry`, and `solid` and treats clean-code regressions as blocking until they are fixed or explicitly justified.
